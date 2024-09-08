# -*- coding: utf-8 -*-
# @Time : 2024/8/23 22:16
# @Author : DecadeX

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

from PySide6.QtCore import QEvent, QThread, Signal, Qt
from PySide6.QtGui import QAction, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QTextBrowser, QMenuBar, QCheckBox, QDialog, QPushButton, \
    QLabel, QMessageBox, QVBoxLayout, QWidget, QFrame, QScrollArea, QGridLayout, QFileDialog

from Module import getIdvLogin, programDir, loadConfig, is_process_running, getRunningTime, \
    savePlayRecord, loadPlayRecord, checkGameIsLogin

__version__ = "1.0.0"

from idvToolLogicMain import idvToolLogic


class MainWindow(QMainWindow):
    def __init__(self):
        # 主页面
        super().__init__()
        self.workingDirectory = loadConfig("working directory", "value")
        self.setWindowTitle("第五人格小助手")

        self.setGeometry(0, 0, 800, 600)
        grid = QGridLayout()
        # vbox = QVBoxLayout()

        top_widget = QWidget()
        top_widget.setLayout(grid)
        self.setCentralWidget(top_widget)

        # 日志输出
        self.logBrowser: QTextBrowser
        self.logger = None
        self.logOutput()

        # 菜单
        self.menuBar: QMenuBar
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

    def startGameThread(self):
        if os.path.isdir(str(self.workingDirectory)):
            self.idvToolLogicThread.start()
            self.startButton.close()
        else:
            self.logger.info("请先打开设置选择第五人格所在目录")

    def checkIsDarkMode(self):
        # 检测系统主题
        palette = QApplication.palette()
        if palette.color(QPalette.Window).lightness() < 128:
            return True
        else:
            return False
        # return True

    def threadManager(self):
        self.settingsLogicThread = self.autoSaveConfig(self)
        self.settingsLogicThread.sig.connect(self.signalProcessing)
        self.settingsLogicThread.start()

        self.idvToolLogicThread = idvToolLogic(self, )
        self.idvToolLogicThread.sig.connect(self.signalProcessing)
        # self.idvToolLogicThread.start()

        self.checkIsGameLoginThread = self.checkIsGameLogin(self)
        self.checkIsGameLoginThread.sig.connect(self.signalProcessing)
        # self.checkIsGameLoginThread.start()

        self.playtimeUpdateThread = self.playtimeUpdate(self)
        self.playtimeUpdateThread.sig.connect(self.signalProcessing)
        # self.playtimeUpdateThread.start()

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
            self.logger.info(f"已将工作目录设置为为 -> {self.workingDirectory}")

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
        checkUpdateLabel = QLabel("别按了，检查更新还没做呢！", self.checkUpdateWindow)
        checkUpdateLabel.setFixedSize(self.checkUpdateWindow.width(),
                                      int(self.checkUpdateWindow.height() / 2))
        self.checkUpdateButton.clicked.connect(self.checkUpdate)

    def signalProcessing(self, sig):
        pass

    def checkUpdate(self):
        self.logger.info("别按了，检查更新还没做呢！")
        self.checkUpdateWindow.show()

    def menuBarClicked(self, action):
        if action.text() == "设置":
            self.settingsWindow.show()
        elif action.text() == "退出":
            sys.exit()
        elif action.text() == "关于":
            self.aboutWindow.show()
        else:
            self.logger.info(f"别点了，没做完呢")

    def buttonClicked(self):
        self.logger.info("别点了，没做完呢")

    def closeEvent(self, event: QEvent):
        # self.logger.info("窗口正在关闭")

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

            # if not data:
            #     return

            # 主布局
            playRecordLayout = QVBoxLayout()

            # 信息显示容器
            containerWidget = QWidget()
            if isDarkMode is True:
                containerWidget.setStyleSheet('background-color: #1e1e1e;')
            else:
                containerWidget.setStyleSheet('background-color: white;')
            containerLayout = QVBoxLayout(containerWidget)

            # 按标题分组数据
            grouped_data = {}
            for item in data:
                title, details = list(item.items())[0]
                if title not in grouped_data:
                    grouped_data[title] = []
                grouped_data[title].append(details)

            # 为每个标题组创建一个小窗口
            for title, detailsList in grouped_data.items():
                smallWindow = QFrame()
                smallWindow.setFrameShape(QFrame.Box)
                smallWindow.setLineWidth(1)
                # smallWindow.setFixedSize(50, 30)

                # 创建小窗口布局
                smallWindowLayout = QVBoxLayout(smallWindow)

                # 添加标题
                titleLabel = QLabel(title)
                titleLabel.setStyleSheet("font-weight: bold;")
                smallWindowLayout.addWidget(titleLabel)

                # 添加详细信息
                for details in detailsList:
                    for detail_key, detail_value in details.items():
                        label = QLabel(f"{detail_key}: {detail_value}")
                        smallWindowLayout.addWidget(label)
                    smallWindowLayout.addWidget(QLabel("---"))  # 添加分隔符

                # 将小窗口添加到容器布局中
                containerLayout.addWidget(smallWindow)

            # 设置容器的布局
            containerWidget.setLayout(containerLayout)

            # 创建滚动区域
            scrollArea = QScrollArea()
            scrollArea.setWidget(containerWidget)
            scrollArea.setWidgetResizable(True)

            # 设置主窗口的布局
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

        def __init__(self, w):
            super().__init__()
            self.w = w

        def run(self):
            try:
                self.w.logger.info("正在检测游戏是否登录！")
                while True:
                    if checkGameIsLogin() is True:
                        break
                    time.sleep(1)

                if self.w.autoExitIdvLoginEnable.isChecked() is True:
                    subprocess.run(f"taskkill /im {self.w.idvLoginName} /f", shell=True)
                self.w.logger.info("登录成功！")

                if self.w.timerEnable.isChecked() is True:
                    self.w.playtimeUpdateThread.start()

                # self.w.checkIsGameLoginThread.exit()
                return
            except Exception as e:
                saveCrashLog(e)

    class playtimeUpdate(QThread):
        sig = Signal(str)

        def __init__(self, w):
            super().__init__()
            self.w = w

        def run(self):
            timerEnable = self.w.timerEnable.isChecked()
            runTime = None
            startTime = datetime.now()
            while is_process_running("dwrg.exe"):
                if timerEnable is True:
                    time.sleep(1)
                    runTime = getRunningTime(startTime)
                    self.w.playtimeShow.setText(str(runTime))
            self.w.playtimeShow.setText(f"游戏已退出：{runTime}")
            self.w.logger.info("游戏已退出")
            savePlayRecord(self.w.playRecordList, startTime, runTime)

    class autoSaveConfig(QThread):
        sig = Signal(str)

        def __init__(self, w):
            super().__init__()
            self.w = w

        def run(self):
            while True:
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


def saveCrashLog(logStr):
    if not os.path.exists(os.path.join(programDir, "crash.log")):
        open(os.path.join(programDir, "crash.log"), 'w').write("")
    open(os.path.join(programDir, "crash.log"), 'a').write(str(logStr))


def main():
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        # sys.exit(app.exec())
        app.exec()
    except Exception as e:
        saveCrashLog(e)


if __name__ == "__main__":
    main()
