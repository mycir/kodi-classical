#!/usr/bin/env python3

import argparse
import datetime
import json
import operator
import re
import sys
import unicodedata
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from functools import reduce, wraps
from inspect import currentframe, getargvalues, getfullargspec, getsource
from subprocess import Popen
from time import sleep
from traceback import format_exc, print_exc

import websocket
from kodi_remote_ui import Ui_MainWindow
from kodijson import Kodi
from psutil import process_iter
from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QRectF,
    QRunnable,
    QSortFilterProxyModel,
    Qt,
    QThread,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFocusEvent,
    QFontMetrics,
    QGuiApplication,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QStandardItem,
    QStandardItemModel,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QAbstractSlider,
    QApplication,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QStyle,
    QTextEdit,
    QWidget,
)
from requests import post


class KodiError(Exception):
    def __init__(self, error, where, argsd, source):
        self.error = error
        self.where = where
        self.argsd = argsd
        self.source = source


class PlayerState(Enum):
    Ready = auto()
    AVStarted = auto()
    Playing = auto()
    Paused = auto()
    Seeking = auto()
    Unknown = auto()


class KodiManager(QObject, Kodi):
    seeking = Signal()
    kodi_error = Signal(KodiError)

    def __init__(self, host, port, username, password):
        QObject.__init__(self)
        Kodi.__init__(self, f"http://{host}:{port}/jsonrpc", username, password)
        self.host = host
        self.port = port
        # not in kodi properties mediatype - add as required
        self.extra_mediatypes = (
            ".aac",
            ".flac",
            ".m4a",
            ".opus",
            ".wma",
            ".mkv",
            ".mp4",
            ".webm",
        )
        self.child = None
        self.watchdog = None
        self.get_a_kodi()
        self.watchdog = KodiManager.KodiWatchdog(
            self, self.host, self.player_state
        )
        self.watchdog_thread = QThread(self)
        self.watchdog.moveToThread(self.watchdog_thread)
        self.watchdog_thread.start()
        self.watchdog.player_state_changed.connect(
            lambda ps: setattr(self, "player_state", ps)
        )
        self.watchdog.new_duration.connect(
            lambda d: setattr(self, "duration", d)
        )
        self.seeking.connect(lambda: setattr(self.watchdog, "seeking", True))
        self.watchdog.finished.connect(
            self.watchdog_thread.quit, Qt.DirectConnection
        )

    def get_a_kodi(self):
        try:
            if self.host in ("127.0.0.1", "localhost"):
                if "kodi" in (p.name() for p in process_iter()):
                    self.instance_type = KodiInstanceType.Local
                else:
                    self.child = Popen(["kodi"])
                    self.instance_type = KodiInstanceType.Child
            else:
                self.instance_type = KodiInstanceType.Remote
            if self.is_rpc_active():
                self.duration = self.get_duration()
                self.player_state = self.get_player_state()
            else:
                raise ConnectionError()
        except Exception:
            self.instance_type = None
            self.quit()
            raise

    def is_rpc_active(self):
        max_tries = 50
        while max_tries:
            try:
                # Unfortunately, kodijson does not pass kwargs
                # to its internal requests.post call, so we need
                # to test host ourselves with a brief timeout.
                # Otherwise, ping will hang on unreachable private IPs
                post(f"http://{self.host}:{self.port}", timeout=0.1)
                self.execute("Ping")
                return True
            except Exception:
                sleep(0.1)
                max_tries -= 1
        return False

    def get_player_state(self):
        if self.duration.total_seconds() == 0:
            state = PlayerState.Ready
        elif self.is_playing():
            state = PlayerState.Playing
        else:
            state = PlayerState.Paused
        return state

    def try_exec(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                names = getfullargspec(f).args
                values = getargvalues(currentframe()).locals["args"]
                argsd = {}
                for i in range(len(names)):
                    argsd[names[i]] = values[i]
                result = f(*args, **kwargs)
                if "error" in result.response:
                    raise KodiError(
                        result.response["error"],
                        f.__name__,
                        argsd,
                        getsource(f),
                    )
                elif result.key_sequence:
                    r = reduce(
                        operator.getitem, result.key_sequence, result.response
                    )
                    if result.transformer:
                        return result.transformer(r)
                    else:
                        return r
            except Exception as e:
                argsd["self"].quit()
                args[0].kodi_error.emit(e)
                raise

        return wrapper

    @try_exec
    def activate_window(self, window):
        return self.KodiTry(self.GUI.ActivateWindow({"window": window}))

    @try_exec
    def is_fullscreen(self):
        return self.KodiTry(
            self.Settings.GetSettingValue({"setting": "videoscreen.screen"}),
            ["result", "value"],
            lambda value: not value,
        )

    @try_exec
    def toggle_fullscreen(self):
        return self.KodiTry(
            self.Input.ExecuteAction({"action": "togglefullscreen"})
        )

    @try_exec
    def clear_playlist(self):
        return self.KodiTry(self.Playlist.Clear({"playlistid": 0}))

    @try_exec
    def add_to_playlist(self, path):
        return self.KodiTry(
            self.Playlist.Add({"playlistid": 0, "item": {"file": path}})
        )

    @try_exec
    def player_open(self):
        return self.KodiTry(
            self.Player.Open(
                {
                    "options": {"shuffled": False},
                    "item": {"playlistid": 0, "position": 0},
                }
            )
        )

    @try_exec
    def play_pause(self):
        return self.KodiTry(self.Player.PlayPause({"playerid": 0}))

    @try_exec
    def is_playing(self):
        def transform(speed):
            if speed > 0:
                return True
            else:
                return False

        return self.KodiTry(
            self.Player.GetProperties({"properties": ["speed"], "playerid": 0}),
            ["result", "speed"],
            transform,
        )

    @try_exec
    def player_stop(self):
        self.duration = datetime.timedelta()
        return self.KodiTry(self.Player.Stop({"playerid": 0}))

    @try_exec
    def seek(self, percentage):
        self.seeking.emit()
        return self.KodiTry(
            self.Player.Seek(
                {"value": {"percentage": percentage}, "playerid": 0}
            )
        )

    @try_exec
    def get_sources(self, type):
        if type == SourceType.Music:
            type = "music"
        elif type == SourceType.Videos:
            type = "video"
        return self.KodiTry(
            self.Files.GetSources({"media": type}), ["result", "sources"]
        )

    @try_exec
    def get_directory(self, path):
        def transform(files):
            if len(files) > 0:
                for f in files:
                    if f["filetype"] == "file":
                        if f["mimetype"].startswith(("audio", "video")):
                            f["type"] = "media_file"
                        elif f["file"].endswith(self.extra_mediatypes):
                            f["type"] = "media_file"
                        elif f["label"] == "":
                            f["type"] = "dummy"
                    elif f["filetype"] == "directory":
                        f["type"] = f["filetype"]
                return files
            else:
                return None

        response = self.Files.GetDirectory(
            {
                "media": "files",
                "directory": path,
                "properties": ["mimetype"],
                "sort": {
                    "order": "ascending",
                    "method": "label",
                    "ignorearticle": False,
                },
            }
        )

        if "error" in response:
            response = {"result": {"files": []}}

        return self.KodiTry(response, ["result", "files"], transform)

    @try_exec
    def get_player_item(self):
        def transform(item):
            al = item["artist"]
            artists = ", ".join(al)
            tags = self.TrackTags(
                item["album"], item["title"], artists, item["mediapath"]
            )
            return tags

        return self.KodiTry(
            self.Player.GetItem(
                {
                    "properties": ["album", "title", "artist", "mediapath"],
                    "playerid": 0,
                }
            ),
            ["result", "item"],
            transform,
        )

    @try_exec
    def get_duration(self):
        def transform(duration):
            if not all(v == 0 for v in duration.values()):
                self.duration = datetime.timedelta(
                    0,
                    duration["seconds"],
                    0,
                    0,
                    duration["minutes"],
                    duration["hours"],
                    0,
                )
            else:
                self.duration = datetime.timedelta()
            return self.duration

        return self.KodiTry(
            self.Player.GetProperties(
                {"properties": ["totaltime"], "playerid": 0}
            ),
            ["result", "totaltime"],
            transform,
        )

    @try_exec
    def get_percentage(self):
        return self.KodiTry(
            self.Player.GetProperties(
                {"properties": ["percentage"], "playerid": 0}
            ),
            ["result", "percentage"],
        )

    @try_exec
    def get_volume(self):
        return self.KodiTry(
            self.Application.GetProperties({"properties": ["volume"]}),
            ["result", "volume"],
        )

    @try_exec
    def set_volume(self, value):
        return self.KodiTry(self.Application.SetVolume({"volume": value}))

    @try_exec
    def toggle_mute(self):
        return self.KodiTry(self.Application.SetMute({"mute": "toggle"}))

    @try_exec
    def is_muted(self):
        return self.KodiTry(
            self.Application.GetProperties({"properties": ["muted"]}),
            ["result", "muted"],
        )

    def quit(self):
        if self.watchdog:
            self.watchdog.quit()
        if self.child:
            self.child.terminate()

    class KodiWatchdog(QObject):
        player_state_changed = Signal(PlayerState)
        new_duration = Signal(datetime.timedelta)
        new_percentage = Signal(float)
        volume_changed = Signal(int, bool)
        finished = Signal()

        class WatchdogTimer(QThread):
            timeout = Signal()

            def __init__(self):
                QThread.__init__(self)
                self.stop = False

            def run(self):
                while not self.stop:
                    self.msleep(500)
                    self.timeout.emit()

            def close(self):
                self.stop = True
                self.msleep(500)

        def __init__(self, parent, host, player_state):
            QObject.__init__(self)
            self.parent = parent
            self.host = host
            self.watchdog_timer = self.WatchdogTimer()
            self.watchdog_timer.timeout.connect(self.on_timer_timeout)
            self.watchdog_timer.start()
            if player_state is not PlayerState.Ready:
                self.playing = True
            else:
                self.playing = False
            self.percentage = 0
            self.seeking = False
            self.start_listener()

        def quit(self):
            if self.listener:
                self.listener.close()
            self.watchdog_timer.close()
            self.finished.emit()

        def start_listener(self):
            try:
                self.listener = websocket.WebSocketApp(
                    f"ws://{self.host}:9090/jsonrpc",
                    on_message=self.on_notification,
                )
                QThreadPool.globalInstance().start(self.listener.run_forever)
            except websocket.WebSocketException:
                self.quit()

        def on_timer_timeout(self):
            if self.playing and not self.seeking:
                p = self.parent.Player.GetProperties(
                    {"properties": ["percentage"], "playerid": 0}
                )["result"]["percentage"]
                if p != 0 and p != self.percentage:
                    self.percentage = float(p)
                    self.new_percentage.emit(float(p))

        def on_notification(self, wsapp, message):
            d = json.loads(message)
            msg = d["method"]
            if msg == "Player.OnAVStart":
                try:
                    d = self.parent.get_duration()
                    self.new_duration.emit(d)
                except Exception:
                    pass
                self.playing = True
                self.player_state_changed.emit(PlayerState.AVStarted)
            elif msg == "Player.OnPlay":
                self.playing = True
                self.player_state_changed.emit(PlayerState.Playing)
            elif msg == "Player.OnPause":
                self.player_state_changed.emit(PlayerState.Paused)
            elif msg == "Player.OnResume":
                self.player_state_changed.emit(PlayerState.Playing)
            elif msg == "Player.OnStop":
                self.playing = False
                self.new_duration.emit(datetime.timedelta())
                self.player_state_changed.emit(PlayerState.Ready)
            elif msg == "Player.OnSeek":
                self.seeking = False
            elif msg == "Application.OnVolumeChanged":
                v = d["params"]["data"]["volume"]
                m = d["params"]["data"]["muted"]
                self.volume_changed.emit(v, m)

    @dataclass
    class TrackTags:
        album: str
        title: str
        artist: str
        mediapath: str

    KodiTry = namedtuple(
        "KodiTry", "response, key_sequence, transformer", defaults=[None, None]
    )


class KodiRemote(QMainWindow):
    def __init__(self, host, port, user, password):
        super(KodiRemote, self).__init__()
        try:
            self.kodi = KodiManager(host, port, user, password)
        except Exception as e:
            self.on_kodi_error(e)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = KodiModel(self.ui.lineEditFilter)
        self.view = KodiRemote.View.Anything
        self.in_autorepeat = False
        self.seek_slider_in_click = False
        self.set_styles()
        self.setup_controls()
        self.installEventFilters()
        self.connect_signals()
        self.load_root()
        if self.kodi.instance_type is not KodiInstanceType.Remote:
            # When kodi starts fullscreen, it disables the compositor,
            # so make kodi windowed to re-enable the compositor.
            if self.kodi.is_fullscreen():
                self.kodi.toggle_fullscreen()
            else:
                # raise kodi
                self.kodi.toggle_fullscreen()
                self.kodi.toggle_fullscreen()
            # raise kodi-remote above kodi
            self.activator = self.ActivateWindow(self)
            self.activator.finished.connect(lambda: delattr(self, "activator"))
        self.kodi.activate_window("home")
        self.move(
            QGuiApplication.screens()[0].geometry().center()
            - self.frameGeometry().center()
        )

    def set_styles(self):
        c_app = self.ui.centralwidget.grab().toImage().pixelColor(0, 0)
        edit = QLineEdit()
        edit.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        block_chr = "\u2588"
        edit.setPlaceholderText(block_chr)
        s = edit.fontMetrics().size(0, edit.placeholderText())
        edit.setFixedSize(s.width() * 4, s.height())
        img = edit.grab().toImage()
        cx = edit.width() / 2
        cy = edit.height() / 2
        c_border = img.pixelColor(0, cy)
        c_background = img.pixelColor(cx / 2, cy)
        c_pht = img.pixelColor(cx, cy)
        edit.setText(block_chr)
        img = edit.grab().toImage()
        c_text = img.pixelColor(cx, cy)
        edit.deleteLater()
        # Pragmatic solution to Qt's incorrect rendering of Linux/KDE
        # dark themes, e.g. Breeze Dark. For the full horror story see
        # https://stackoverflow.com/questions/75457687
        # TODO investigate Windows and macOS handling of dark themes
        if c_background.blackF() > c_app.blackF():
            c_border = c_app.lighter(200)
        if c_text.blackF() > c_background.blackF():
            c_pb_background = c_pht.lighter(175)
            c_pb_chunk = c_pht.lighter(150)
        else:
            c_pht = c_text.darker(150)
            # Qt styles do not include placeholder text
            p = self.ui.lineEditFilter.palette()
            p.setColor(QPalette.PlaceholderText, c_pht)
            self.ui.lineEditFilter.setPalette(p)
            c_pb_background = c_pht.darker(150)
            c_pb_chunk = c_pht.darker(125)
        ss = (
            "QListView, QLineEdit, QTextEdit, QProgressBar,"
            f"QFrame#frameLoading{{border: 1px solid {c_border.name()};"
            f"border-radius: 2px; background: {c_background.name()}}}"
            f"QProgressBar {{background-color: {c_pb_background.name()}}}"
            f"QProgressBar::chunk {{background-color: {c_pb_chunk.name()}}}"
            f"QLabel#labelLoading{{color: {c_pht.name()};border: none}}"
            "QPushButton#pushButtonMute:focus {border-style: solid}"
        )
        self.ui.centralwidget.setStyleSheet(ss)

    def setup_controls(self):
        self.ui.listView.setModel(self.model.proxy_model)
        self.highlighter = KodiRemote.Highlighter(self.ui.textEditBrowsing)
        self.ui.lineEditFilter.hide()
        self.ui.pagePlaying = QWidget()
        self.ui.pagePlaying.setObjectName("pagePlaying")
        self.ui.gridLayoutPlaying = QGridLayout(self.ui.pagePlaying)
        self.ui.gridLayoutPlaying.setObjectName("gridLayoutPlaying")
        self.ui.gridLayoutPlaying.setContentsMargins(0, 0, 0, 0)
        self.ui.mediaDetailsPlaying = self.MediaDetails()
        self.ui.mediaDetailsPlaying.setObjectName("mediaDetailsPlaying")
        self.ui.mediaDetailsPlaying.setFocusPolicy(Qt.NoFocus)
        self.ui.mediaDetailsPlaying.setFrameShape(QFrame.NoFrame)
        self.ui.mediaDetailsPlaying.setFrameShadow(QFrame.Plain)
        self.ui.mediaDetailsPlaying.setReadOnly(True)
        self.ui.gridLayoutPlaying.addWidget(
            self.ui.mediaDetailsPlaying, 0, 0, 1, 1
        )
        self.ui.stackedWidgetDetails.addWidget(self.ui.pagePlaying)
        self.ui.pushButtonSkipForward.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSeekForward)
        )
        self.ui.pushButtonSkipBackward.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSeekBackward)
        )
        self.ui.pushButtonPlay.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay)
        )
        self.ui.pushButtonStop.setIcon(
            self.style().standardIcon(QStyle.SP_MediaStop)
        )
        self.ui.pushButtonMute.setIcon(
            self.style().standardIcon(QStyle.SP_MediaVolume)
        )
        pm = (
            self.style()
            .standardIcon(QStyle.SP_TitleBarNormalButton)
            .pixmap(32, 32)
        )
        pms = pm.scaled(
            25,
            30,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.ui.pushButtonCombine.setIcon(pms)
        self.ui.pushButtonCombine.hide()
        self.ui.horizontalSliderSeek.setTracking(False)
        self.ui.horizontalSliderVolume.setValue(self.kodi.get_volume())
        if self.kodi.player_state is PlayerState.Ready:
            self.ui.widgetPlaying.setVisible(False)
            self.enable_layout_widgets(self.ui.horizontalLayoutButtons, False)
        else:
            if self.kodi.player_state is PlayerState.Playing:
                self.ui.pushButtonPlay.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause)
                )
            self.display_tags()
            self.ui.stackedWidgetDetails.setCurrentIndex(1)
            self.update_player_widgets(self.set_seek_slider_step())

    def installEventFilters(self):
        self.ui.listView.installEventFilter(self)
        self.ui.listView.viewport().installEventFilter(self)
        self.ui.lineEditFilter.installEventFilter(self)
        self.ui.textEditBrowsing.viewport().installEventFilter(self)
        self.ui.mediaDetailsPlaying.viewport().installEventFilter(self)
        self.ui.horizontalSliderSeek.installEventFilter(self)
        self.ui.horizontalSliderVolume.installEventFilter(self)
        self.ui.pushButtonMute.installEventFilter(self)
        for i in range(self.ui.horizontalLayoutButtons.count()):
            self.ui.horizontalLayoutButtons.itemAt(
                i
            ).widget().installEventFilter(self)

    def connect_signals(self):
        self.kodi.watchdog.player_state_changed.connect(
            self.on_player_state_changed
        )
        self.kodi.watchdog.new_percentage.connect(self.on_new_percentage)
        self.kodi.watchdog.volume_changed.connect(self.on_volume_changed)
        self.kodi.kodi_error.connect(self.on_kodi_error)
        self.model.items_changed.connect(self.focus_list)
        self.ui.listView.clicked.connect(
            lambda: self.do_action(KodiRemote.Action.Get_Item)
        )
        self.ui.lineEditFilter.textEdited.connect(
            lambda: self.do_action(KodiRemote.Action.Filter_Apply)
        )
        self.ui.mediaDetailsPlaying.textChanged.connect(
            lambda: self.ui.stackedWidgetDetails.setCurrentIndex(1)
        )
        self.ui.pushButtonPlay.clicked.connect(
            lambda: self.do_action(KodiRemote.Action.Play)
        )
        self.ui.pushButtonStop.clicked.connect(
            lambda: self.do_action(KodiRemote.Action.Stop)
        )
        self.ui.pushButtonSkipForward.clicked.connect(
            lambda: self.skip(self.Seek.Forward)
        )
        self.ui.pushButtonSkipBackward.clicked.connect(
            lambda: self.skip(self.Seek.Back)
        )
        self.ui.pushButtonCombine.clicked.connect(
            lambda: self.combine_playlists()
        )
        self.ui.horizontalSliderSeek.sliderMoved.connect(
            lambda value: self.update_player_widgets(
                value / 1000, set_slider_pos=False
            )
        )
        self.ui.horizontalSliderSeek.valueChanged.connect(
            self.on_seek_slider_changed
        )
        self.ui.horizontalSliderVolume.sliderMoved.connect(
            lambda value: self.kodi.set_volume(value)
        )
        self.ui.pushButtonMute.clicked.connect(self.kodi.toggle_mute)

    def enable_layout_widgets(self, layout, enabled):
        for i in range(layout.count()):
            layout.itemAt(i).widget().setEnabled(enabled)

    def eventFilter(self, widget, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            self.in_autorepeat = event.isAutoRepeat()
            if widget is self.ui.horizontalSliderVolume:
                slider = widget
                p = slider.sliderPosition()
                p_new = None
                if key == Qt.Key_PageUp:
                    p_new = p + 10
                elif key == Qt.Key_PageDown:
                    p_new = p - 10
                elif key == Qt.Key_Left:
                    p_new = p - 1
                elif key == Qt.Key_Right:
                    p_new = p + 1
                if p_new:
                    self.kodi.set_volume(p_new)
                    return True
            elif self.ui.widgetPlaying.isVisible():
                if widget is not self.ui.lineEditFilter:
                    slider = self.ui.horizontalSliderSeek
                    p = slider.sliderPosition()
                    p_new = None
                    if key == Qt.Key_PageUp:
                        p_new = p + 10000
                    elif key == Qt.Key_PageDown:
                        p_new = p - 10000
                    if widget is not self.ui.lineEditFilter:
                        if key == Qt.Key_Left:
                            p_new = p - slider.singleStep()
                        elif key == Qt.Key_Right:
                            p_new = p + slider.singleStep()
                    if p_new:
                        slider.setValue(p_new)
                        return True
            if not self.in_autorepeat:
                if key == Qt.Key_Space:
                    if QApplication.focusWidget() not in (
                        self.ui.pushButtonSkipBackward,
                        self.ui.pushButtonPlay,
                        self.ui.pushButtonStop,
                        self.ui.pushButtonSkipForward,
                        self.ui.pushButtonMute,
                        self.ui.lineEditFilter,
                    ):
                        self.do_action(KodiRemote.Action.Play)
                        return True
                elif key == Qt.Key_Return and widget is self.ui.listView:
                    item, _ = self.current_item()
                    if item[Column.Type] in ("media_file", "song"):
                        self.play_if_playable(item)
                    else:
                        self.do_action(KodiRemote.Action.Get_Item)
                    return True
                elif key == Qt.Key_Escape and widget is self.ui.lineEditFilter:
                    self.do_action(KodiRemote.Action.Filter_Clear)
                    return True
            return self.check_if_shortcut(key, event.modifiers(), widget)
        elif event.type() == QEvent.KeyRelease:
            key = event.key()
            ar = event.isAutoRepeat()
            if widget not in (
                self.ui.lineEditFilter,
                self.ui.horizontalSliderVolume,
            ):
                if key == Qt.Key_Left:
                    self.on_key_release(ar)
                elif key == Qt.Key_Right:
                    self.on_key_release(ar)
            if widget not in (self.ui.listView, self.ui.horizontalSliderVolume):
                if key == Qt.Key_PageUp:
                    self.on_key_release(ar)
                elif key == Qt.Key_PageDown:
                    self.on_key_release(ar)
            if widget is self.ui.listView:
                ci, ci_index = self.current_item()
                if key in (
                    Qt.Key_Up,
                    Qt.Key_Down,
                    Qt.Key_Home,
                    Qt.Key_End,
                ):
                    if ci_index > 0 and ci[Column.Type] != "sources":
                        self.do_action(
                            KodiRemote.Action.Get_Item, browsing=True
                        )
                    else:
                        self.ui.textEditBrowsing.clear()
                    return True
            self.in_autorepeat = ar
        elif event.type() is QMouseEvent.MouseButtonPress:
            if widget.parent() in (
                self.ui.textEditBrowsing,
                self.ui.mediaDetailsPlaying,
            ):
                self.toggle_details()
                return True
            elif widget is self.ui.horizontalSliderSeek:
                self.seek_slider_in_click = True
        elif event.type() is QMouseEvent.MouseButtonDblClick:
            if widget is self.ui.listView.viewport():
                i = self.ui.listView.indexAt(event.position().toPoint())
                self.ui.listView.setCurrentIndex(i)
                self.play_if_playable()
                return True
        elif event.type() is QMouseEvent.MouseButtonRelease:
            if widget is self.ui.horizontalSliderSeek:
                self.ui.horizontalSliderSeek.triggerAction(
                    QAbstractSlider.SliderMove
                )
                self.seek_slider_in_click = False
        elif event.type() == QFocusEvent.FocusOut:
            if event.reason() is Qt.TabFocusReason:
                if widget is self.ui.horizontalSliderVolume:
                    self.ui.listView.setFocus()
                elif widget is self.ui.listView:
                    self.ui.listView.selectionModel().clearSelection()
                    if self.ui.lineEditFilter.isVisible():
                        self.ui.lineEditFilter.setFocus()
                    else:
                        self.ui.pushButtonSkipBackward.setFocus()
            if event.reason() is Qt.BacktabFocusReason:
                if widget is self.ui.listView:
                    self.ui.listView.selectionModel().clearSelection()
                    self.ui.horizontalSliderVolume.setFocus()
                elif widget is self.ui.pushButtonSkipBackward:
                    if self.ui.lineEditFilter.isVisible():
                        self.ui.lineEditFilter.setFocus()
                    else:
                        self.ui.listView.setFocus()
        return False

    def check_if_shortcut(self, key, modifiers, widget):
        if not self.in_autorepeat:
            if modifiers == Qt.KeyboardModifier.AltModifier:
                if key == Qt.Key_D:
                    self.toggle_details()
                    return True
                if key == Qt.Key_C:
                    if self.view is KodiRemote.View.Combineable:
                        self.combine_playlists()
                        return True
                return False
            if key == Qt.Key_F8:
                self.kodi.toggle_mute()
                return True
        if widget is not self.ui.lineEditFilter:
            if key == Qt.Key_Minus:
                self.kodi.set_volume(self.kodi.get_volume() - 1)
                return True
            if key == Qt.Key_Plus:
                self.kodi.set_volume(self.kodi.get_volume() + 1)
                return True
        return False

    def on_key_release(self, autorepeat):
        self.in_autorepeat = autorepeat
        if not autorepeat:
            self.seek(self.ui.horizontalSliderSeek.value() / 1000)

    def closeEvent(self, event):
        self.kodi.quit()

    def on_kodi_error(self, e):
        msgBox = MessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setWindowTitle("Kodi Classical - Remote - Error")
        msgBox.setText(type(e).__name__)
        it, dt = None, None
        if type(e) is ConnectionError:
            it = (
                "Unable to establish control.\n\n"
                "Possible reasons for failure:\n"
                "1. Trying to connect to a non-existent Kodi.\n"
                "2. Remote control is disabled in Kodi settings.\t\t\n"
                "4. Incorrect kodi address or port.\n"
                "5. Incorrect kodi user or password.\n"
                "6. No network connection.\n"
                "7. Blocked by firewall."
            )
            dt = format_exc()
            msgBox.set_exit_code(1)
        elif type(e) is KodiError:
            it = (
                f"Error code: {e.error['code']}\n"
                f"Message: {e.error['message']}\n\n"
                f"In function KodiManager.{e.where} with arguments:\n"
            )
            for k, v in e.argsd.items():
                it += f"{k}: {v}\n"
            dt = e.source
            msgBox.set_exit_code(2)
        else:
            dt = format_exc()
            msgBox.set_exit_code(3)
        if it:
            msgBox.setInformativeText(it)
        if dt:
            msgBox.setDetailedText(dt)
            msgBox.buttons()[0].click()
        qp = QPoint(msgBox.width / 2, msgBox.height / 2)
        msgBox.move(QGuiApplication.screens()[0].geometry().center() - qp)
        QApplication.processEvents()
        msgBox.exec()
        sys.exit(msgBox.exit_code)

    def on_player_state_changed(self, player_state):
        if player_state == PlayerState.AVStarted:
            self.set_seek_slider_step()
        if player_state == PlayerState.Playing:
            self.ui.pushButtonPlay.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
            self.ui.widgetPlaying.setVisible(True)
            self.enable_layout_widgets(self.ui.horizontalLayoutButtons, True)
            if self.model.playlist_loaded:
                text = self.ui.textEditBrowsing.toPlainText()
                if len(text):
                    self.ui.mediaDetailsPlaying.setText(text)
            else:
                self.display_tags()
        elif player_state == PlayerState.Paused:
            self.ui.pushButtonPlay.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )
        elif player_state == PlayerState.Ready:
            self.ui.pushButtonPlay.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )
            self.ui.widgetPlaying.setVisible(False)
            if not self.media_selected:
                self.ui.textEditBrowsing.clear()
                self.enable_layout_widgets(
                    self.ui.horizontalLayoutButtons, False
                )

    def do_action(self, action, browsing=False):
        if action is KodiRemote.Action.Get_Item:
            self.ui.textEditBrowsing.clear()
            self.get_item(browsing)
        elif action is KodiRemote.Action.Filter_Apply:
            QApplication.processEvents()
            self.ui.lineEditFilter.update()
            QApplication.processEvents()
            self.ui.textEditBrowsing.clear()
            AsyncRunner(
                self.model.apply_filter,
                None,
                None,
                self.ui.lineEditFilter.text(),
            )
        elif action is KodiRemote.Action.Filter_Clear:
            self.ui.textEditBrowsing.clear()
            self.model.apply_filter(None)
        elif action is KodiRemote.Action.Play:
            self.play()
        elif action is KodiRemote.Action.Stop:
            self.kodi.player_stop()
            QApplication.processEvents()
            self.ui.stackedWidgetDetails.setCurrentIndex(0)

    @Slot()
    def get_sources(self, type):
        kodi_sources = self.kodi.get_sources(type)
        sources = []
        for s in kodi_sources:
            s["type"] = "source"
            sources.append(s)
        return sources

    def convert_sources(self, sources, type):
        qsi = QStandardItem()
        qsi.setData(sources)
        d = {"label": type, "file": qsi, "type": "sources"}
        return d

    def load_root(self):
        music = self.get_sources(SourceType.Music)
        videos = self.get_sources(SourceType.Videos)
        self.kodi_sources = KodiRemote.KodiSources(music, videos)
        self.model.set_items(
            [
                self.convert_sources(music, "Music"),
                self.convert_sources(videos, "Videos"),
            ]
        )

    def get_item(self, browsing=False):
        self.media_selected = False
        item, _ = self.current_item()
        if item[Column.Type] in ("media_file", "song"):
            # just in case playlists were generated from
            # webpage text saved with unicode encoding...
            bytes = item[Column.Label].encode("latin-1", "ignore")
            label = bytes.decode("latin-1", "ignore")
            self.ui.textEditBrowsing.setText(label)
            self.ui.stackedWidgetDetails.setCurrentIndex(0)
            if self.model.filtering:
                delimiters = r"\+\|"
                pattern = "|".join(map(re.escape, delimiters))
                words = re.split(pattern, self.ui.lineEditFilter.text())
                self.highlighter.highlight(words)
            self.media_selected = True
            self.enable_layout_widgets(self.ui.horizontalLayoutButtons, True)
        elif item[Column.Type] == "sources":
            self.model.filtering = False
            self.model.set_items(
                item[Column.Path], parent_path="", parent_type="root"
            )
        elif item[Column.Label] == "..":
            if item[Column.Type] == "root":
                self.load_root()
            elif any(
                item[Column.Path] == s["file"] for s in self.kodi_sources.music
            ):
                s = self.get_sources(SourceType.Music)
                self.model.set_items(s, parent_path="", parent_type="root")
            elif any(
                item[Column.Path] == s["file"] for s in self.kodi_sources.videos
            ):
                s = self.get_sources(SourceType.Videos)
                self.model.set_items(s, parent_path="", parent_type="root")
            else:
                p = item[Column.Path].rsplit("/", 2)
                if p[2] != "":
                    item[Column.Path] = p[0] + "/" + p[1] + "/"
                else:
                    item[Column.Path] = p[0] + "/"
                self.set_view(KodiRemote.View.Loading)
                AsyncRunner(
                    self.load_items, self.set_view, None, item[Column.Path]
                )
                self.do_action(KodiRemote.Action.Filter_Clear)
        elif not browsing:
            self.set_view(KodiRemote.View.Loading)
            AsyncRunner(self.load_items, self.set_view, None, item[Column.Path])
            self.do_action(KodiRemote.Action.Filter_Clear)

    def current_item(self):
        qmi = self.ui.listView.currentIndex()
        if self.model.filtering:
            qmi = self.model.proxy_model.mapToSource(qmi)
        i = qmi.row()
        if self.model.row(i)[Column.Type] == "sources":
            return (
                [
                    self.model.row(i)[Column.Label],
                    self.model.item(i, Column.Path).data(),
                    self.model.row(i)[Column.Type],
                ],
                i,
            )
        else:
            return (self.model.row(i), i)

    def load_items(self, path):
        self.model.filtering = False
        items = self.kodi.get_directory(path)
        if items is not None:
            self.model.set_items(items, parent_path=path)
            if all(i["file"].endswith((".pls", ".m3u", "m3u8")) for i in items):
                view = KodiRemote.View.Combineable
            elif path.endswith((".pls", ".m3u", "m3u8")):
                view = KodiRemote.View.Playlist
            else:
                view = KodiRemote.View.Anything
            return view
        else:
            return KodiRemote.View.Anything

    def combine_playlists(self):
        self.set_view(KodiRemote.View.Combining)
        playlists = []
        for i in range(1, self.model.rowCount() - 1):
            playlists.append(self.model.item(i, Column.Path).text())
        combined_items = []
        v = 0
        step = self.ui.progressBar.maximum() / len(playlists)
        for p in playlists:
            playlist_items = self.kodi.get_directory(p)
            if playlist_items is not None:
                for i in playlist_items:
                    combined_items.append(i)
            v += step
            self.ui.progressBar.setValue(v)
        path = self.model.row(0)[Column.Path] + "."
        self.model.set_items(combined_items, parent_path=path)
        self.set_view(KodiRemote.View.Playlist)

    def set_view(self, view):
        if view is KodiRemote.View.Loading:
            self.ui.lineEditFilter.hide()
            self.ui.pushButtonCombine.hide()
            self.ui.progressBar.setMaximum(0)
            self.ui.progressBar.setValue(0)
            self.ui.labelLoading.setText("Loading playlists...")
            self.ui.stackedWidget.setCurrentIndex(1)
        elif view is KodiRemote.View.Combining:
            self.ui.pushButtonCombine.hide()
            self.ui.progressBar.setMaximum(100)
            self.ui.progressBar.setValue(0)
            self.ui.labelLoading.setText("Combining playlists...")
            self.ui.stackedWidget.setCurrentIndex(1)
        else:
            if view is KodiRemote.View.Anything:
                self.ui.lineEditFilter.hide()
                self.ui.pushButtonCombine.hide()
            elif view is KodiRemote.View.Playlist:
                self.ui.lineEditFilter.show()
                self.ui.pushButtonCombine.hide()
            elif view is KodiRemote.View.Combineable:
                self.ui.lineEditFilter.hide()
                self.ui.pushButtonCombine.show()
            self.ui.stackedWidget.setCurrentIndex(0)
        QApplication.processEvents()
        self.view = view

    def play_if_playable(self, item=None):
        if not item:
            item, _ = self.current_item()
        if item[Column.Type] in ("media_file", "song"):
            self.do_action(KodiRemote.Action.Stop)
            self.play(item, force=True)
        elif item[Column.Type] not in ("root", "sources"):
            self.do_action(KodiRemote.Action.Get_Item)

    def play(self, item=None, force=False):
        if self.kodi.player_state == PlayerState.Ready or force:
            if not item:
                item, _ = self.current_item()
            path = item[Column.Path]
            self.kodi.clear_playlist()
            self.kodi.add_to_playlist(path)
            self.kodi.player_open()
            self.kodi.activate_window("home")
            self.kodi.activate_window("visualisation")
        else:
            self.kodi.play_pause()

    def on_volume_changed(self, volume, muted):
        self.ui.horizontalSliderVolume.setSliderPosition(volume)
        if muted:
            self.ui.pushButtonMute.setIcon(
                self.style().standardIcon(QStyle.SP_MediaVolumeMuted)
            )
        else:
            self.ui.pushButtonMute.setIcon(
                self.style().standardIcon(QStyle.SP_MediaVolume)
            )

    def seek(self, percentage):
        AsyncRunner(self.kodi.seek, None, None, percentage)

    def on_seek_slider_changed(self, value):
        p = value / 1000
        if (
            self.kodi.player_state is not PlayerState.Ready
            and not self.in_autorepeat
            or self.seek_slider_in_click
        ):
            self.seek(p)
        else:
            self.update_player_widgets(p, set_slider_pos=False)

    def on_new_percentage(self, p):
        if (
            not self.in_autorepeat
            and not self.ui.horizontalSliderSeek.isSliderDown()
        ):
            self.update_player_widgets(p)

    def update_player_widgets(self, percentage, set_slider_pos=True):
        if percentage != 0:
            if set_slider_pos:
                self.ui.horizontalSliderSeek.setSliderPosition(
                    round(percentage * 1000)
                )
            td_current = self.kodi.duration * percentage / 100
            h = int(self.kodi.duration.seconds / 3600)
            m = int(self.kodi.duration.seconds % 3600 / 60)
            s = self.kodi.duration.seconds % 60
            self.ui.labelDuration.setText("%02d:%02d:%02d" % (h, m, s))
            hms = str(td_current).split(":")
            self.ui.labelCurrentPosition.setText(
                "%02d:%02d:%02d"
                % (int(hms[0]), int(hms[1]), int(round(float(hms[2]), 0)))
            )

    def set_seek_slider_step(self):
        ds = self.kodi.duration.total_seconds()
        ss = 100000 / (ds / 5)
        self.single_step_changed = True
        self.ui.horizontalSliderSeek.setSingleStep(ss)
        p, _ = self.get_player_stats()
        self.ui.horizontalSliderSeek.setValue(p * 1000)
        return p

    def skip(self, seek_direction):
        p = self.kodi.get_percentage()
        amount = self.ui.horizontalSliderSeek.singleStep() / 1000
        if seek_direction is self.Seek.Forward:
            self.seek(min(p + amount, 100))
        else:
            self.seek(max(p - amount, 0))

    def get_player_stats(self):
        if self.kodi.duration.total_seconds() == 0:
            p = 0
        else:
            p = self.kodi.get_percentage()
        v = self.kodi.get_volume()
        return (p, v)

    @Slot()
    def focus_list(self):
        self.ui.stackedWidget.setFocus()
        self.ui.listView.setFocus()

    def toggle_details(self):
        if self.kodi.player_state is not PlayerState.Ready:
            if (
                self.ui.stackedWidgetDetails.currentWidget()
                is self.ui.pagePlaying
                and len(self.ui.textEditBrowsing.toPlainText()) > 0
            ):
                self.ui.stackedWidgetDetails.setCurrentIndex(0)
            else:
                self.ui.stackedWidgetDetails.setCurrentIndex(1)

    def display_tags(self):
        tags = self.kodi.get_player_item()
        if self.model.rowCount() == 0:
            if self.kodi.player_state is not PlayerState.Paused:
                mds = "Playing now:\n\n"
            else:
                mds = "Playing now (paused):\n\n"
        else:
            mds = ""
        if tags.title != "":
            mds += f"Album: {tags.album}\n\n"
        if tags.album != "":
            mds += f"Title: {tags.title}\n\n"
        if tags.artist != "":
            mds += f"Artist: {tags.artist}\n\n"
        if tags.mediapath != "":
            mds += f"Media path: {tags.mediapath}"
        self.ui.mediaDetailsPlaying.setText(mds)
        self.media_selected = False

    class MediaDetails(QTextEdit):
        Ring = namedtuple("Ring", "d_fraction, w_fraction, colour")

        def __init__(self):
            super().__init__()
            self.viewport().setAutoFillBackground(True)
            self.setTextBackgroundColor(Qt.transparent)
            self.setLineWrapMode(QTextEdit.WidgetWidth)
            self.setReadOnly(True)

        def paintEvent(self, e):
            tbc = self.textBackgroundColor()
            if tbc != Qt.transparent:
                self.viewport().setStyleSheet(f"background-color:{tbc.name()};")
                self.setTextBackgroundColor(Qt.transparent)
            qp = QPainter(self.viewport())
            rings = [
                self.Ring(1.0, 0.012, "#e8e8e8"),
                self.Ring(0.98, 0.31, "#d8d8d8"),
                self.Ring(0.367, 0.1, "#d0d0d0"),
                self.Ring(0.3, 0.012, "#e8e8e8"),
                self.Ring(0.277, 0.072, "#ffffff"),
                self.Ring(0.183, 0.003, "#d8d8d8"),
                self.Ring(0.133, 0.003, "#d8d8d8"),
            ]
            d = min(self.width() * 0.8, self.height() * 0.8)
            path = QPainterPath()
            qp.setOpacity(
                1 - self.palette().color(self.backgroundRole()).blackF()
            )
            for i, r in enumerate(rings):
                d_fraction = r.d_fraction - r.w_fraction
                x = (self.width() - (d * d_fraction)) / 2
                y = (self.height() - (d * d_fraction)) / 2
                p = QPen(
                    Qt.NoBrush, d * r.w_fraction, Qt.SolidLine, Qt.RoundCap
                )
                p.setColor(r.colour)
                qp.setPen(p)
                ed = d * d_fraction
                er = QRectF(x, y, ed, ed)
                qp.drawEllipse(er)
                if i == 0 or i == len(rings) - 1:
                    path.addEllipse(er)
            qp.setClipPath(path)
            qp.setPen(Qt.NoPen)
            od = self.width() * 0.8
            xc = self.width() / 2
            yc = self.height() / 2
            qp.translate(xc, yc)
            qp.rotate(70)
            rx = -(xc * 0.8)
            ry = -(yc * 0.3)
            r = QRectF(rx, ry, od, self.width() * 0.3)
            gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
            gradient.setColorAt(0, Qt.transparent)
            gradient.setColorAt(0.5, QColor.fromString("#ECECEC"))
            gradient.setColorAt(1, Qt.transparent)
            qp.setBrush(QBrush(gradient))
            qp.drawRect(r)
            super().paintEvent(e)

    class Highlighter:
        def __init__(self, control):
            self.control = control
            self.doc = control.document()
            self.cur = QTextCursor(self.doc)
            self.palette = control.palette()
            self.text_format = QTextCharFormat()
            self.text_format.setBackground(
                self.palette.brush(QPalette.Normal, QPalette.Highlight)
            )
            self.text_format.setForeground(
                self.palette.brush(QPalette.Normal, QPalette.HighlightedText)
            )

        def highlight(self, words):
            normalized_text = "".join(
                c
                for c in unicodedata.normalize("NFD", self.doc.toPlainText())
                if unicodedata.category(c) != "Mn"
            )
            doc_dt = QTextDocument(normalized_text.lower())
            cur_dt = QTextCursor(doc_dt)
            selections = []
            positions = set()
            for w in words:
                while True:
                    cur_dt = doc_dt.find(w, cur_dt)
                    if cur_dt.isNull():
                        break
                    cur_dt.movePosition(
                        QTextCursor.MoveOperation.EndOfWord,
                        QTextCursor.MoveMode.KeepAnchor,
                    )
                    self.cur.setPosition(cur_dt.anchor())
                    self.cur.setPosition(
                        cur_dt.position(), QTextCursor.MoveMode.KeepAnchor
                    )
                    sel = QTextEdit.ExtraSelection()
                    sel.cursor = self.cur
                    sel.format = self.text_format
                    selections.append(sel)
                    positions.add(self.cur.anchor())
            self.control.setExtraSelections(selections)
            pos_lowest = min(positions)
            self.jiggle_position(pos_lowest, QTextCursor.Up)
            self.jiggle_position(pos_lowest, QTextCursor.Down)

        def jiggle_position(self, pos, direction):
            # called several times, scrolls
            # first highlight into view
            self.cur.setPosition(pos)
            self.cur.movePosition(direction, QTextCursor.MoveAnchor, 5)
            self.control.setTextCursor(self.cur)
            self.control.ensureCursorVisible()

    @dataclass
    class KodiSources:
        music: list
        videos: list

    class View(Enum):
        Anything = auto()
        Playlist = auto()
        Loading = auto()
        Combineable = auto()
        Combining = auto()

    class Action(Enum):
        Get_Item = auto()
        Filter_Apply = auto()
        Filter_Clear = auto()
        Play = auto()
        Stop = auto()
        Combine = auto()

    class Seek(Enum):
        Forward = auto()
        Back = auto()

    class ActivateWindow(QThread):
        # Qt raise, activateWindow, isActive and
        # Qt.WindowStaysOnTopHint can be fickle,
        # so use brute force
        finished = Signal()

        def __init__(self, window, tries=10):
            QThread.__init__(self)
            self.window = window
            self.tries = tries
            self.start()

        def run(self):
            while self.tries:
                self.msleep(100)
                self.window.raise_()
                self.window.activateWindow()
                self.tries -= 1
            self.finished.emit()


