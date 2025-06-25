#!/usr/bin/env python3
import sys
import traceback

print("1. 开始调试...")

try:
    from PySide6.QtWidgets import QApplication
    print("2. PySide6 导入成功")
except Exception as e:
    print(f"PySide6 导入失败: {e}")
    sys.exit(1)

try:
    app = QApplication(sys.argv)
    print("3. QApplication 创建成功")
except Exception as e:
    print(f"QApplication 创建失败: {e}")
    sys.exit(1)

try:
    from cq_editor.main_window import MainWindow
    print("4. MainWindow 导入成功")
except Exception as e:
    print(f"MainWindow 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("5. 开始创建 MainWindow 实例...")
    win = MainWindow()
    print("6. MainWindow 创建成功")
except Exception as e:
    print(f"MainWindow 创建失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("7. 开始显示窗口...")
    win.show()
    print("8. 窗口显示成功")
except Exception as e:
    print(f"窗口显示失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("9. 开始事件循环...")
    app.exec()
except Exception as e:
    print(f"事件循环失败: {e}")
    traceback.print_exc()
    sys.exit(1) 