#!/usr/bin/env python3

import configparser
import glob
import os
import platform
import re
import sys
from enum import Enum, IntEnum

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QLabel,
    QListView,
    QMessageBox,
    QSplashScreen,
    QSplitter,
    QSplitterHandle,
    QVBoxLayout,
)


class PlaylistRecomposer:

    KODI_MAX_FILE_LENGTH = 1048576

    playlists = None
    pattern = None

    def __init__(self, root, key=None):
        super(PlaylistRecomposer, self).__init__()
        if key:
            self.key = key
            self.select_regex(key)
            self.search_playlists()
        else:
            self.catalogue_chooser = self.FolderDialog(
                "Choose catalogues and playlists folder to search",
                root,
                catalogue_chooser=True,
            )
            self.catalogue_chooser.finished.connect(
                self.on_chooser_finished
            )
            if self.catalogue_chooser.exec():
                if len(self.catalogues) > 0:
                    playlists_folder = self.catalogue_chooser.selectedFiles()[0]
                    self.destination_chooser = self.FolderDialog(
                        "Choose destination folder for catalogue playlists",
                        root
                    )
                    if self.destination_chooser.exec():
                        self.destination_folder = (
                            self.destination_chooser.selectedFiles()[0]
                        )
                        if self.destination_folder != playlists_folder:
                            pf_parent = os.path.abspath(
                                os.path.join(playlists_folder, os.pardir)
                            )
                            df_parent = os.path.abspath(
                                os.path.join(self.destination_folder, os.pardir)
                            )
                            if df_parent == pf_parent:
                                self.playlists = glob.glob(
                                    playlists_folder + "/*.pls"
                                )
                                if self.playlists:
                                    pm = QPixmap(1000, 300)
                                    pm.fill(Qt.gray)
                                    self.splashscreen = QSplashScreen(
                                        pm, Qt.WindowStaysOnTopHint
                                    )
                                    self.splashscreen.setStyleSheet(
                                        "font-weight: bold;"
                                    )
                                    self.splashscreen.show()
                                    QApplication.processEvents()
                                    self.catalogue_search()
                                    self.return_code = 0
                                else:
                                    self.return_code = 6
                            else:
                                self.return_code = 5
                        else:
                            self.return_code = 4
                    else:
                        self.return_code = 3
                else:
                    self.return_code = 2
            else:
                self.return_code = 1

    def on_chooser_finished(self):
        self.catalogues = (
            self.catalogue_chooser.catalogue_chooser.get_selections()
        )

    def catalogue_search(self):
        for catalogue in self.catalogues:
            self.key = catalogue
            self.select_regex(catalogue)
            self.search_playlists()

    def select_regex(self, key):
        # TODO weed out matches that exceed the last work
        # in catalogue, e.g. opus posthumous (1830)
        if key == self.Catalogue.OPUS:
            self.pattern = re.compile(
                r"\b(?:op|opus)+(?:\s|\.)*(?:posth.*?)*(?:[\s\.,])*(\d+)"
                r"([a-z]?)(?:[\s\/.,-]*)(?:No|Nr|N\xB0)*(?:\s|\.)*(\d*)",
                flags=re.IGNORECASE,
            )
        elif key == self.Catalogue.BWV:
            self.pattern = re.compile(
                r"\b(?:bwv)+(?:\s|\.)*(\d+)([a-z]?)(?:[\s/.,-]*)*(\d*)",
                flags=re.IGNORECASE,
            )
        elif key == self.Catalogue.KOECHEL:
            # TODO weed out Scarlatti Kirkpatrick No's
            self.pattern = re.compile(
                r"\b(?:k|kv)+(?:\s|\.)*(\d+)([a-z]?)(?:[\s/.,-]*)"
                r"(?:No|Nr|N\xB0)*(?:\s|\.)*(\d*)",
                flags=re.IGNORECASE,
            )
        elif key == self.Catalogue.DEUTSCH:
            self.pattern = re.compile(
                r"\b(?:d)+(?:\s|\.)*(\d+)([a-z]?)(?:[\s/.,-]*)"
                r"(?:No|Nr|N\xB0)*(?:\s|\.)*(\d*)",
                flags=re.IGNORECASE,
            )
        elif key == self.Catalogue.HOBOKEN:
            # TODO weed out other 'H.' catalogues
            # e.g. CPE Bach, Honegger, Martinu, Berlioz etc.
            self.pattern = re.compile(
                r"\b(?:h(?:ob)?[\s.]+)([XVI]+|\d+)([abc]?)"
                r"(?:[\s/:.,]*)(?:n[or°]\.)*(?:\s|\.)*(\d*)",
                flags=re.IGNORECASE,
            )

    def search_playlists(self):
        works = self.PlaylistWorks(self.key)
        for playlist in self.playlists:
            catalogue_name = self.key.name
            if catalogue_name != "BWV":
                catalogue_name = catalogue_name.capitalize()
            msg = (
                f"Searching playlists for {catalogue_name} "
                f"catalogue numbers...\n\n{playlist}"
            )
            self.splashscreen.showMessage(
                msg, Qt.AlignVCenter | Qt.AlignHCenter, Qt.white
            )
            QApplication.processEvents()
            pl = configparser.ConfigParser(interpolation=None)
            pl.read_file(open(playlist, encoding="latin-1"))
            n = pl["playlist"]["NumberOfEntries"]
            for i in range(1, int(n)):
                title = pl["playlist"][f"title{i}"]
                matches = (self.pattern).finditer(title)
                works.append_regex_matches(
                    matches,
                    self.key,
                    pl["playlist"][f"file{i}"],
                    title[5:],
                    pl["playlist"][f"length{i}"],
                )
        works.sort()
        works.remove_duplicates()
        self.write_playlists(catalogue_name, works)

    def write_playlists(self, catalogue_name, works):
        # split list into Kodi size chunks
        # KODI_MAX_FILE_LENGTH: 1048576
        chunk_start = 0
        # TODO size of [playlist], NumberOfEntries, Version,
        size = 0
        cn_boundary = (0, works[0][self.Columns.CATALOGUE_NUM])
        for i in range(0, len(works)):
            cn_new = works[i][self.Columns.CATALOGUE_NUM]
            if cn_new > cn_boundary[1]:
                cn_boundary = (i, cn_new)
            s = 0
            # TODO size of playlist relevant cols only
            for w in works[i]:
                s += sys.getsizeof(w)
            if size + s <= self.KODI_MAX_FILE_LENGTH:
                size += s
            else:
                start_label = works.create_work_label(chunk_start, prefix=True)
                end_label = works.create_work_label(cn_boundary[0] - 1)
                self.write_playlist(
                    catalogue_name,
                    works[chunk_start : cn_boundary[0]],  # noqa: E203
                    f"{start_label} - {end_label}.pls",
                )
                i = cn_boundary[0]
                chunk_start = i
                size = 0
        start_label = works.create_work_label(chunk_start, prefix=True)
        end_label = works.create_work_label(i)
        self.write_playlist(
            catalogue_name,
            works[chunk_start : len(works)],  # noqa: E203
            f"{start_label} - {end_label}.pls",
        )

    def write_playlist(self, catalogue_name, works, fname):
        cp = configparser.ConfigParser(interpolation=None)
        cp.optionxform = lambda option: option
        cp.add_section("playlist")
        i = 1
        for w in works:
            cp.set("playlist", f"File{i}", w[self.Columns.FILE])
            cp.set("playlist", f"Title{i}", w[self.Columns.TITLE])
            cp.set("playlist", f"Length{i}", w[self.Columns.LENGTH])
            i += 1
        cp.set("playlist", "NumberOfEntries", f"{i - 1}")
        cp.set("playlist", "Version", f"{2}")
        fn = f"{self.destination_folder}/{fname}"
        msg = f"Writing {catalogue_name} catalogue playlist...\n\n{fn}"
        self.splashscreen.showMessage(
            msg, Qt.AlignVCenter | Qt.AlignHCenter, Qt.white
        )
        QApplication.processEvents()
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

    class PlaylistWorks(list):
        abbreviations = ["Op.", "BWV.", "K.", "D.", "Hob."]

        def __init__(self, key=None):
            super().__init__()
            if key is None:
                key = self.Catalogue.OPUS
            self.key = key

        def append_regex_matches(self, matches, catalogue, file, title, length):
            for m in matches:
                value = m.groups()[PlaylistRecomposer.Columns.CATALOGUE_NUM]
                if catalogue == PlaylistRecomposer.Catalogue.HOBOKEN:
                    if PlaylistRecomposer.Roman.is_roman(value):
                        value = PlaylistRecomposer.Roman.to_decimal(value)
                entry = (
                    f"{self.abbreviations[catalogue.value]} "
                    f"{value}"
                    f"{m.groups()[PlaylistRecomposer.Columns.SUFFIX]}"
                )
                piece = m.groups()[PlaylistRecomposer.Columns.PIECE]
                if piece == "":
                    piece = "0"
                else:
                    entry = f"{entry} No. {piece}"
                super().append(
                    [
                        int(value),
                        m.groups()[PlaylistRecomposer.Columns.SUFFIX],
                        int(piece),
                        file,
                        f"{entry} - {title}",
                        length,
                    ]
                )

        def sort(self):
            super().sort(
                key=lambda row: (
                    row[PlaylistRecomposer.Columns.CATALOGUE_NUM],
                    row[PlaylistRecomposer.Columns.SUFFIX],
                    row[PlaylistRecomposer.Columns.PIECE],
                )
            )

        def remove_duplicates(self):
            uniques = list()
            [uniques.append(item) for item in self if item not in uniques]
            self[:] = uniques

        def create_work_label(self, index, prefix=False):
            if prefix:
                label = f"{self.abbreviations[self.key.value]} "
            else:
                label = ""
            label += (
                f"{self[index][PlaylistRecomposer.Columns.CATALOGUE_NUM]}"
                f"{self[index][PlaylistRecomposer.Columns.SUFFIX]}"
            )
            piece = self[index][PlaylistRecomposer.Columns.PIECE]
            if piece == 0:
                return label
            else:
                return f"{label} No. {piece}"

    class FolderDialog(QFileDialog):
        def __init__(self, title, rootdir=None, catalogue_chooser=None):
            QFileDialog.__init__(self)
            self.setWindowTitle(title)
            self.setFileMode(QFileDialog.Directory)
            if rootdir:
                self.setDirectory(rootdir)
            if catalogue_chooser:
                self.catalogue_chooser = self.CatalogueGroupBox()
                self.catalogue_chooser.setMinimumWidth(122)
                self.modify()

        def modify(self):
            splitter = self.findChild(QSplitter, None)
            sidebar = splitter.findChild(QListView, "sidebar")
            listview = splitter.findChild(QListView, "listView")
            filename_label = self.findChild(QLabel, "fileNameLabel")
            # TODO set a theme appropriate
            # border colour, as in kodi-remote
            listview.setStyleSheet(
                "border: 1px solid silver; border-radius: 4px"
            )
            filename_label.setFixedWidth(120)
            sidebar.hide()
            children = splitter.findChildren(QSplitterHandle, None)
            for c in children:
                c.setDisabled(True)
            splitter.insertWidget(0, self.catalogue_chooser)

        class CatalogueGroupBox(QGroupBox):

            def __init__(self):
                super().__init__()
                self.chkbox_catalogues = {
                    "checkBoxOpus": PlaylistRecomposer.Catalogue.OPUS,
                    "checkBoxBWV": PlaylistRecomposer.Catalogue.BWV,
                    "checkBoxKoechel": PlaylistRecomposer.Catalogue.KOECHEL,
                    "checkBoxDeutsch": PlaylistRecomposer.Catalogue.DEUTSCH,
                    "checkBoxHoboken": PlaylistRecomposer.Catalogue.HOBOKEN,
                }
                self.setObjectName("checkGroupBox")
                self.setCheckable(True)
                self.verticalLayout = QVBoxLayout(self)
                self.verticalLayout.setObjectName("verticalLayout")
                self.checkBoxOpus = QCheckBox(self)
                self.checkBoxOpus.setObjectName("checkBoxOpus")
                self.checkBoxOpus.setChecked(True)
                self.verticalLayout.addWidget(self.checkBoxOpus)
                self.checkBoxBWV = QCheckBox(self)
                self.checkBoxBWV.setObjectName("checkBoxBWV")
                self.checkBoxBWV.setChecked(True)
                self.verticalLayout.addWidget(self.checkBoxBWV)
                self.checkBoxKoechel = QCheckBox(self)
                self.checkBoxKoechel.setObjectName("checkBoxKoechel")
                self.checkBoxKoechel.setChecked(True)
                self.verticalLayout.addWidget(self.checkBoxKoechel)
                self.checkBoxDeutsch = QCheckBox(self)
                self.checkBoxDeutsch.setObjectName("checkBoxDeutsch")
                self.checkBoxDeutsch.setChecked(True)
                self.verticalLayout.addWidget(self.checkBoxDeutsch)
                self.checkBoxHoboken = QCheckBox(self)
                self.checkBoxHoboken.setObjectName("checkBoxHoboken")
                self.checkBoxHoboken.setChecked(True)
                self.verticalLayout.addWidget(self.checkBoxHoboken)
                self.setTitle("Select All")
                self.checkBoxOpus.setText("Opus")
                self.checkBoxBWV.setText("BWV")
                self.checkBoxKoechel.setText("Köchel")
                self.checkBoxDeutsch.setText("Deutsch")
                self.checkBoxHoboken.setText("Hoboken")
                self.toggled.connect(self.toggle_all)
                for box in self.findChildren(QCheckBox):
                    box.stateChanged.connect(self.manage_states)
                    # box.stateChanged.connect(self.manage_states)

            def toggle_all(self, state):
                for box in self.sender().findChildren(QCheckBox):
                    box.setChecked(state)
                    box.setEnabled(True)

            def manage_states(self):
                checked = []
                for c in self.findChildren(QCheckBox):
                    if c.isChecked():
                        checked.append(c)
                if len(checked) < len(PlaylistRecomposer.Catalogue):
                    self.setChecked(False)
                    for box in checked:
                        box.setChecked(True)
                else:
                    self.setChecked(True)

            def get_selections(self):
                selected_catalogues = []
                for box in self.findChildren(QCheckBox):
                    if box.isChecked():
                        selected_catalogues.append(
                            self.chkbox_catalogues[box.objectName()]
                        )
                return selected_catalogues

    class Catalogue(Enum):
        OPUS = 0
        BWV = 1
        KOECHEL = 2
        DEUTSCH = 3
        HOBOKEN = 4

    class Columns(IntEnum):
        CATALOGUE_NUM = 0
        SUFFIX = 1
        PIECE = 2
        FILE = 3
        TITLE = 4
        LENGTH = 5

    class Roman():
        
        numerals = {
            "CM": 900,
            "M": 1000,
            "CD": 400,
            "D": 500,
            "XC": 90,
            "C": 100,
            "XL": 40,
            "L": 50,
            "IX": 9,
            "X": 10,
            "IV": 4,
            "V": 5,
            "I": 1,
        }
        
        decimals = {
            1000: "M",
            900: "CM",
            500: "D",
            400: "CD",
            100: "C",
            90: "XC",
            50: "L",
            40: "XL",
            10: "X",
            9: "IX",
            5: "V",
            4: "IV",
            1: "I",
        }

        @classmethod
        def to_decimal(self, roman_n):
            d = 0
            for key in self.numerals:
                while roman_n.find(key) >= 0:
                    d += self.numerals[key]
                    roman_n = roman_n.replace(key, "", 1)
            return d

        @classmethod
        def from_decimal(self, decimal_n):
            r = ""
            for key in self.decimals:
                while decimal_n % key < decimal_n:
                    r += self.decimals[key]
                    decimal_n -= key
            return r

        def is_roman(value):
            return re.search(r"[MDCLXVI]", value, re.IGNORECASE)


