# -*- coding: utf-8 -*-
# @Time : 2024/8/25 21:58
# @Author : DecadeX

import os
import subprocess
import time

from PySide6.QtCore import QThread, Signal

from Module import getDwrg, is_port_in_use, programDir


class idvToolLogic(QThread):
    sig = Signal(str)

    def __init__(self, w):
        super().__init__()
        self.w = w

    def run(self):
        try:
            time.sleep(1)
            logger = self.w.logger
            dwrgName = getDwrg()
            logger.info(f"已将第五人格所在目录设置为 -> {self.w.workingDirectory}")
            logger.info(f"成功找到第五人格，路径：{os.path.join(self.w.workingDirectory, dwrgName)}")

            if self.w.idvLoginName is None:
                logger.info("未在当前目录找到 idv-login 正在尝试下载...")
                logger.info("下载...(开发中)")
                return
            elif self.w.idvLoginName is False:
                logger.info("识别到当前目录有多个 idv-login")
                logger.info("操作...(开发中)")
            else:
                logger.info(f"成功找到 idv-login，路径：{os.path.join(self.w.workingDirectory, self.w.idvLoginName)}")
            try:
                logger.info("正在等待 idv-login 完全启动")
                subprocess.run(f"start {os.path.join(programDir, self.w.idvLoginName)}", shell=True, timeout=3)
            except subprocess.TimeoutExpired:
                logger.info("idv-login 启动失败启动失败")
                subprocess.run(f"taskkill /im {self.w.idvLoginName} /f", shell=True)
                return 0

            while not is_port_in_use(self.w.idvLoginName, 443):
                time.sleep(1)
            logger.info("idv-login 已完全启动！正在唤醒第五人格！")
            try:
                subprocess.run(f"start {os.path.join(self.w.workingDirectory, dwrgName)}",
                               shell=True, cwd=self.w.workingDirectory, timeout=3)
            except subprocess.TimeoutExpired:
                logger.info("第五人格 启动失败启动失败")
                return 0

            self.w.checkIsGameLoginThread.start()
            # self.w.idvToolLogicThread.exit()
        except Exception as e:
            print(e)
            open(os.path.join(programDir, "crash.log"), 'w').write(str(e))
