# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'kodi_remote.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QListView, QMainWindow, QProgressBar, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(19)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(640, 480))
        MainWindow.setFocusPolicy(Qt.NoFocus)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(9, 9, 9, -1)
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy1.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy1)
        self.stackedWidget.setMinimumSize(QSize(296, 0))
        self.page = QWidget()
        self.page.setObjectName(u"page")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.page.sizePolicy().hasHeightForWidth())
        self.page.setSizePolicy(sizePolicy2)
        self.gridLayout = QGridLayout(self.page)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayoutPlaylist = QVBoxLayout()
        self.verticalLayoutPlaylist.setObjectName(u"verticalLayoutPlaylist")
        self.verticalLayoutPlaylist.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.listView = QListView(self.page)
        self.listView.setObjectName(u"listView")
        sizePolicy1.setHeightForWidth(self.listView.sizePolicy().hasHeightForWidth())
        self.listView.setSizePolicy(sizePolicy1)
        self.listView.setMinimumSize(QSize(296, 0))
        self.listView.setFrameShape(QFrame.NoFrame)
        self.listView.setFrameShadow(QFrame.Plain)
        self.listView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayoutPlaylist.addWidget(self.listView)

        self.lineEditFilter = QLineEdit(self.page)
        self.lineEditFilter.setObjectName(u"lineEditFilter")
        self.lineEditFilter.setMinimumSize(QSize(0, 25))
        self.lineEditFilter.setMaximumSize(QSize(16777215, 25))
        self.lineEditFilter.setBaseSize(QSize(0, 25))
#if QT_CONFIG(tooltip)
        self.lineEditFilter.setToolTip(u"<html><head/><body><p>Filter playlist items by literal text or keywords. Keywords can be whole words or word beginnings separated by the + character. There is no need for accented characters in proper names, (playlist diacritics will be decoded before matching).<br></p></body></html>")
