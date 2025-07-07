from OCC.Display.backend import load_backend
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from OCC.Core.Graphic3d import (
    Graphic3d_MaterialAspect,
    Graphic3d_NameOfMaterial,
    Graphic3d_Camera,
    Graphic3d_StereoMode,
)
from OCC.Core.Quantity import Quantity_Color
from OCC.Core.Quantity import Quantity_NOC_BLACK, Quantity_TOC_RGB
from OCC.Core.Aspect import Aspect_GDM_Lines, Aspect_GT_Rectangular
from OCC.Core.AIS import AIS_Shaded, AIS_WireFrame, AIS_ColoredShape, AIS_Axis, AIS_InteractiveObject, AIS_Shape
from OCC.Core.Geom import Geom_Axis1Placement
from OCC.Core.gp import gp_Ax3, gp_Dir, gp_Pnt, gp_Ax1
from ..cq_utils import to_occ_color, make_AIS
from ..utils import layout, get_save_filename
from ..icons import icon
load_backend("pyside6")
from OCC.Display.qtDisplay import qtViewer3d
from ..mixins import ComponentMixin
from PySide6.QtCore import Slot, Signal
from PySide6.QtWidgets import QTreeWidgetItem
from pyqtgraph.parametertree import Parameter
from PySide6.QtGui import QAction
import qtawesome as qta


BLACK = Quantity_NOC_BLACK
DEFAULT_EDGE_COLOR = Quantity_Color(BLACK)
DEFAULT_EDGE_WIDTH = 2
DEFAULT_FACE_COLOR = (0.5, 0.5, 0.5)

