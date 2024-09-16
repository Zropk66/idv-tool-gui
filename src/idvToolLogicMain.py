# -*- coding: utf-8 -*-
# @Time : 2024/8/25 21:58
# @Author : DecadeX

import os
import subprocess
import time
import traceback

from PySide6.QtCore import QThread, Signal

from Module import getDwrg, is_port_in_use, programDir, is_process_running


class idvToolLogic(QThread):
    sig = Signal(str)
    errorSig = Signal(str)

    def __init__(self, w):
        super().__init__()
        self.w = w

    def run(self):
        try:
            time.sleep(1)
            logger = self.w.logger
            dwrgName = getDwrg()
            logger.info(f"成功找到第五人格 ->：{os.path.join(self.w.workingDirectory, dwrgName)}")

            if self.w.idvLoginName is None:
                logger.info("未在当前目录找到 idv-login 正在尝试下载...")
                logger.info("下载...(开发中)")
                logger.info(
                    "请手动前往 -> [https://wiki.biligame.com/dwrg/PC端免扫码登录工具]\n下载相应版本,放在当前目录下")
                return
            elif self.w.idvLoginName is False:
                logger.info("识别到当前目录有多个 idv-login")
                logger.info("操作...(开发中)")
            else:
                logger.info(f"成功找到 idv-login ->{os.path.join(self.w.workingDirectory, self.w.idvLoginName)}")
            try:
                logger.info("正在等待 idv-login 完全启动")
                subprocess.run(f"start {os.path.join(programDir, self.w.idvLoginName)}", shell=True, timeout=3)
                time.sleep(1)
            except subprocess.TimeoutExpired:
                logger.info("idv-login 启动失败启动失败")
                subprocess.run(f"taskkill /im {self.w.idvLoginName} /f", shell=True)
                return

            while not is_port_in_use(self.w.idvLoginName, 443):
                time.sleep(1)
                if is_process_running(self.w.idvLoginName) is False:
                    self.w.logger.info("idv-login 运行异常")
                    if is_process_running("dwr.exe") is True:
                        subprocess.run(f"taskkill /im dwrg.exe /f", shell=True)
                    self.w.startButton.show()
                    return
            logger.info("idv-login 已完全启动！正在唤醒第五人格！")
            try:
                subprocess.run(f"start {os.path.join(self.w.workingDirectory, dwrgName)}",
                               shell=True, cwd=self.w.workingDirectory, timeout=3)
            except subprocess.TimeoutExpired:
                logger.info("第五人格 启动失败启动失败")
                return

            self.w.checkIsGameLoginThread.start()
        except Exception as e:
            error_message = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            self.errorSig.emit(error_message)