#endif // QT_CONFIG(tooltip)
        self.lineEditFilter.setToolTipDuration(10000)
        self.lineEditFilter.setFrame(True)
        self.lineEditFilter.setPlaceholderText(u"Enter literal text or word+word to filter")
        self.lineEditFilter.setClearButtonEnabled(True)

        self.verticalLayoutPlaylist.addWidget(self.lineEditFilter)


        self.gridLayout.addLayout(self.verticalLayoutPlaylist, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        sizePolicy2.setHeightForWidth(self.page_2.sizePolicy().hasHeightForWidth())
        self.page_2.setSizePolicy(sizePolicy2)
        self.page_2.setStyleSheet(u"")
        self.gridLayout_3 = QGridLayout(self.page_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frameLoading = QFrame(self.page_2)
        self.frameLoading.setObjectName(u"frameLoading")
        self.frameLoading.setFrameShape(QFrame.NoFrame)
        self.frameLoading.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_3 = QHBoxLayout(self.frameLoading)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacerLeft = QSpacerItem(56, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacerLeft)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalSpacerTop = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacerTop)

        self.progressBar = QProgressBar(self.frameLoading)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(10)
        self.progressBar.setTextVisible(False)

        self.verticalLayout.addWidget(self.progressBar)

        self.labelLoading = QLabel(self.frameLoading)
        self.labelLoading.setObjectName(u"labelLoading")
        font = QFont()
        font.setPointSize(12)
        self.labelLoading.setFont(font)
        self.labelLoading.setFrameShape(QFrame.NoFrame)
        self.labelLoading.setFrameShadow(QFrame.Plain)
        self.labelLoading.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.labelLoading, 0, Qt.AlignHCenter)

        self.verticalSpacerBottom = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacerBottom)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.horizontalSpacerRight = QSpacerItem(56, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacerRight)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 3)
        self.horizontalLayout_3.setStretch(2, 1)

        self.gridLayout_3.addWidget(self.frameLoading, 0, 0, 1, 1)

        self.gridLayout_3.setColumnStretch(0, 1)
        self.stackedWidget.addWidget(self.page_2)

        self.horizontalLayout.addWidget(self.stackedWidget)

        self.stackedWidgetDetails = QStackedWidget(self.centralwidget)
        self.stackedWidgetDetails.setObjectName(u"stackedWidgetDetails")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(55)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stackedWidgetDetails.sizePolicy().hasHeightForWidth())
        self.stackedWidgetDetails.setSizePolicy(sizePolicy3)
        self.stackedWidgetDetails.setFocusPolicy(Qt.NoFocus)
        self.stackedWidgetDetails.setStyleSheet(u"")
        self.stackedWidgetDetails.setFrameShape(QFrame.NoFrame)
        self.stackedWidgetDetails.setFrameShadow(QFrame.Plain)
        self.pageDetails = QWidget()
        self.pageDetails.setObjectName(u"pageDetails")
        self.gridLayout_4 = QGridLayout(self.pageDetails)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.textEditBrowsing = QTextEdit(self.pageDetails)
        self.textEditBrowsing.setObjectName(u"textEditBrowsing")
        self.textEditBrowsing.setFocusPolicy(Qt.NoFocus)
        self.textEditBrowsing.setFrameShape(QFrame.NoFrame)
        self.textEditBrowsing.setFrameShadow(QFrame.Plain)
        self.textEditBrowsing.setLineWidth(1)
        self.textEditBrowsing.setReadOnly(True)

        self.gridLayout_4.addWidget(self.textEditBrowsing, 0, 0, 1, 1)

        self.stackedWidgetDetails.addWidget(self.pageDetails)

        self.horizontalLayout.addWidget(self.stackedWidgetDetails)

        self.horizontalLayout.setStretch(0, 3)
        self.horizontalLayout.setStretch(1, 4)

        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.verticalLayoutControls = QVBoxLayout()
        self.verticalLayoutControls.setSpacing(0)
        self.verticalLayoutControls.setObjectName(u"verticalLayoutControls")
        self.verticalLayoutControls.setContentsMargins(9, 9, 9, 9)
        self.widgetPlaying = QWidget(self.centralwidget)
        self.widgetPlaying.setObjectName(u"widgetPlaying")
        self.horizontalLayout_6 = QHBoxLayout(self.widgetPlaying)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, -1, 0, -1)
        self.horizontalLayoutPlaying = QHBoxLayout()
        self.horizontalLayoutPlaying.setObjectName(u"horizontalLayoutPlaying")
        self.labelCurrentPosition = QLabel(self.widgetPlaying)
        self.labelCurrentPosition.setObjectName(u"labelCurrentPosition")

        self.horizontalLayoutPlaying.addWidget(self.labelCurrentPosition)

        self.horizontalSliderSeek = QSlider(self.widgetPlaying)
        self.horizontalSliderSeek.setObjectName(u"horizontalSliderSeek")
        self.horizontalSliderSeek.setFocusPolicy(Qt.NoFocus)
        self.horizontalSliderSeek.setMaximum(99999)
        self.horizontalSliderSeek.setSingleStep(100)
        self.horizontalSliderSeek.setPageStep(10000)
        self.horizontalSliderSeek.setTracking(False)
        self.horizontalSliderSeek.setOrientation(Qt.Horizontal)

        self.horizontalLayoutPlaying.addWidget(self.horizontalSliderSeek)

        self.labelDuration = QLabel(self.widgetPlaying)
        self.labelDuration.setObjectName(u"labelDuration")

        self.horizontalLayoutPlaying.addWidget(self.labelDuration, 0, Qt.AlignRight)


        self.horizontalLayout_6.addLayout(self.horizontalLayoutPlaying)


        self.verticalLayoutControls.addWidget(self.widgetPlaying)

        self.widgetPlayerControls = QWidget(self.centralwidget)
        self.widgetPlayerControls.setObjectName(u"widgetPlayerControls")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.widgetPlayerControls.sizePolicy().hasHeightForWidth())
        self.widgetPlayerControls.setSizePolicy(sizePolicy4)
        self.widgetPlayerControls.setLayoutDirection(Qt.LeftToRight)
        self.horizontalLayout_2 = QHBoxLayout(self.widgetPlayerControls)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, -1, 0, -1)
        self.horizontalLayoutAll = QHBoxLayout()
        self.horizontalLayoutAll.setObjectName(u"horizontalLayoutAll")
        self.horizontalLayoutAll.setContentsMargins(-1, 6, -1, -1)
        self.pushButtonCombine = QPushButton(self.widgetPlayerControls)
        self.pushButtonCombine.setObjectName(u"pushButtonCombine")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.pushButtonCombine.sizePolicy().hasHeightForWidth())
        self.pushButtonCombine.setSizePolicy(sizePolicy5)
        self.pushButtonCombine.setMaximumSize(QSize(30, 25))
        self.pushButtonCombine.setBaseSize(QSize(0, 0))
#if QT_CONFIG(tooltip)
        self.pushButtonCombine.setToolTip(u"Combine items from all playlists.")