class OCCViewer(qtViewer3d, ComponentMixin):
    name = "3D Viewer"

    preferences = Parameter.create(
        name="Pref",
        children=[
            {"name": "Fit automatically", "type": "bool", "value": True},
            {"name": "Use gradient", "type": "bool", "value": False},
            {"name": "Background color", "type": "color", "value": (95, 95, 95)},
            {"name": "Background color (aux)", "type": "color", "value": (30, 30, 30)},
            {
                "name": "Deviation",
                "type": "float",
                "value": 1e-5,
                "dec": True,
                "step": 1,
            },
            {
                "name": "Angular deviation",
                "type": "float",
                "value": 0.1,
                "dec": True,
                "step": 1,
            },
            {
                "name": "Projection Type",
                "type": "list",
                "value": "Orthographic",
                "values": [
                    "Orthographic",
                    "Perspective",
                    "Stereo",
                    "MonoLeftEye",
                    "MonoRightEye",
                ],
            },
            {
                "name": "Stereo Mode",
                "type": "list",
                "value": "QuadBuffer",
                "values": [
                    "QuadBuffer",
                    "Anaglyph",
                    "RowInterlaced",
                    "ColumnInterlaced",
                    "ChessBoard",
                    "SideBySide",
                    "OverUnder",
                ],
            },
        ],
    )
    IMAGE_EXTENSIONS = "png"

    sigObjectSelected = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        ComponentMixin.__init__(self)
        # 1. 先设置 canvas，兼容旧逻辑
        self.canvas = self
        # 2. 初始化 OCCT 显示接口（必须在用 context/viewer/view 之前做）
        self.context = self._display.Context
        self.view = self._display.View
        self.viewer = self._display.Viewer
        # 3、创建toolbar  action、布局等
        self.create_actions(self)
        # self.layout_ = layout(self, [self], top_widget=self, margin=0)
        # 4、初始化默认显示参数（必须在context初始化之后）
        self.setup_default_drawer()
        self.updatePreferences()
        self.displayed_shapes = []
        self.displayed_ais = []
        

        # self._display.create_windows()
        
        

    def setup_default_drawer(self):

        # set the default color and material
        # material = Graphic3d_MaterialAspect(Graphic3d_NOM_JADE)

        shading_aspect = self.context.DefaultDrawer().ShadingAspect()
        # shading_aspect.SetMaterial(Graphic3d_NOM_JADE)
        material = Graphic3d_MaterialAspect(Graphic3d_NameOfMaterial.Graphic3d_NOM_JADE)
        shading_aspect.SetMaterial(material)
        #shading_aspect.SetColor(DEFAULT_FACE_COLOR)

        material = Graphic3d_MaterialAspect(Graphic3d_NameOfMaterial.Graphic3d_NOM_JADE)
        shading_aspect.SetMaterial(material)

        # face edge lw
        line_aspect = self.context.DefaultDrawer().FaceBoundaryAspect()
        line_aspect.SetWidth(DEFAULT_EDGE_WIDTH)
        line_aspect.SetColor(DEFAULT_EDGE_COLOR)

    def updatePreferences(self, *args):

        color1 = to_occ_color(self.preferences["Background color"])
        color2 = to_occ_color(self.preferences["Background color (aux)"])

        if not self.preferences["Use gradient"]:
            color2 = color1
        print("[DEBUG] color1:", color1, type(color1))
        print("[DEBUG] color2:", color2, type(color2))
        self.view.SetBgGradientColors(color1, color2)

        self.update()

        ctx = self.context
        ctx.SetDeviationCoefficient(self.preferences["Deviation"])
        ctx.SetDeviationAngle(self.preferences["Angular deviation"])

        v = self._get_view()
        camera = v.Camera()
        projection_type = self.preferences["Projection Type"]
        camera.SetProjectionType(
            getattr(
                Graphic3d_Camera,
                f"Projection_{projection_type}",
                Graphic3d_Camera.Projection_Orthographic,
            )
        )

        # onle relevant for stereo projection
        stereo_mode = self.preferences["Stereo Mode"]
        params = v.ChangeRenderingParams()
        params.StereoMode = getattr(
            Graphic3d_StereoMode,
            f"Graphic3d_StereoMode_{stereo_mode}",
            Graphic3d_StereoMode.Graphic3d_StereoMode_QuadBuffer,
        )
    def create_actions(self, parent):

        self._actions = {
            "View": [
                QAction(
                    qta.icon("fa5s.arrows-alt"),
                    "Fit (Shift+F1)",
                    parent,
                    shortcut="shift+F1",
                    triggered=self.fit,
                ),
                QAction(
                    QIcon(":/images/icons/isometric_view.svg"),
                    "Iso (Shift+F2)",
                    parent,
                    shortcut="shift+F2",
                    triggered=self.iso_view,
                ),
                QAction(
                    QIcon(":/images/icons/top_view.svg"),
                    "Top (Shift+F3)",
                    parent,
                    shortcut="shift+F3",
                    triggered=self.top_view,
                ),
                QAction(
                    QIcon(":/images/icons/bottom_view.svg"),
                    "Bottom (Shift+F4)",
                    parent,
                    shortcut="shift+F4",
                    triggered=self.bottom_view,
                ),
                QAction(
                    QIcon(":/images/icons/front_view.svg"),
                    "Front (Shift+F5)",
                    parent,
                    shortcut="shift+F5",
                    triggered=self.front_view,
                ),
                QAction(
                    QIcon(":/images/icons/back_view.svg"),
                    "Back (Shift+F6)",
                    parent,
                    shortcut="shift+F6",
                    triggered=self.back_view,
                ),
                QAction(
                    QIcon(":/images/icons/left_side_view.svg"),
                    "Left (Shift+F7)",
                    parent,
                    shortcut="shift+F7",
                    triggered=self.left_view,
                ),
                QAction(
                    QIcon(":/images/icons/right_side_view.svg"),
                    "Right (Shift+F8)",
                    parent,
                    shortcut="shift+F8",
                    triggered=self.right_view,
                ),
                QAction(
                    qta.icon("fa5s.square"),
                    "Wireframe (Shift+F9)",
                    parent,
                    shortcut="shift+F9",
                    triggered=self.wireframe_view,
                ),
                QAction(
                    qta.icon("fa5s.square"),
                    "Shaded (Shift+F10)",
                    parent,
                    shortcut="shift+F10",
                    triggered=self.shaded_view,
                ),
            ],
            "Tools": [
                QAction(
                    icon("screenshot"),
                    "Screenshot",
                    parent,
                    triggered=self.save_screenshot,
                )
            ],
        }

    def toolbarActions(self):
        return self._actions["View"]
    
    def clear(self):

        self.displayed_shapes = []
        self.displayed_ais = []
        self.context.EraseAll(True)
        context = self._get_context()
        context.PurgeDisplay()
        context.RemoveAll(True)

    def _display(self, shape):

        ais, _ = make_AIS(shape)
        # self.context.Display(shape, True)
        self.context.Display(ais, True)

        self.displayed_shapes.append(shape)
        self.displayed_ais.append(ais)

        # self.canvas._display.Repaint()

    @Slot(object)
    def display(self, ais):

        context = self._get_context()
        context.Display(ais, True)

        if self.preferences["Fit automatically"]:
            self.fit()

    @Slot(list)
    @Slot(list, bool)
    def display_many(self, ais_list, fit=None):
        print("[DEBUG] Received in display_many:", ais_list)
        print("[DEBUG] ais_list type:", type(ais_list))
        print("[DEBUG] ais_list length:", len(ais_list) if ais_list else 0)
        print("[DEBUG] view object:", self.view)
        print("[DEBUG] view.IsEmpty():", self.view.IsEmpty())
        
        if not ais_list:
            print("[DEBUG] ais_list is empty, nothing to display")
            return
            
        context = self._get_context()
        # 清除旧内容（不立即刷新）
        context.EraseAll(True)
        
        # 显示新对象
        for i, ais in enumerate(ais_list):
            print(f"[DEBUG] Processing ais {i}:", type(ais))
            try:
                if isinstance(ais, AIS_InteractiveObject):
                    print(f"[DEBUG] Displaying AIS_InteractiveObject {i}")
                    context.Display(ais, True)
                else:
                    print(f"[DEBUG] Creating AIS for object {i}")
                    ais_obj, _ = make_AIS(ais)
                    print(f"[DEBUG] Created AIS object {i}:", type(ais_obj))
                    context.Display(ais_obj, True)
            except Exception as e:
                print(f"[DEBUG] Error displaying object {i}:", e)
                import traceback
                traceback.print_exc()
        
        # 强制刷新视图
        self.view.Redraw()
        self.view.Update()
        
        # 自动缩放视图
        if self.preferences["Fit automatically"] and fit is None:
            print("[DEBUG] Auto-fitting view")
            self.fit()
        elif fit:
            print("[DEBUG] Manual fitting view")
            self.fit()
        
        print("[DEBUG] display_many completed")

    @Slot(QTreeWidgetItem, int)
    def update_item(self, item, col):

        ctx = self._get_context()
        if item.checkState(0):
            ctx.Display(item.ais, True)
        else:
            ctx.Erase(item.ais, True)

    @Slot(list)
    def remove_items(self, ais_items):

        ctx = self._get_context()
        for ais in ais_items:
            ctx.Erase(ais, True)

    @Slot()
    def redraw(self):

        self._get_viewer().Redraw()

    def fit(self):
        self.view.FitAll()

    def iso_view(self):

        v = self._get_view()
        v.SetProj(1, -1, 1)
        v.SetTwist(0)

    def bottom_view(self):

        v = self._get_view()
        v.SetProj(0, 0, -1)
        v.SetTwist(0)

    def top_view(self):

        v = self._get_view()
        v.SetProj(0, 0, 1)
        v.SetTwist(0)

    def front_view(self):

        v = self._get_view()
        v.SetProj(0, 1, 0)
        v.SetTwist(0)

    def back_view(self):

        v = self._get_view()
        v.SetProj(0, -1, 0)
        v.SetTwist(0)

    def left_view(self):

        v = self._get_view()
        v.SetProj(-1, 0, 0)
        v.SetTwist(0)

    def right_view(self):

        v = self._get_view()
        v.SetProj(1, 0, 0)
        v.SetTwist(0)

    def shaded_view(self):

        c = self._get_context()
        c.SetDisplayMode(AIS_Shaded, True)

    def wireframe_view(self):

        c = self._get_context()
        c.SetDisplayMode(AIS_WireFrame, True)

    def show_grid(
        self, step=1.0, size=10.0 + 1e-6, color1=(0.7, 0.7, 0.7), color2=(0, 0, 0)
    ):

        viewer = self._get_viewer()
        viewer.ActivateGrid(Aspect_GT_Rectangular, Aspect_GDM_Lines)
        viewer.SetRectangularGridGraphicValues(size, size, 0)
        viewer.SetRectangularGridValues(0, 0, step, step, 0)
        grid = viewer.Grid()
        grid.SetColors(
            Quantity_Color(*color1, Quantity_TOC_RGB), Quantity_Color(*color2, Quantity_TOC_RGB)
        )

    def hide_grid(self):

        viewer = self._get_viewer()
        viewer.DeactivateGrid()

    @Slot(bool, float)
    @Slot(bool)
    def toggle_grid(self, value: bool, dim: float = 10.0):

        if value:
            self.show_grid(step=dim / 20, size=dim + 1e-9)
        else:
            self.hide_grid()

    @Slot(gp_Ax3)
    def set_grid_orientation(self, orientation: gp_Ax3):

        viewer = self._get_viewer()
        viewer.SetPrivilegedPlane(orientation)

    def show_axis(self, origin=(0, 0, 0)):
        direction=[(1,0,0), (0,1,0), (0,0,1)]
        ax_placement = Geom_Axis1Placement(gp_Ax1(gp_Pnt(*origin), gp_Dir(*direction)))
        ax = AIS_Axis(ax_placement)
        self._display_ais(ax)
        '''for dir in directions:
            self._display_ais(AIS_Axis(Geom_Axis1Placement(gp_Ax1(gp_Pnt(*origin), gp_Dir(*dir)))))'''

    def save_screenshot(self):

        fname = get_save_filename(self.IMAGE_EXTENSIONS)
        if fname != "":
            self._get_view().Dump(fname)

    def _display_ais(self, ais):

        self._get_context().Display(ais)

    def _get_view(self):

        return self.view

    def _get_viewer(self):

        return self.viewer

    def _get_context(self):

        return self.context

    @Slot(list)
    def handle_selection(self, obj):

        self.sigObjectSelected.emit(obj)

    @Slot(list)
    def set_selected(self, ais):

        ctx = self._get_context()
        ctx.ClearSelected(False)

        for obj in ais:
            ctx.AddOrRemoveSelected(obj, False)

        self.redraw()

__all__ = ["OCCViewer"]
