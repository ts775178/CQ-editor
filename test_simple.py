#!/usr/bin/env python3
import sys
import os

# 设置环境变量
os.environ["PYTHONASYNCIODEBUG"] = "0"
os.environ["IPYTHONDIR"] = ""
os.environ["JUPYTER_CONFIG_DIR"] = ""
os.environ["JUPYTER_DATA_DIR"] = ""

# 配置日志
import logging
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

for logger_name in ['ipykernel', 'jupyter_client', 'qtconsole', 'asyncio', 'tornado', 'zmq', 'OCC', 'VTK']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

from PySide6.QtWidgets import QApplication
from cq_editor.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    win = MainWindow()
    win.show()
    
    # 测试简单的CadQuery代码
    editor = win.components["editor"]
    editor.set_text('''import cadquery as cq
result = cq.Workplane("XY").box(10, 10, 5)
show_object(result)''')
    
    # 运行代码
    debugger = win.components["debugger"]
    debugger._actions["Run"][0].triggered.emit()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 