#endif // QT_CONFIG(tooltip)
        self.pushButtonCombine.setToolTipDuration(5000)
        self.pushButtonCombine.setIconSize(QSize(25, 20))

        self.horizontalLayoutAll.addWidget(self.pushButtonCombine)

        self.horizontalSpacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayoutAll.addItem(self.horizontalSpacer)

        self.horizontalLayoutButtons = QHBoxLayout()
        self.horizontalLayoutButtons.setSpacing(15)
        self.horizontalLayoutButtons.setObjectName(u"horizontalLayoutButtons")
        self.pushButtonSkipBackward = QPushButton(self.widgetPlayerControls)
        self.pushButtonSkipBackward.setObjectName(u"pushButtonSkipBackward")
        sizePolicy6 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.pushButtonSkipBackward.sizePolicy().hasHeightForWidth())
        self.pushButtonSkipBackward.setSizePolicy(sizePolicy6)
        self.pushButtonSkipBackward.setMinimumSize(QSize(0, 0))
        self.pushButtonSkipBackward.setMaximumSize(QSize(30, 25))
        self.pushButtonSkipBackward.setBaseSize(QSize(0, 0))
        self.pushButtonSkipBackward.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayoutButtons.addWidget(self.pushButtonSkipBackward)

        self.pushButtonPlay = QPushButton(self.widgetPlayerControls)
        self.pushButtonPlay.setObjectName(u"pushButtonPlay")
        sizePolicy6.setHeightForWidth(self.pushButtonPlay.sizePolicy().hasHeightForWidth())
        self.pushButtonPlay.setSizePolicy(sizePolicy6)
        self.pushButtonPlay.setMinimumSize(QSize(0, 0))
        self.pushButtonPlay.setMaximumSize(QSize(30, 25))
        self.pushButtonPlay.setBaseSize(QSize(0, 0))
        self.pushButtonPlay.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayoutButtons.addWidget(self.pushButtonPlay)

        self.pushButtonStop = QPushButton(self.widgetPlayerControls)
        self.pushButtonStop.setObjectName(u"pushButtonStop")
        self.pushButtonStop.setEnabled(True)
        sizePolicy6.setHeightForWidth(self.pushButtonStop.sizePolicy().hasHeightForWidth())
        self.pushButtonStop.setSizePolicy(sizePolicy6)
        self.pushButtonStop.setMaximumSize(QSize(30, 25))
        self.pushButtonStop.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayoutButtons.addWidget(self.pushButtonStop)

        self.pushButtonSkipForward = QPushButton(self.widgetPlayerControls)
        self.pushButtonSkipForward.setObjectName(u"pushButtonSkipForward")
        sizePolicy6.setHeightForWidth(self.pushButtonSkipForward.sizePolicy().hasHeightForWidth())
        self.pushButtonSkipForward.setSizePolicy(sizePolicy6)
        self.pushButtonSkipForward.setMinimumSize(QSize(0, 0))
        self.pushButtonSkipForward.setMaximumSize(QSize(30, 25))
        self.pushButtonSkipForward.setBaseSize(QSize(0, 0))
        self.pushButtonSkipForward.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayoutButtons.addWidget(self.pushButtonSkipForward)


        self.horizontalLayoutAll.addLayout(self.horizontalLayoutButtons)

        self.pushButtonMute = QPushButton(self.widgetPlayerControls)
        self.pushButtonMute.setObjectName(u"pushButtonMute")
        sizePolicy6.setHeightForWidth(self.pushButtonMute.sizePolicy().hasHeightForWidth())
        self.pushButtonMute.setSizePolicy(sizePolicy6)
        self.pushButtonMute.setMaximumSize(QSize(30, 25))
        self.pushButtonMute.setFlat(True)

        self.horizontalLayoutAll.addWidget(self.pushButtonMute, 0, Qt.AlignRight)

        self.horizontalSliderVolume = QSlider(self.widgetPlayerControls)
        self.horizontalSliderVolume.setObjectName(u"horizontalSliderVolume")
        sizePolicy6.setHeightForWidth(self.horizontalSliderVolume.sizePolicy().hasHeightForWidth())
        self.horizontalSliderVolume.setSizePolicy(sizePolicy6)
        self.horizontalSliderVolume.setMaximumSize(QSize(100, 16777215))
        self.horizontalSliderVolume.setOrientation(Qt.Horizontal)

        self.horizontalLayoutAll.addWidget(self.horizontalSliderVolume)

        self.horizontalLayoutAll.setStretch(1, 10)
        self.horizontalLayoutAll.setStretch(2, 16)
        self.horizontalLayoutAll.setStretch(3, 8)
        self.horizontalLayoutAll.setStretch(4, 4)

        self.horizontalLayout_2.addLayout(self.horizontalLayoutAll)


        self.verticalLayoutControls.addWidget(self.widgetPlayerControls)


        self.gridLayout_2.addLayout(self.verticalLayoutControls, 1, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        QWidget.setTabOrder(self.listView, self.lineEditFilter)
        QWidget.setTabOrder(self.lineEditFilter, self.pushButtonCombine)
        QWidget.setTabOrder(self.pushButtonCombine, self.horizontalSliderSeek)
        QWidget.setTabOrder(self.horizontalSliderSeek, self.pushButtonSkipBackward)
        QWidget.setTabOrder(self.pushButtonSkipBackward, self.pushButtonPlay)
        QWidget.setTabOrder(self.pushButtonPlay, self.pushButtonStop)
        QWidget.setTabOrder(self.pushButtonStop, self.pushButtonSkipForward)
        QWidget.setTabOrder(self.pushButtonSkipForward, self.pushButtonMute)
        QWidget.setTabOrder(self.pushButtonMute, self.horizontalSliderVolume)
        QWidget.setTabOrder(self.horizontalSliderVolume, self.stackedWidgetDetails)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Kodi Classical - Remote", None))
        self.labelLoading.setText(QCoreApplication.translate("MainWindow", u"Loading ...", None))
        self.textEditBrowsing.setPlaceholderText("")
        self.labelCurrentPosition.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.labelDuration.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.pushButtonCombine.setText("")
        self.pushButtonSkipBackward.setText("")
        self.pushButtonPlay.setText("")
        self.pushButtonStop.setText("")
        self.pushButtonSkipForward.setText("")
        self.pushButtonMute.setText("")
    # retranslateUi