class KodiModel(QStandardItemModel):
    items_changed = Signal()

    def __init__(self, filter_edit):
        super().__init__()
        self.proxy_model = KodiFilter()
        self.proxy_model.setSourceModel(self)
        self.filter_edit = filter_edit
        self.filtering = False

    def set_items(self, items, parent_path=None, parent_type="unknown"):
        self.clear()
        if parent_path is not None:
            self.appendRow(
                [
                    QStandardItem(".."),
                    QStandardItem(parent_path),
                    QStandardItem(parent_type),
                ]
            )
        for i in items:
            if i["type"] in (
                "song",
                "media_file",
                "source",
                "sources",
                "directory",
            ):
                self.appendRow(
                    [
                        QStandardItem(i["label"]),
                        QStandardItem(i["file"]),
                        QStandardItem(i["type"]),
                    ]
                )
        if (
            parent_path is None
            or parent_path == ""
            or parent_path.endswith("/")
        ):
            self.playlist_loaded = False
        else:
            self.playlist_loaded = True
        self.items_changed.emit()

    def row(self, index):
        return [
            self.item(index, Column.Label).text(),
            self.item(index, Column.Path).text(),
            self.item(index, Column.Type).text(),
        ]

    def apply_filter(self, text):
        if text is not None:
            terms = text.split("+")
            expr = ""
            for term in terms:
                if term != "":
                    expr += f"(?=.*\\b({term}))"
            pattern = re.compile(expr, re.IGNORECASE)
            self.filtering = True
            self.proxy_model.setFilterPattern(pattern)
        else:
            self.filtering = False
            self.filter_edit.clear()
            self.proxy_model.setFilterPattern(None)


