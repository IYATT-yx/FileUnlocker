'''
file: FileUnlocker.py
description: 文件占用查询与解除工具入口程序
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
'''

import os
import sys
from pathlib import Path
from tkinterdnd2 import TkinterDnD

from ui import FileUnlockerApp

if __name__ == "__main__":
    compiledObj = globals().get('__compiled__')
    appDir = os.path.dirname(__file__)

    iconPath = Path(appDir) / 'icon.ico'

    initialPath = sys.argv[1] if len(sys.argv) > 1 else None

    root = TkinterDnD.Tk()

    if iconPath.exists():
        try:
            root.iconbitmap(str(iconPath))
        except Exception:
            pass

    app = FileUnlockerApp(root, initialPath=initialPath, compiledObj=compiledObj)

    root.mainloop()