'''
file: utils.py
description: 系统权限管理与文件占用查询核心逻辑
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
'''

import os
import sys
import ctypes
from ctypes import wintypes
import psutil
from tkinter import messagebox
from constants import RM_PROCESS_INFO

try:
    rstrtmgr = ctypes.windll.rstrtmgr
except Exception:
    rstrtmgr = None


def getLockingProcesses(filePath):
    """使用 Windows Restart Manager API 获取占用指定文件的进程信息列表"""
    if not rstrtmgr:
        return []

    absPath = os.path.abspath(filePath)
    handle = wintypes.DWORD(0)
    sessionKey = (ctypes.c_wchar * 32)()

    if rstrtmgr.RmStartSession(ctypes.byref(handle), 0, sessionKey) != 0:
        return []

    try:
        fileNames = (ctypes.c_wchar_p * 1)(absPath)
        if rstrtmgr.RmRegisterResources(handle, 1, fileNames, 0, None, 0, None) != 0:
            return []

        nProcNeeded = wintypes.DWORD(0)
        nProcInfo = wintypes.DWORD(0)
        rebootReasons = wintypes.DWORD(0)

        res = rstrtmgr.RmGetList(handle, ctypes.byref(nProcNeeded), ctypes.byref(nProcInfo), None, ctypes.byref(rebootReasons))
        
        if res == 234:
            nProcInfo = nProcNeeded
            procInfoArray = (RM_PROCESS_INFO * nProcInfo.value)()
            
            res = rstrtmgr.RmGetList(handle, ctypes.byref(nProcNeeded), ctypes.byref(nProcInfo), procInfoArray, ctypes.byref(rebootReasons))
            
            if res == 0:
                foundProcs = []
                seenPids = set()
                for i in range(nProcInfo.value):
                    pid = procInfoArray[i].Process.dwProcessId
                    if pid in seenPids:
                        continue
                    seenPids.add(pid)

                    appName = procInfoArray[i].strAppName or "未知进程"
                    exePath = "无法访问路径"
                    try:
                        p = psutil.Process(pid)
                        exePath = p.exe() or "系统服务/内部进程"
                        if not appName or appName == "未知进程":
                            appName = p.name()
                    except Exception:
                        pass

                    foundProcs.append({
                        "pid": pid,
                        "name": appName,
                        "exe": exePath
                    })
                return foundProcs
        elif res == 0:
            return []
    finally:
        rstrtmgr.RmEndSession(handle)

    return []


def isUserAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def runAsAdmin(compiledObj=None):
    if isUserAdmin():
        return True
    
    confirm = messagebox.askyesno(
        "权限不足",
        "该操作需要管理员权限。\n是否立即以管理员身份重新运行本程序？"
    )
    if confirm:
        try:
            if compiledObj is not None:
                executable = compiledObj.original_argv0
                arguments = ""
            else:
                executable = sys.executable
                arguments = f'"{os.path.abspath(sys.argv[0])}"'
                if len(sys.argv) > 1:
                    arguments += " " + " ".join([f'"{a}"' for a in sys.argv[1:]])
            
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", executable, arguments, None, 1
            )
            if ret > 32:
                sys.exit(0)
            else:
                messagebox.showerror("错误", "请求管理员权限失败！")
        except Exception as e:
            messagebox.showerror("错误", f"无法以管理员权限启动: {e}")
    return False