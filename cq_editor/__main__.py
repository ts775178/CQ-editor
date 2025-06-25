# __main__.py负责程序主逻辑
import sys
import argparse

from PySide6.QtWidgets import QApplication

NAME = "CQ-editor"
# 必须先创建一个 QApplication 实例，才能使用窗口控件
app = QApplication(sys.argv, applicationName=NAME)
app.setStyle("Fusion")
from .main_window import MainWindow


def main():
    # 创建一个命令行参数解析器。说明这个程序可以从命令行运行并接收文件名作为参数。
    parser = argparse.ArgumentParser(description=NAME)
    parser.add_argument("filename", nargs="?", default=None)
    # 实际解析命令行参数。app.arguments() 是 PyQt 提供的方式，用来获取启动参数。
    args = parser.parse_args(app.arguments()[1:])
    # 创建主窗口实例，通常是整个 GUI 的核心类，负责布局和用户交互。
    win = MainWindow(filename=args.filename if args.filename else None)
    # 显示窗口（PyQt 中必须调用 .show() 才会把窗口绘制出来）。
    win.show()
    # 运行应用主循环。app.exec() 启动事件循环（GUI必须的），sys.exit 用于安全退出
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
