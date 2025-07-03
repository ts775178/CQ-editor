# 这个文件是可以显示出3D模型的
from OCC.Display.backend import load_backend
load_backend("pyside6")

from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.AIS import AIS_Shape
from PySide6.QtWidgets import QApplication, QMainWindow
import sys

app = QApplication(sys.argv)

win = QMainWindow()
viewer = qtViewer3d(win)
win.setCentralWidget(viewer)
win.resize(800, 600)
win.show()

shape = BRepPrimAPI_MakeBox(10, 20, 30).Shape()
ais = AIS_Shape(shape)
viewer._display.DisplayShape(shape, update=True)
viewer._display.FitAll()

sys.exit(app.exec())