if __name__ == "__main__":
    QApplication()
    if len(sys.argv) > 1:
        rootdir = sys.argv[1]
    else:
        rootdir = os.path.expanduser("~")
    pr = PlaylistRecomposer(rootdir)
    rc = pr.return_code
    if rc:
        if rc in (1, 3):
            err_msg = (
                "\nCannot continue unless a folder is chosen\t\n"
            )
            exit_type = "Aborting"
        elif rc == 2:
            err_msg = (
                "\nCannot continue unless catalogues are chosen\t\n"
            )
            exit_type = "Aborting"                       
        elif rc == 4:
            err_msg = (
                "\nCannot continue.\n\nPlaylists folder "
                "and sources folder must be different.\t\t\t"
            )
            exit_type = "Error"
        elif rc == 5:
            err_msg = (
                "\nCannot continue.\n\nPlaylists folder "
                "and sources folder must share the same parent.\n\n"
                "(This is because playlist media paths will be written\n"
                "relative to the playlists folder so that the parent tree\n"
                "can be easily moved or copied to one of your other devices.)"
            )
            exit_type = "Error"
        elif rc == 6:
            err_msg = (
                "\nCannot continue.\n\n"
                "No playlists in chosen search folder.\t\n"
            )
            exit_type = "Aborting"
        QMessageBox(
            QMessageBox.Critical, f"Playlist Generator - {exit_type}", err_msg
        ).exec()
