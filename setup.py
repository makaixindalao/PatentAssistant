import sys
import os
from cx_Freeze import setup, Executable

# ---------- 资源路径处理 ----------
def find_qt_plugins():
    """自动查找Qt插件路径"""
    try:
        from PyQt5.QtCore import QLibraryInfo
        return QLibraryInfo.location(QLibraryInfo.PluginsPath)
    except Exception as e:
        print(f"Qt插件路径查找失败: {str(e)}")
        return ""

# ---------- 配置参数 ----------
include_files = [
    ("config.json", "config.json"),
]

# 包含Qt插件
qt_plugin_path = find_qt_plugins()
if qt_plugin_path:
    include_files.append((os.path.join(qt_plugin_path, "platforms"), "platforms"))

# 排除不必要的包
excludes = ["tkinter", "unittest", "email", "xml", "pydoc"]

# 需要显式包含的模块
includes = ["PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets"]

# 编译选项
build_options = {
    "packages": ["openai", "logging.handlers"],
    "excludes": excludes,
    "includes": includes,
    "include_files": include_files,
    "optimize": 1
}

# ---------- 可执行文件配置 ----------
base = "Win32GUI" if sys.platform == "win32" else None

executable = Executable(
    script="main.py",
    base=base,
    icon="app_icon.ico",
    target_name="PatentAssistant.exe"
)

# ---------- 元数据 ----------
setup(
    name="PatentAssistant",
    version="1.0.0",
    description="专利文档生成工具",
    options={"build_exe": build_options},
    executables=[executable]
)
