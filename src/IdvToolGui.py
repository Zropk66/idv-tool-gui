# -*- coding: utf-8 -*-
# @Time : 2024/8/19 22:12
# @Author : DecadeX

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

from PySide6 import QtWidgets
from PySide6.QtCore import QSize, QEvent, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QTextBrowser, QMenuBar, QCheckBox, QDialog, QPushButton, \
    QLabel, QMessageBox

from Module import getDwrg, getIdvLogin, is_port_in_use, programDir, loadConfig, is_process_running, getRunningTime, \
    savePlaytime

__version__ = "1.0.0"


class MainWindow(QMainWindow):
    def __init__(self):
        # 主页面
        super().__init__()
        self.setWindowTitle("第五人格小助手")
        self.setFixedSize(800, 600)

        # 日志输出
        self.log_browser = QTextBrowser(self)
        self.log_browser.setFixedSize(QSize(
            int(self.size().width() / 1.25),
            int(self.size().height()))
        )
        self.log_browser.move(0, 33)
        self.logger = logging.getLogger()
        self.logger.addHandler(self.QTextBrowserHandler(self.log_browser))
        self.logger.setLevel(logging.INFO)

        # 游戏日志
        self.playLogList = QTextBrowser(self)
        self.playLogList.setFixedSize(
            int(self.width() - (self.size().width() / 1.25)),
            int(self.size().height())
        )
        self.playLogList.move(int(self.size().width() / 1.25), 33)

        self.playLogListLabel = QLabel("游玩日志", self.playLogList)
        self.playLogListLabel.setFixedSize(50, 15)
        self.playLogListLabel.move(
            int((self.width() - (self.size().width() / 1.25)) / 2.5),
            5
        )

        # 菜单栏
        self.menuBar = QMenuBar(self)
        self.menuBar.setFixedSize(self.width(), 33)

        self.fileMenu = self.menuBar.addMenu("文件")
        self.fileMenu.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.fileMenu.addAction("设置")
        self.fileMenu.addAction("退出")  # .setShortcut("Ctrl+S")
        self.fileMenu.triggered[QAction].connect(self.menuBarClicked)

        self.aboutMenu = self.menuBar.addMenu("关于")
        self.aboutMenu.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.aboutMenu.addAction("关于")
        self.aboutMenu.triggered[QAction].connect(self.menuBarClicked)

        # 设置页面
        self.settingsWindow = QDialog()
        self.settingsWindow.setWindowTitle("设置")
        self.settingsWindow.setFixedSize(150, 200)
        self.settingsWindow.setModal(True)

        self.autoUpdateEnable = QCheckBox("自动更新", self.settingsWindow)
        self.autoUpdateEnable.setChecked(loadConfig("auto update", "value") is True)
        self.autoUpdateEnable.move(10, 10)

        self.timerEnable = QCheckBox("计时器", self.settingsWindow)
        self.timerEnable.setChecked(loadConfig("timer", "value") is True)
        self.timerEnable.move(10, 40)

        self.savePlaytimeEnable = QCheckBox("自动保存游戏时间", self.settingsWindow)
        self.savePlaytimeEnable.setChecked(loadConfig("auto save playtime", "value") is True)
        self.savePlaytimeEnable.move(10, 70)

        self.autoExitIdvLoginEnable = QCheckBox("自动关闭 idv-login", self.settingsWindow)
        self.autoExitIdvLoginEnable.setChecked(loadConfig("auto exit idv-login", "value") is True)
        self.autoExitIdvLoginEnable.move(10, 100)

        # 关于页面
        self.aboutWindow = QDialog()
        self.aboutWindow.setWindowTitle("关于")
        self.aboutWindow.setFixedSize(150, 200)
        self.aboutWindow.setModal(True)
        self.authorLabel = QLabel("开发者：DecadeX", self.aboutWindow).move(10, 10)
        self.versionLabel = QLabel(f"版本：{__version__}", self.aboutWindow).move(10, 40)

        self.checkUpdateButton = QPushButton("检查更新", self.aboutWindow)
        self.checkUpdateButton.setFixedSize(60, 30)
        self.checkUpdateButton.move(int((self.aboutWindow.width() / 2) - 30), 100)
        self.checkUpdateWindow = QDialog()
        self.checkUpdateWindow.setWindowTitle("检查更新")
        self.checkUpdateWindow.setModal(True)
        self.checkUpdateWindow.setFixedSize(200, 100)
        self.checkUpdateLabel = QLabel("别按了，检查更新还没做呢！", self.checkUpdateWindow)
        self.checkUpdateLabel.setFixedSize(self.checkUpdateWindow.width(),
                                           int(self.checkUpdateWindow.height() / 2))
        self.checkUpdateButton.clicked.connect(self.checkUpdate)

        # 逻辑线程
        self.idvToolLogicThread = idvToolLogic(self)
        self.idvToolLogicThread.sig.connect(self.signalProcessing)
        self.idvToolLogicThread.start()

        self.settingsLogicThread = settingsLogic(self)
        self.settingsLogicThread.sig.connect(self.signalProcessing)
        self.settingsLogicThread.start()

    class QTextBrowserHandler(logging.Handler):
        def __init__(self, text_browser):
            super().__init__()
            self.text_browser = text_browser

        def emit(self, record):
            msg = self.format(record)
            self.text_browser.append(msg)

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
        self.idvToolLogicThread.exit()
        self.settingsLogicThread.exit()
        self.logger.info("窗口正在关闭")

        reply = QMessageBox.question(self, 'idv-tool', '是否确定退出？', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

        # event.accept()


class test(QThread):
    sig = Signal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        pass


class settingsLogic(QThread):
    sig = Signal(str)

    def __init__(self, w):
        super().__init__()
        self.w = w

    def run(self):
        while True:
            time.sleep(3)
            configData = [
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
            with open("../config.json", "w", encoding="utf8") as config:
                json.dump(configData, config, ensure_ascii=False, indent=4)


class idvToolLogic(QThread):
    sig = Signal(str)

    def __init__(self, w):
        super().__init__()
        self.w = w

    def run(self, ):
        time.sleep(1)
        logger = self.w.logger
        dwrgName = getDwrg()
        if dwrgName is None:
            logger.info("当前文件夹未找到第五人格， 请将程序放置在第五人格根目录后再运行...")
            return
        elif dwrgName is False:
            logger.info("识别到多个 第五人格 主程序...")
            return
        else:
            logger.info(f"成功找到第五人格，路径：{os.path.join(programDir, dwrgName)}")

        idvLoginName = getIdvLogin()
        if idvLoginName is None:
            logger.info("未在当前目录找到 idv-login 正在尝试下载...")
            logger.info("下载...(开发中)")
            return
        elif idvLoginName is False:
            logger.info("识别到当前目录有多个 idv-login")
            logger.info("操作...(开发中)")
        else:
            logger.info(f"成功找到 idv-login，路径：{os.path.join(programDir, idvLoginName)}")
        subprocess.run(f"start {str(os.path.join(programDir, idvLoginName))}", shell=True)
        logger.info("正在等待 idv-login 完全启动")

        while not is_port_in_use(443):
            time.sleep(1)
        logger.info("idv-login 已完全启动！正在唤醒第五人格！\n")
        subprocess.run(f"start {str(os.path.join(programDir, dwrgName))}", shell=True)

        for timing in range(10):
            if is_process_running(dwrgName):
                logger.info("第五人格已启动！\n")
                break
            elif timing == 9:
                logger.info("第五人格启动超时，程序已退出！")
                os.system("pause")
                sys.exit()
            time.sleep(1)

        if self.w.timerEnable.isChecked() is True:
            self.timer(self, dwrgName, idvLoginName).run()

    class timer:
        def __init__(self, w, dwrgName, idvLoginName):
            self.w = w
            self.dwrgName = dwrgName
            self.idvLoginName = idvLoginName

        def run(self):
            logger = self.w.logger
            playtime = ""
            try:
                if self.w.timerEnable.isChecked() is True:
                    logger.info("自动退出模块（待实现）")
                os.system("cls")
                startTime = datetime.now()
                while is_process_running(self.dwrgName):
                    time.sleep(1)
                    logger.info("\033[0;0H第五人格运行中...")
                    playtime = getRunningTime(startTime)
                    logger.info(f"已运行 {playtime}   ")
                if self.w.savePlaytimeEnable.checked() is True:
                    savePlaytime(playtime, startTime)
                    logger.info("游玩时间已保存！")

                if is_process_running(self.idvLoginName):
                    os.system(f"taskkill /im {self.idvLoginName} /f")
                    logger.info("登录工具已关闭已关闭...")
                logger.info("程序即将关闭...")
                time.sleep(1)
                sys.exit(-1)
            except KeyboardInterrupt:
                logger.info("检测到强制退出！游玩时间将不会保存！")
                sys.exit(-1)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
