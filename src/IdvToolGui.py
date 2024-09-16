# -*- coding: utf-8 -*-
# @Time : 2024/8/23 22:16
# @Author : DecadeX

import datetime
import json
import logging
import os
import subprocess
import sys
import time
import traceback

from PySide6.QtCore import QEvent, QThread, Signal, Qt, Slot
from PySide6.QtGui import QAction, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QTextBrowser, QMenuBar, QCheckBox, QDialog, QPushButton, \
    QLabel, QMessageBox, QVBoxLayout, QWidget, QFrame, QScrollArea, QGridLayout, QFileDialog, QSizePolicy, \
    QTextEdit

from Module import getIdvLogin, programDir, loadConfig, is_process_running, getRunningTime, \
    savePlayRecord, loadPlayRecord, checkGameIsLogin

__version__ = "1.1.0"

from idvToolLogicMain import idvToolLogic


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.workingDirectory = loadConfig("working directory", "value")
        self.setWindowTitle("idv-tool-gui")

        self.setGeometry(0, 0, 800, 600)
        grid = QGridLayout()
        # vbox = QVBoxLayout()

        top_widget = QWidget()
        top_widget.setLayout(grid)
        self.setCentralWidget(top_widget)

        # 日志输出
        self.logBrowser = None
        self.logger = None
        self.logOutput()

        # 菜单
        self.menuBar = None
        self.fileMenu = None
        self.aboutMenu = None
        self.idvToolMenuBar()

        # 设置
        self.workingDirectorySelect = None
        self.settingsWindow = None
        self.autoUpdateEnable = None
        self.timerEnable = None
        self.savePlaytimeEnable = None
        self.autoExitIdvLoginEnable = None

        self.idvToolSettings()

        # 关于
        self.aboutWindow = None
        self.checkUpdateButton = None
        self.checkUpdateWindow = None
        self.idvToolAbout()

        # 游玩记录
        self.playRecordList = loadPlayRecord()
        self.playRecord = self.idvToolPlayRecord(self.playRecordList, self.checkIsDarkMode())
        self.playRecord.setFixedWidth(260)

        # 游玩时间
        self.playtime = QWidget()
        self.playtime.setFixedSize(250, 35)
        if self.checkIsDarkMode():
            self.playtime.setStyleSheet('background-color: #2e2e2e; border-radius: 5px; ')
        else:
            self.playtime.setStyleSheet('background-color: white; border-radius: 5px')

        self.startTime = None
        self.playtimeShow = QLabel("None", self.playtime)
        self.playtimeShow.setFixedSize(250, 35)
        self.playtimeShow.move(10, 0)

        self.startButton = QPushButton("启动游戏", self.menuBar)
        self.startButton.setFixedSize(66, 33)
        self.startButton.move(int(self.menuBar.width() / 1.75) - 5, 0)
        self.startButton.clicked.connect(self.startGameThread)

        # 线程
        self.idvToolLogicThread = None
        self.settingsLogicThread = None
        self.playtimeUpdateThread = None
        self.checkIsGameLoginThread = None
        self.threadManager()

        self.idvLoginName = getIdvLogin()

        # 主布局
        grid.addWidget(self.menuBar, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.playtime, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.logBrowser, 1, 0)
        grid.addWidget(self.playRecord, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)

    def checkIsDarkMode(self):
        # 检测系统主题
        palette = QApplication.palette()
        if palette.color(QPalette.Window).lightness() < 128:
            return True
        else:
            return False

    def threadManager(self):
        self.settingsLogicThread = self.autoSaveConfig(self)
        self.settingsLogicThread.sig.connect(self.signalProcessing)
        self.settingsLogicThread.errorSig.connect(self.show_error_message)
        self.settingsLogicThread.start()

        self.idvToolLogicThread = idvToolLogic(self, )
        self.idvToolLogicThread.sig.connect(self.signalProcessing)
        self.idvToolLogicThread.errorSig.connect(self.show_error_message)

        self.checkIsGameLoginThread = self.checkIsGameLogin(self)
        self.checkIsGameLoginThread.sig.connect(self.signalProcessing)
        self.checkIsGameLoginThread.errorSig.connect(self.show_error_message)

        self.playtimeUpdateThread = self.playtimeUpdate(self)
        self.playtimeUpdateThread.sig.connect(self.signalProcessing)
        self.playtimeUpdateThread.errorSig.connect(self.show_error_message)

    def logOutput(self):
        self.logBrowser = QTextBrowser(self)
        if self.checkIsDarkMode():
            self.logBrowser.setStyleSheet('background-color: #2e2e2e; border-radius: 5px; color: white;')
        else:
            self.logBrowser.setStyleSheet('background-color: white; border-radius: 5px')
        self.logger = logging.getLogger()
        self.logger.addHandler(self.QTextBrowserHandler(self.logBrowser))
        self.logger.setLevel(logging.INFO)

    def idvToolMenuBar(self):
        # 菜单栏
        self.menuBar = QMenuBar(self)
        if self.checkIsDarkMode():
            self.menuBar.setStyleSheet(
                "QMenuBar { background-color: #2e2e2e; color: white; border-radius: 5px; }"
                "QMenu::item { padding: 5px 20px; background-color: #2e2e2e; color: white; }"
                "QMenu::item:selected { background-color: #505050; color: white; border-radius: 5px; }"
                "QMenu::item:disabled { color: gray; background-color: #2e2e2e; }"
                "QMenu::separator { background-color: #444444; height: 1px; }"
            )
        else:
            self.menuBar.setStyleSheet(
                "QMenuBar { background-color: white; border-radius: 5px; }"
                "QMenu::item { padding: 5px 20px; }"
                "QMenu::item:selected { background-color: darkgray; border-radius: 5px; }"
                "QMenu::item:disabled { color: gray; border-radius: 5px; }"
            )

        # self.menuBar.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

        self.fileMenu = self.menuBar.addMenu("文件")
        # self.fileMenu.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.fileMenu.addAction("设置")
        self.fileMenu.addAction("退出")  # .setShortcut("Ctrl+S")
        self.fileMenu.triggered[QAction].connect(self.menuBarClicked)

        self.aboutMenu = self.menuBar.addMenu("关于")
        # self.aboutMenu.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.aboutMenu.addAction("关于")
        self.aboutMenu.triggered[QAction].connect(self.menuBarClicked)

    def idvToolSettings(self):
        # 页面
        self.settingsWindow = QDialog()
        self.settingsWindow.setWindowTitle("设置")
        self.settingsWindow.setFixedSize(150, 200)
        self.settingsWindow.setModal(True)

        # 选项
        self.workingDirectorySelect = QPushButton("选择工作目录", self.settingsWindow)
        self.workingDirectorySelect.setFixedSize(int(self.settingsWindow.width() * 0.8), 20)
        self.workingDirectorySelect.clicked.connect(self.selectWorkingDirectory)
        self.workingDirectorySelect.move(10, 10)

        self.autoUpdateEnable = QCheckBox("自动更新", self.settingsWindow)
        self.autoUpdateEnable.setChecked(loadConfig("auto update", "value") is True)
        self.autoUpdateEnable.move(10, 40)

        self.timerEnable = QCheckBox("计时器", self.settingsWindow)
        self.timerEnable.setChecked(loadConfig("timer", "value") is True)
        self.timerEnable.move(10, 70)

        self.savePlaytimeEnable = QCheckBox("自动保存游戏时间", self.settingsWindow)
        self.savePlaytimeEnable.setChecked(loadConfig("auto save playtime", "value") is True)
        self.savePlaytimeEnable.move(10, 100)

        self.autoExitIdvLoginEnable = QCheckBox("自动关闭 idv-login", self.settingsWindow)
        self.autoExitIdvLoginEnable.setChecked(loadConfig("auto exit idv-login", "value") is True)
        self.autoExitIdvLoginEnable.move(10, 130)

    def selectWorkingDirectory(self):
        selectDir = QFileDialog.getExistingDirectory(None, "请选择第五人格主程序所在的文件夹", self.workingDirectory)
        if os.path.isdir(selectDir):
            self.workingDirectory = selectDir.replace('/', '\\')
            self.logger.info(f"已将工作目录设置为 -> {self.workingDirectory}")

    def idvToolAbout(self):
        # 关于
        self.aboutWindow = QDialog()
        self.aboutWindow.setWindowTitle("关于")
        self.aboutWindow.setFixedSize(150, 200)
        self.aboutWindow.setModal(True)
        QLabel("开发者：DecadeX", self.aboutWindow).move(10, 10)
        QLabel(f"版本：{__version__}", self.aboutWindow).move(10, 40)

        self.checkUpdateButton = QPushButton("检查更新", self.aboutWindow)
        self.checkUpdateButton.setFixedSize(60, 30)
        self.checkUpdateButton.move(int((self.aboutWindow.width() / 2) - 30), 100)
        self.checkUpdateWindow = QDialog()
        self.checkUpdateWindow.setWindowTitle("检查更新")
        self.checkUpdateWindow.setModal(True)
        self.checkUpdateWindow.setFixedSize(200, 100)
        checkUpdateLabel = QLabel("检查更新还没做呢！", self.checkUpdateWindow)
        checkUpdateLabel.setFixedSize(self.checkUpdateWindow.width(),
                                      int(self.checkUpdateWindow.height() / 2))
        self.checkUpdateButton.clicked.connect(self.checkUpdate)

    def signalProcessing(self, sig):
        pass

    @Slot(str)
    def show_error_message(self, error_message):
        error_dialog = ErrorDialog(error_message, self)
        error_dialog.exec()

    def checkUpdate(self):
        self.logger.info("检查更新还没做呢！")
        self.checkUpdateWindow.show()

    def startGameThread(self):
        if os.path.isdir(str(self.workingDirectory)):
            self.idvToolLogicThread.start()
            self.startButton.hide()
        else:
            self.logger.info("请先打开设置选择第五人格所在目录")

    def menuBarClicked(self, action):
        if action.text() == "设置":
            self.settingsWindow.show()
        elif action.text() == "退出":
            sys.exit()
        elif action.text() == "关于":
            self.aboutWindow.show()
        else:
            self.logger.info(f"没做完呢")

    def buttonClicked(self):
        self.logger.info("没做完呢")

    def closeEvent(self, event: QEvent):

        reply = QMessageBox.question(self, 'idv-tool', '是否确定退出？',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.idvToolLogicThread.exit()
            self.settingsLogicThread.exit()
            event.accept()
        else:
            event.ignore()

    class idvToolPlayRecord(QWidget):
        def __init__(self, data, isDarkMode: bool):
            super().__init__()

            playRecordLayout = QVBoxLayout()

            containerWidget = QWidget()
            if isDarkMode:
                containerWidget.setStyleSheet('background-color: #1e1e1e;')
            else:
                containerWidget.setStyleSheet('background-color: white;')
            containerLayout = QVBoxLayout(containerWidget)

            grouped_data = {}
            for item in data:
                date_str, details = list(item.items())[0]
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                if date not in grouped_data:
                    grouped_data[date] = []
                grouped_data[date].append(details)

            sorted_dates = sorted(grouped_data.keys(), reverse=True)

            for date in sorted_dates:
                title = date.strftime('%Y-%m-%d')
                detailsList = grouped_data[date]
                smallWindow = QFrame()
                smallWindow.setFrameShape(QFrame.Box)
                smallWindow.setLineWidth(1)

                smallWindowLayout = QVBoxLayout(smallWindow)

                titleLabel = QLabel(title)
                titleLabel.setStyleSheet("font-weight: bold;")
                smallWindowLayout.addWidget(titleLabel)

                num_details = len(detailsList)
                for idx, details in enumerate(detailsList):
                    for detail_key, detail_value in details.items():
                        # 替换键名
                        if detail_key == 'Start time':
                            detail_key = '开始时间'
                        elif detail_key == 'End time':
                            detail_key = '结束时间'
                        elif detail_key == 'Playtime':
                            detail_key = '游玩时间'

                        label = QLabel(f"{detail_key}: {detail_value}")
                        label.setWordWrap(True)
                        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                        smallWindowLayout.addWidget(label)

                    if idx < num_details - 1:
                        separator = QLabel("---")
                        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                        smallWindowLayout.addWidget(separator)

                containerLayout.addWidget(smallWindow)

            containerWidget.setLayout(containerLayout)

            scrollArea = QScrollArea()
            scrollArea.setWidget(containerWidget)
            scrollArea.setWidgetResizable(True)

            playRecordLayout.addWidget(scrollArea)
            self.setLayout(playRecordLayout)

    class QTextBrowserHandler(logging.Handler):
        def __init__(self, text_browser):
            super().__init__()
            self.text_browser = text_browser

        def emit(self, record):
            msg = self.format(record)
            self.text_browser.append(msg)

    # class test(QThread):
    #     sig = Signal(str)
    #
    #     def __init__(self):
    #         super().__init__()
    #
    #     def run(self):
    #         pass

    class checkIsGameLogin(QThread):
        sig = Signal(str)
        errorSig = Signal(str)

        def __init__(self, w):
            super().__init__()
            self.w = w

        def run(self):
            try:
                self.w.logger.info("正在检测游戏是否登录")
                while True:
                    if checkGameIsLogin() is True:
                        if is_process_running(self.w.idvLoginName) is False:
                            self.w.logger.info("idv-login 运行异常")
                            if is_process_running("dwr.exe") is True:
                                subprocess.run(f"taskkill /im dwrg.exe /f", shell=True)
                            self.w.startButton.show()
                            return
                        break
                    time.sleep(1)

                if self.w.autoExitIdvLoginEnable.isChecked() is True:
                    killIdvLoginResult = subprocess.run(f"taskkill /im {self.w.idvLoginName} /f",
                                                        shell=True, capture_output=True).stderr.decode('gbk')
                    if killIdvLoginResult.startswith('错误: 无法终止进程'):
                        self.w.logger.warning("权限不足, 无法终止idv-login, 请以管理员权限运行")
                self.w.logger.info("登录成功！")

                if self.w.timerEnable.isChecked() is True:
                    self.w.playtimeUpdateThread.start()

                return
            except Exception as e:
                error_message = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                self.errorSig.emit(error_message)

    class playtimeUpdate(QThread):
        sig = Signal(str)
        errorSig = Signal(str)

        def __init__(self, w):
            super().__init__()
            self.w = w

        def run(self):
            try:
                startTime = datetime.datetime.now()
                while True:
                    runTime = getRunningTime(startTime)
                    self.w.playtimeShow.setText(runTime)
                    if self.w.timerEnable.isChecked() is False:
                        return
                    if is_process_running("dwrg.exe") is False:
                        self.w.playtimeShow.setText(f"游戏已退出：{runTime}")
                        self.w.logger.info("游戏已退出")
                        self.w.startButton.show()
                        savePlayRecord(self.w.playRecordList, startTime, runTime)
                        return
                    time.sleep(1)
            except Exception as e:
                error_message = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                self.errorSig.emit(error_message)

    class autoSaveConfig(QThread):
        sig = Signal(str)
        errorSig = Signal(str)

        def __init__(self, w):
            super().__init__()
            self.w = w

        def run(self):
            while True:
                try:
                    time.sleep(3)
                    configData = [
                        {
                            "name": "working directory",
                            "value": self.w.workingDirectory
                        },
                        {
                            "name": "auto update",
                            "value": self.w.autoUpdateEnable.isChecked() is True
                        },
                        {
                            "name": "timer",
                            "value": self.w.timerEnable.isChecked() is True
                        },
                        {
                            "name": "auto save playtime",
                            "value": self.w.savePlaytimeEnable.isChecked() is True
                        },
                        {
                            "name": "auto exit idv-login",
                            "value": self.w.autoExitIdvLoginEnable.isChecked() is True
                        }
                    ]
                    with open(os.path.join(programDir, "config.json"), "w", encoding="utf8") as config:
                        json.dump(configData, config, ensure_ascii=False, indent=4)
                except Exception as e:
                    error_message = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                    self.errorSig.emit(error_message)


class ErrorDialog(QDialog):
    def __init__(self, error_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error")

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setText(error_message)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)
        self.resize(600, 400)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()


if __name__ == "__main__":
    main()
