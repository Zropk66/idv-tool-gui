# -*- coding: utf-8 -*-
# @Time : 2024/8/23 22:16
# @Author : DecadeX

import array
import glob
import json
import os
import sys
import time
from datetime import datetime

import psutil

programDir = str(os.path.dirname(os.path.abspath(sys.argv[0])))


def find_program(program_name):
    if "idv-login" in program_name:
        pattern = os.path.join(os.path.join(programDir), program_name)
    else:
        pattern = os.path.join(loadConfig("working directory", "value"), program_name)
    idv_login_programs = glob.glob(pattern)
    return [os.path.basename(programs) for programs in idv_login_programs]


def is_process_running(process_name):
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cwd', 'exe']):
            if proc.info['name'].lower() == process_name.lower():
                # 获取运行目录
                # print(proc.info['cwd'])
                return True
        return False
    except AttributeError:
        return False


def is_port_in_use(name, port):
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            if proc.info['name'].lower() == name.lower():
                for con in proc.connections():
                    if con.status == 'LISTEN' and con.laddr.port == port and con.laddr.ip == '127.0.0.1':
                        return True
        return False
    except AttributeError:
        return False


def getDwrg():
    return "dwrg.exe"
    # allDwrg = find_program('dwrg.exe')
    # if allDwrg is None:
    #     return None
    # elif len(allDwrg) == 1:
    #     return allDwrg[0]
    # elif len(allDwrg) > 1:
    #     return False


def getIdvLogin():
    allIdvLogin = find_program('idv-login*')
    if allIdvLogin is None:
        return None
    elif len(allIdvLogin) == 1:
        return allIdvLogin[0]
    elif len(allIdvLogin) > 1:
        return False


def loadConfig(name, elements):
    try:
        configs = json.loads(open(os.path.join(programDir, 'config.json'), 'r', encoding='utf8').read())
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        return None

    for i in configs:
        for k, v in i.items():
            if v == name:
                return i[elements]
            else:
                break


def savePlayRecord(recordList: array, startTime, playtime):
    if recordList is not None:
        recordList.append({datetime.now().strftime('%Y-%m-%d'): {
            "Start time": startTime.strftime('%H:%M:%S'),
            "End time": datetime.now().strftime('%H:%M:%S'),
            "Playtime": playtime
        }
        })

        with open(os.path.join(programDir, "play record.json"), "w", encoding="utf8") as config:
            json.dump(recordList, config, ensure_ascii=False, indent=4)


def loadPlayRecord() -> array:
    try:
        recordList = json.loads(open(os.path.join(programDir, 'play record.json'), 'r', encoding='utf8').read())
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        open(os.path.join(programDir, "play record.json"), "w", encoding="utf8").write("")
        return []
    return recordList


def getRunningTime(startTime):
    current_time = datetime.now()
    time_diff = current_time - startTime

    total_seconds = int(time_diff.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours} 时 {minutes} 分 {seconds} 秒"


def checkGameIsLogin():
    logPath = "C:\\ProgramData\\idv-login\\log.txt"

    with open(logPath, 'r', encoding='utf-8') as file:
        log_list = file.readlines()
    log = log_list[-1]

    login_successful = {"('verify_status', '1')",
                        "渠道服登录信息已更新",
                        "请求 https://service.mkey.163.com/mpay/api/data/upload 200 OK"
                        }

    for login_message in login_successful:
        if login_message in log:
            return True
        time.sleep(1)
    return False


if __name__ == '__main__':
    path = "C:\\ProgramData\\idv-login\\"
    print(os.path.isdir(path))
