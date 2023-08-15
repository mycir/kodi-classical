#!/usr/bin/env python3

import configparser
import os
import platform
import re
import sys

from pymediainfo import MediaInfo
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QSplashScreen,
)


class FolderDialog(QFileDialog):
    def __init__(self, title, rootdir=None):
        QFileDialog.__init__(self)
        self.setWindowTitle(title)
        self.setFileMode(QFileDialog.Directory)
        if rootdir:
            self.setDirectory(rootdir)


class PlaylistGenerator:
    media_types = (
        ".mp2",
        ".mp3",
        ".m4a",
        ".wma",
        ".aac",
        ".ogg",
        ".flac",
        # add as required
    )

    @staticmethod
    def _generate_playlist(playlist_dir, station, media_list):
        cp = configparser.ConfigParser(interpolation=None)
        cp.optionxform = lambda option: option
        cp.add_section("playlist")
        # kodi plays single item playlists but
        # doesn't expand them for browsing,
        # so append a dummy item
        if len(media_list) == 1:
            media_list.append(["\\", None, "", ""])
        for i, m in enumerate(media_list):
            # m = [
            #     mediafile relative path,
            #     mediafile modified time,
            #     media title,
            #     media length (duration s)
            # ]
            # Note: media_list has been sorted most recent first.
            # Hence a zero padded index will be prefixed to title
            # so that kodi_remote users can browse most
            # recent broadcasts in descending order.
            cp.set("playlist", f"File{i + 1}", m[0])
            if m[2] > "":
                t = f"{format(i + 1, '04d')}.{m[2]}"
            else:
                t = ""
            cp.set("playlist", f"Title{i + 1}", t)
            cp.set("playlist", f"Length{i + 1}", f"{m[3]}")
        cp.set("playlist", "NumberOfEntries", f"{i + 1}")
        cp.set("playlist", "Version", f"{2}")
        fn = f"{playlist_dir}/{station}.pls"
        with open(fn, mode="w", encoding="latin-1") as f:
            cp.write(f, space_around_delimiters=False)
            # https://bugs.python.org/issue32917
            # 'ConfigParser writes a superfluous final blank line'
            # ...which causes kodi to ignore the playlist, thanks!
            if platform.system() == "Windows":
                newline_len = 2
            else:
                newline_len = 1
            new_eof = f.tell() - newline_len
            f.seek(new_eof)
            f.truncate()

    @staticmethod
    def generate_playlists(playlists_dir, sources_dir, splashscreen=None):
        pd_parent = os.path.abspath(os.path.join(pf, os.pardir))
        sd_parent = os.path.abspath(os.path.join(sf, os.pardir))
        if sd_parent != pd_parent:
            return False
        if platform.system() == "Windows":
            sep = "\\"
        else:
            sep = "/"
        common_root = playlists_dir.rpartition(sep)[0]
        sd_relative = sources_dir.partition(common_root)[2][1:]
        for dir, _, files in os.walk(sources_dir):
            media_list = []
            for f in files:
                if splashscreen:
                    msg = f"Generating playlists...\n\n{dir}"
                    splashscreen.showMessage(
                        msg, Qt.AlignVCenter | Qt.AlignHCenter, Qt.white
                    )
                    QApplication.processEvents()
                if f.endswith(__class__.media_types):
                    f_fqp = f"{dir}{sep}{f}"
                    modified = os.path.getmtime(f_fqp)
                    duration = MediaInfo.parse(f_fqp, output="Audio;%Duration%")
                    if duration != "":
                        length = f"{round(float(duration) / 1000)}"
                    else:
                        length = "0"
                    f_rp = f_fqp.rpartition(f"{sources_dir}")[2]
                    if sep == "/":
                        f_rp = f_rp.replace("/", "\\")
                    f_txt = f"{dir}{sep}{f.rpartition('.')[0]}.txt"
                    if os.path.exists(f_txt):
                        with open(f_txt, encoding="latin-1") as f:
                            d = f.read()
                        details = re.sub(r"\s*[\r\n]+", " | ", d)
                    else:
                        details = f
                    media_list.append(
                        [
                            f"..\\{sd_relative}{f_rp}",
                            modified,
                            details,
                            length,
                        ]
                    )
            if media_list != []:
                # sort descending from most recent
                media_list.sort(key=lambda m: float(m[1]), reverse=True)
                dir_rp = dir.rpartition(f"{common_root}{sep}{sd_relative}")
                source = dir_rp[2].split(sep)[1]
                __class__._generate_playlist(playlists_dir, source, media_list)
        return True


if __name__ == "__main__":
    app = QApplication()
    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = os.path.expanduser("~")
    fd = FolderDialog("Choose destination folder for playlists", root)
    if fd.exec():
        pf = fd.selectedFiles()[0]
    else:
        pf = None
    fd = FolderDialog("Choose mediafile sources folder", root)
    if fd.exec():
        sf = fd.selectedFiles()[0]
    else:
        sf = None
    if pf and sf:
        pm = QPixmap(1000, 300)
        pm.fill(Qt.gray)
        ss = QSplashScreen(pm, Qt.WindowStaysOnTopHint)
        ss.setStyleSheet("font-weight: bold;")
        ss.show()
        app.processEvents()
        res = PlaylistGenerator.generate_playlists(pf, sf, ss)
        if res is True:
            sys.exit(0)
        else:
            ss.close()
            err_msg = (
                "\nCannot continue.\n\nPlaylists folder "
                "and sources folder must share the same parent.\n\n"
                "(This is because playlist media paths will be written\n"
                "relative to the playlists folder so that the parent tree\n"
                "can be easily moved or copied to one of your other devices.)"
            )
    else:
        err_msg = "\nCannot continue, no playlists or sources folder chosen.\n"
    QMessageBox(QMessageBox.Critical, "Playlist Generator", err_msg).exec()
    sys.exit(1)
