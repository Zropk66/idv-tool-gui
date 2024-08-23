# -*- coding: utf-8 -*-
# @Time : 2024/8/23 22:16
# @Author : DecadeX

import glob
import json
import os
import socket
import sys
import time
from datetime import datetime

import psutil

programDir = str(os.path.dirname(os.path.abspath(sys.argv[0])))


def find_program(program_name):
    pattern = os.path.join(programDir, program_name)
    idv_login_programs = glob.glob(pattern)
    return [os.path.basename(programs) for programs in idv_login_programs]


def is_process_running(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return True
    return False


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
        except socket.error:
            return True
        return False


def getDwrg():
    allDwrg = find_program('dwrg.exe')
    if allDwrg is None:
        return None
    elif len(allDwrg) == 1:
        return allDwrg[0]
    elif len(allDwrg) > 1:
        return False


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
        s = json.loads(open(os.path.join(programDir, 'config.json'), 'r', encoding='utf8').read())
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        return None

    for i in s:
        for k, v in i.items():
            if v == name:
                return i[elements]
            else:
                break


def savePlaytime(playtime, startTime):
    endTime = datetime.now()
    today_date = time.strftime('%Y-%m-%d', time.localtime())

    fond_write = (f"开始时间: {startTime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"结束时间: {endTime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"游玩时长: {playtime}\n\n")
    no_fond_write = (f"[{today_date}]\n"
                     f"开始时间: {startTime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"结束时间: {endTime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"游玩时长: {playtime}\n\n")

    playtimePath = os.path.join(programDir, "playtime.log")
    if not os.path.exists(playtimePath):
        open(playtimePath, 'w').close()

    found = False
    with open(playtimePath, 'r+', encoding='utf-8') as file:
        allLines = file.readlines()

        for line in reversed(allLines):
            if f"[{today_date}]" in line:
                found = True
                break
        if not found:
            file.write(no_fond_write)
        else:
            file.write(fond_write)
        file.close()


def getRunningTime(startTime):
    current_time = datetime.now()
    time_diff = current_time - startTime

    total_seconds = int(time_diff.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours} 时 {minutes} 分 {seconds} 秒"
