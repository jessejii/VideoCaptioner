"""
PyInstaller 运行时钩子
用于防止 ffmpeg 子进程弹出命令窗口
"""

import os
import sys
import subprocess

# 保存原始的 subprocess.Popen
_original_popen = subprocess.Popen

class NoWindowPopen(subprocess.Popen):
    """自定义 Popen 类，防止子进程弹出窗口"""
    
    def __init__(self, *args, **kwargs):
        # 在 Windows 上设置 CREATE_NO_WINDOW 标志
        if sys.platform == 'win32':
            # 如果没有指定 creationflags，则设置为不创建窗口
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            else:
                kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
        
        super().__init__(*args, **kwargs)

# 替换默认的 Popen
subprocess.Popen = NoWindowPopen

print("ffmpeg_hook: 已应用防弹窗补丁")