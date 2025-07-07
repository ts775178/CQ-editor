# 3D视图组件
from sys import platform


from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Slot, Signal, Qt, QEvent
from objc import lookUpClass
# import OCC

from OCC.Core.Aspect import Aspect_DisplayConnection, Aspect_TypeOfTriedronPosition
# from OCC.Core.OpenGl import OpenGl_GraphicDriver
from OCC.Core.V3d import V3d_Viewer
from OCC.Core.AIS import AIS_InteractiveContext, AIS_DisplayMode
from OCC.Core.Quantity import Quantity_Color

from OCC.Display.backend import load_backend
load_backend("pyside6")
from OCC.Display.qtDisplay import qtViewer3d

class MyViewer(qtViewer3d):
    sigObjectSelected = Signal(list)

    def __init__(self):
        super().__init__()

    def simulate_selection(self):
        # 手动调用时触发选择信号（你可以在 moveTo/select 等操作后调用）
        selected = []  # 假设你用 InteractiveContext 获取到了选中的 shape
        self.sigObjectSelected.emit(selected)



"""ZOOM_STEP = 0.9


class OCCTWidget(QWidget):

    sigObjectSelected = Signal(list)

    def __init__(self, parent=None):

        super(OCCTWidget, self).__init__(parent)

        self.setAttribute(Qt.WA_NativeWindow)
        self.setAttribute(Qt.WA_PaintOnScreen)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self._initialized = False
        self._needs_update = False

        # OCCT secific things
        self.display_connection = Aspect_DisplayConnection()
        self.graphics_driver = OpenGl_GraphicDriver(self.display_connection)

        self.viewer = V3d_Viewer(self.graphics_driver)
        self.view = self.viewer.CreateView()
        self.context = AIS_InteractiveContext(self.viewer)

        # Trihedorn, lights, etc
        self.prepare_display()
        # 下面这行代码在终端报错
        self._initialize()

    def prepare_display(self):

        view = self.view

        params = view.ChangeRenderingParams()
        params.NbMsaaSamples = 8
        params.IsAntialiasingEnabled = True

        view.TriedronDisplay(
            Aspect_TypeOfTriedronPosition.Aspect_TOTP_RIGHT_LOWER, Quantity_Color(), 0.1
        )

        viewer = self.viewer

        viewer.SetDefaultLights()
        viewer.SetLightOn()

        ctx = self.context

        ctx.SetDisplayMode(AIS_DisplayMode.AIS_Shaded, True)
        ctx.DefaultDrawer().SetFaceBoundaryDraw(True)

    def wheelEvent(self, event):

        delta = event.angleDelta().y()
        factor = ZOOM_STEP if delta < 0 else 1 / ZOOM_STEP

        self.view.SetZoom(factor)

    def mousePressEvent(self, event):
        if not self._initialized:
            return
        pos = event.pos()

        if event.button() == Qt.LeftButton:
            # Used to prevent drag selection of objects
            self.pending_select = True
            self.left_press = pos

            self.view.StartRotation(pos.x(), pos.y())
        elif event.button() == Qt.RightButton:
            self.view.StartZoomAtPoint(pos.x(), pos.y())

        self.old_pos = pos

    def mouseMoveEvent(self, event):

        pos = event.pos()
        x, y = pos.x(), pos.y()

        if event.buttons() == Qt.LeftButton:
            self.view.Rotation(x, y)

            # If the user moves the mouse at all, the selection will not happen
            if abs(x - self.left_press.x()) > 2 or abs(y - self.left_press.y()) > 2:
                self.pending_select = False

        elif event.buttons() == Qt.MiddleButton:
            self.view.Pan(x - self.old_pos.x(), self.old_pos.y() - y, theToStart=True)

        elif event.buttons() == Qt.RightButton:
            self.view.ZoomAtPoint(self.old_pos.x(), y, x, self.old_pos.y())

        self.old_pos = pos

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:
            pos = event.pos()
            x, y = pos.x(), pos.y()

            # Only make the selection if the user has not moved the mouse
            if self.pending_select:
                self.context.MoveTo(x, y, self.view, True)
                self._handle_selection()

    def _handle_selection(self):

        self.context.Select(True)
        self.context.InitSelected()

        selected = []
        if self.context.HasSelectedShape():
            selected.append(self.context.SelectedShape())

        self.sigObjectSelected.emit(selected)

    def paintEngine(self):

        return None

    def paintEvent(self, event):

        if not self._initialized:
            self._initialize()
        else:
            self.view.Redraw()

    def showEvent(self, event):

        super(OCCTWidget, self).showEvent(event)

    def resizeEvent(self, event):

        super(OCCTWidget, self).resizeEvent(event)

        self.view.MustBeResized()

    def _initialize(self):

        wins = {
            "darwin": self._get_window_osx,
            "linux": self._get_window_linux,
            "win32": self._get_window_win,
        }
        # 终端显示下面这句有问题
        self.view.SetWindow(wins.get(platform, self._get_window_linux)(self.winId()))

        self._initialized = True

    def _get_window_win(self, wid):

        from OCC.Core.WNT import WNT_Window

        #return WNT_Window(wid.ascapsule())
        return WNT_Window(wid)

    def _get_window_linux(self, wid):

        from OCC.Core.Xw import Xw_Window

        return Xw_Window(self.display_connection, int(wid))

    
    # 这个函数在macOS上无法正常工作，需要使用其他方法，先暂时使用下面那种方法替代，使窗口独立显示
    def _get_window_osx(self, wid):
        
        # from objc import objc_object
        from OCC.Core.Cocoa import Cocoa_Window

        # return Cocoa_Window(int(wid))  # 直接传整型窗口ID
        return Cocoa_Window("OCCTWidget", 100, 100, 800, 600)  # 临时使用独立窗口显示"""
        
def create_occt_viewer():
    return MyViewer()

