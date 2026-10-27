'''
file: ui.py
description: 文件占用查询工具图形用户界面
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
'''

import os
import threading
import psutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from utils import getLockingProcesses, isUserAdmin, runAsAdmin
from tkinterdnd2 import DND_FILES
from buildtime import buildTime

class FileUnlockerApp:
    def __init__(self, root, initialPath=None, compiledObj=None):
        self.root = root
        self.compiledObj = compiledObj
        info = f' by IYATT-yx {buildTime}'
        self.root.title(f"文件占用查询与解除工具{info}")
        
        if isUserAdmin():
            self.root.title(f"文件占用查询与解除工具 (管理员模式){info}")

        self.root.geometry("720x520")
        self.root.minsize(640, 420)

        style = ttk.Style()
        style.theme_use("clam")

        self.setupUi()

        if initialPath:
            self.pathVar.set(os.path.normpath(initialPath))
            self.startCheck()

    def setupUi(self):
        # 1. 顶部文件选择框区域
        frameInput = ttk.LabelFrame(self.root, text=" 选择或拖拽文件 ", padding=10)
        frameInput.pack(fill="x", padx=10, pady=10)

        self.pathVar = tk.StringVar()
        self.entryPath = ttk.Entry(frameInput, textvariable=self.pathVar, font=("Segoe UI", 9))
        self.entryPath.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btnBrowse = ttk.Button(frameInput, text="浏览...", command=self.browseFile)
        btnBrowse.pack(side="left", padx=2)

        btnSearch = ttk.Button(frameInput, text="🔍 查询", command=self.startCheck)
        btnSearch.pack(side="left", padx=2)

        self.entryPath.drop_target_register(DND_FILES)
        self.entryPath.dnd_bind('<<Drop>>', self.onDrop)
        lblTip = ttk.Label(self.root, text="💡 提示：可以直接把文件拖入上方输入框中", foreground="gray")
        lblTip.pack(anchor="w", padx=12, pady=(0, 2))

        # 2. 占用进程列表区域
        frameList = ttk.LabelFrame(self.root, text=" 占用此文件的进程列表 ", padding=10)
        frameList.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("pid", "name", "path")
        self.tree = ttk.Treeview(frameList, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("pid", text="PID", anchor="center")
        self.tree.heading("name", text="进程名称", anchor="w")
        self.tree.heading("path", text="程序路径", anchor="w")

        self.tree.column("pid", width=80, stretch=False, anchor="center")
        self.tree.column("name", width=150, stretch=False)
        self.tree.column("path", width=350, stretch=True)

        scrollbarY = ttk.Scrollbar(frameList, orient="vertical", command=self.tree.yview)
        scrollbarX = ttk.Scrollbar(frameList, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbarY.set, xscrollcommand=scrollbarX.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbarY.pack(side="right", fill="y")

        # 3. 底部状态与操作按钮
        frameBottom = ttk.Frame(self.root, padding=10)
        frameBottom.pack(fill="x")

        statusText = "就绪"
        if not isUserAdmin():
            statusText += " (普通权限)"
        self.lblStatus = ttk.Label(frameBottom, text=statusText, anchor="w")
        self.lblStatus.pack(side="left", fill="x", expand=True)

        self.btnUnlock = ttk.Button(frameBottom, text="⚡ 解除选中占用", command=self.unlockSelected, state="disabled")
        self.btnUnlock.pack(side="right", padx=5)

    def browseFile(self):
        fileSelected = filedialog.askopenfilename()
        if fileSelected:
            self.pathVar.set(os.path.normpath(fileSelected))
            self.startCheck()

    def onDrop(self, event):
        path = event.data.strip()
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        self.pathVar.set(os.path.normpath(path))
        self.startCheck()

    def startCheck(self):
        targetPath = self.pathVar.get().strip().strip('"')
        if not targetPath:
            messagebox.showwarning("警告", "请先选择或输入要查询的文件路径！")
            return
        
        if not os.path.exists(targetPath):
            messagebox.showerror("错误", f"找不到指定的文件或路径：\n{targetPath}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.lblStatus.config(text="正在通过系统内核快速扫描...")
        self.btnUnlock.config(state="disabled")

        threading.Thread(target=self.scanProcess, args=(targetPath,), daemon=True).start()

    def scanProcess(self, targetPath):
        foundProcs = getLockingProcesses(targetPath)
        self.root.after(0, self.updateTree, foundProcs)

    def updateTree(self, foundProcs):
        if not foundProcs:
            self.lblStatus.config(text="✅ 该文件当前未被任何进程占用！")
            self.btnUnlock.config(state="disabled")
            return

        for p in foundProcs:
            self.tree.insert("", "end", values=(p['pid'], p['name'], p['exe']))

        count = len(foundProcs)
        self.lblStatus.config(text=f"⚠️ 发现 {count} 个正在占用该文件的进程。")
        self.btnUnlock.config(state="normal")

    def unlockSelected(self):
        selectedItems = self.tree.selection()
        if not selectedItems:
            messagebox.showwarning("提示", "请先在列表中选中要解除占用的进程！")
            return

        confirm = messagebox.askyesno(
            "强行结束进程确认", 
            f"确定要强行终止选中的 {len(selectedItems)} 个进程吗？\n"
            "⚠️ 警告：强行结束未保存数据的进程可能导致数据丢失！"
        )
        if not confirm:
            return

        successCount = 0
        failCount = 0
        permissionDenied = False

        for item in selectedItems:
            values = self.tree.item(item, "values")
            pid = int(values[0])
            name = values[1]

            try:
                proc = psutil.Process(pid)
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired:
                    proc.kill()

                self.tree.delete(item)
                successCount += 1
            except psutil.NoSuchProcess:
                self.tree.delete(item)
                successCount += 1
            except psutil.AccessDenied:
                failCount += 1
                permissionDenied = True
            except Exception as e:
                failCount += 1
                messagebox.showerror("错误", f"终止进程 {name} (PID: {pid}) 失败：{str(e)}")

        self.lblStatus.config(text=f"操作完成：成功结束 {successCount} 个进程，失败 {failCount} 个。")

        if permissionDenied:
            if not isUserAdmin():
                runAsAdmin(self.compiledObj)

        if not self.tree.get_children():
            self.btnUnlock.config(state="disabled")