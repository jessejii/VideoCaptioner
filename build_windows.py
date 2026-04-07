"""
Windows 打包脚本
使用 PyInstaller 将程序打包成 Windows 可执行文件
"""

import os
import shutil
import subprocess
import sys

def clean_build():
    """清理之前的构建文件"""
    print("清理旧的构建文件...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除 {dir_name}/")

def _resolve_entry_script() -> str:
    """解析可用的入口脚本路径"""
    candidates = [
        'main.py',
        os.path.join('videocaptioner', 'ui', 'main.py'),
        os.path.join('videocaptioner', '__main__.py'),
    ]
    for script in candidates:
        if os.path.exists(script):
            return script
    raise FileNotFoundError(
        f"未找到可用入口脚本，已尝试: {', '.join(candidates)}"
    )


def build_exe():
    """使用 PyInstaller 构建可执行文件"""
    print("\n开始构建 Windows 可执行文件...")
    
    # 创建运行时钩子文件（如果不存在）
    hook_file = 'ffmpeg_hook.py'
    if not os.path.exists(hook_file):
        print(f"创建运行时钩子文件: {hook_file}")
        hook_content = '''"""
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
'''
        with open(hook_file, 'w', encoding='utf-8') as f:
            f.write(hook_content)
    
    entry_script = _resolve_entry_script()
    print(f"[OK] 使用入口脚本: {entry_script}")

    # PyInstaller 命令参数
    cmd = [
        'pyinstaller',
        '--name=VideoCaptioner',            # 程序名称
        '--windowed',                       # 不显示控制台窗口
        '--onedir',                         # 打包成文件夹（推荐，启动更快）
        '--hidden-import=PyQt5',
        '--hidden-import=qfluentwidgets',
        '--hidden-import=openai',
        '--hidden-import=yt_dlp',
        '--hidden-import=modelscope',
        '--hidden-import=pydub',
        '--hidden-import=langdetect',
        '--collect-all=PyQt5',
        '--collect-all=qfluentwidgets',
        '--noconfirm',                      # 不询问确认
        f'--runtime-hook={hook_file}',      # 添加运行时钩子
    ]

    # 按需添加数据目录
    if os.path.exists('resource'):
        cmd.append('--add-data=resource;resource')
    if os.path.exists('app'):
        cmd.append('--add-data=app;app')
    else:
        print("[WARN] 提示: 未找到 app 目录，跳过 --add-data=app;app")
    
    # 添加提示词目录（prompts 下的 .md 文件不是 Python 模块，不会被自动收集）
    prompts_dir = os.path.join('videocaptioner', 'core', 'prompts')
    if os.path.exists(prompts_dir):
        cmd.append(f'--add-data={prompts_dir};videocaptioner/core/prompts')
        print("[OK] 添加提示词目录到打包数据")
    
    # 检查并添加可选的图标
    icon_path = 'resource/icon.ico'
    if os.path.exists(icon_path):
        cmd.insert(4, f'--icon={icon_path}')
        print(f"[OK] 找到图标: {icon_path}")
    else:
        print(f"[WARN] 提示: 未找到图标文件 {icon_path}, 将使用默认图标")

    # 检查并添加 ffmpeg 二进制文件
    ffmpeg_bin_dir = os.path.join('resource', 'bin')
    if os.path.exists(ffmpeg_bin_dir):
        ffmpeg_exe = os.path.join(ffmpeg_bin_dir, 'ffmpeg.exe')
        ffprobe_exe = os.path.join(ffmpeg_bin_dir, 'ffprobe.exe')
        
        if os.path.exists(ffmpeg_exe):
            # 只将 ffmpeg 打包到 resource/bin 目录，避免路径冲突
            cmd.insert(-1, f'--add-binary={ffmpeg_exe};resource/bin')
            print("[OK] 找到 ffmpeg.exe, 将打包到 resource/bin")
            
        if os.path.exists(ffprobe_exe):
            cmd.insert(-1, f'--add-binary={ffprobe_exe};resource/bin')
            print("[OK] 找到 ffprobe.exe, 将打包到 resource/bin")
    else:
        print(f"[WARN] 提示: 未找到 {ffmpeg_bin_dir} 目录，将跳过内建 ffmpeg 打包")
    
    try:
        cmd.append(entry_script)
        print("PyInstaller 命令:")
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)
        print("\n[OK] 构建成功！")
        print(f"可执行文件位置: dist/VideoCaptioner/VideoCaptioner.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] 构建失败: {e}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("VideoCaptioner Windows 打包工具")
    print("=" * 50)
    
    # 检查是否安装了 PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n错误: 未安装 PyInstaller")
        print("请运行: pip install pyinstaller")
        sys.exit(1)
    
    clean_build()
    build_exe()
    
    print("\n" + "=" * 50)
    print("打包完成！")
    print("=" * 50)

if __name__ == '__main__':
    main()