class KodiFilter(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.filterPattern = None

    def setFilterPattern(self, pattern):
        self.beginResetModel()
        self.filterPattern = pattern
        self.endResetModel()

    def filterAcceptsRow(self, row_num, parent):
        if self.filterPattern is not None:
            label = self.sourceModel().row(row_num)[Column.Label]
            # match parent directory alias
            if label == "..":
                return True
            # ignore diacritics
            normalized_label = "".join(
                c
                for c in unicodedata.normalize("NFD", label)
                if unicodedata.category(c) != "Mn"
            )
            return self.filterPattern.match(normalized_label) is not None
        else:
            return True


class MessageBox(QMessageBox):
    def __init__(self):
        super().__init__()
        self.width = 640
        self.height = 480
        self.default_height = self.height
        self.details_hidden = True

    def setWidth(self, width):
        self.width = width

    def setHeight(self, height):
        self.height = height

    def get_required_height(self, widget):
        font = widget.font()
        metrics = QFontMetrics(font)
        rh = metrics.size(0, widget.text(), 0).height()
        rh += widget.contentsMargins().top() + widget.contentsMargins().bottom()
        return rh

    def resizeEvent(self, event):
        result = super().resizeEvent(event)
        t_label = self.findChild(QLabel, name="qt_msgbox_label")
        it_label = self.findChild(QLabel, name="qt_msgbox_informativelabel")
        # NB labels may not be instantiated if text
        # or informativeText are empty strings
        if t_label:
            t_label_height = self.get_required_height(t_label)
        else:
            t_label_height = 0
        if it_label:
            it_label_height = self.get_required_height(it_label)
        else:
            it_label_height = 0
        button_box = self.findChild(QDialogButtonBox)
        divider = self.findChild(QFrame, name="")
        if divider:
            self.divider_vspace = (
                divider.height() + divider.contentsMargins().bottom()
            )
        self.layout_spacing = self.findChild(QGridLayout).spacing()
        empty_space = t_label.y() + (self.layout_spacing * 4)
        self.min_height = (
            t_label_height + it_label_height + button_box.height() + empty_space
        )
        if not self.details_hidden:
            h = self.default_height
        else:
            h = self.min_height
        self.setFixedSize(self.width, h)
        self.details = self.findChild(QTextEdit)
        if self.details is not None:
            self.details_parent = self.details.parent()
            self.details.installEventFilter(self)
            self.details_parent.setFixedHeight(
                self.default_height - self.min_height - self.layout_spacing
            )
            self.details.setFixedHeight(
                self.details_parent.height() - self.layout_spacing
            )
        return result

    def eventFilter(self, widget, event):
        if event.type() == QEvent.Hide:
            self.details_hidden = True
            self.height = self.details_parent.y() + self.divider_vspace
            self.resize(self.width, self.min_height)
        elif event.type() == QEvent.Show:
            self.details_hidden = False
            self.height = self.default_height
            self.resize(self.width, self.height)
        return QWidget.eventFilter(self, widget, event)

    def set_exit_code(self, exit_code):
        self.exit_code = exit_code

    def closeEvent(self, event):
        sys.exit(self.exit_code)


class AsyncRunner:
    class Runner(QRunnable, QObject):
        finished = Signal()
        error = Signal(tuple)
        result = Signal(object)
        progress = Signal(int)

        def __init__(
            self,
            func,
            result_slot,
            finished_slot,
            *args,
            **kwargs,
        ):
            QRunnable.__init__(self)
            QObject.__init__(self)
            self.func = func
            self.args = args
            self.kwargs = kwargs
            if result_slot:
                self.result.connect(result_slot)
            if finished_slot:
                self.finished.connect(finished_slot)
            if kwargs:
                self.kwargs["progress_signal"] = self.progress

        @Slot()
        def run(self):
            try:
                result = self.func(*self.args, **self.kwargs)
            except BaseException:
                print_exc()
                type, value = sys.exc_info()[:2]
                self.error.emit((type, value, format_exc()))
            else:
                self.result.emit(result)
            finally:
                self.finished.emit()

    def __init__(self, func, result_slot, finished_slot, *args, **kwargs):
        w = self.Runner(func, result_slot, finished_slot, *args, **kwargs)
        QThreadPool.globalInstance().start(w)


class KodiInstanceType(Enum):
    Local = auto()
    Child = auto()
    Remote = auto()


class SourceType(IntEnum):
    Music = 0
    Videos = 1


class Column(IntEnum):
    Label = 0
    Path = 1
    Type = 2


if __name__ == "__main__":
    app = QApplication(sys.argv)
    parser = argparse.ArgumentParser(
        "kodi-remote",
        usage="%(prog)s -a [address] -p [port] -u [username] -P [password]",
    )
    required_args = parser.add_argument_group("required parameters")
    required_args.add_argument(
        "-a", help="Kodi address", metavar="", required=True
    )
    parser.add_argument(
        "-p",
        help="Kodi port (default: 8080)",
        metavar="",
        required=False,
        default="8080",
    )
    required_args.add_argument(
        "-u", help="Kodi username", metavar="", required=True
    )
    required_args.add_argument(
        "-P", help="Kodi password", metavar="", required=True
    )
    try:
        known_args, _ = parser.parse_known_args()
    except SystemExit as err:
        parser.usage = argparse.SUPPRESS
        if err.args[0]:
            parser.print_help()
        raise
    args = {k: v.lstrip() for k, v in vars(known_args).items()}
    kodi_remote = KodiRemote(args["a"], args["p"], args["u"], args["P"])
    kodi_remote.show()
    app.exec()
