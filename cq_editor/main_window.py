# 负责GUI构造和交互界面
import sys

# from PySide6.QtCore import QObject, Signalfrom PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPalette, QColor, QAction
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QToolBar,
    QDockWidget,
    QApplication,
    QMenu,
)
from logbook import Logger
import cadquery as cq

# 导入自定义组件
from .widgets.editor import Editor
from .widgets.viewer import OCCViewer
from .widgets.console import ConsoleWidget
from .widgets.object_tree import ObjectTree
from .widgets.traceback_viewer import TracebackPane
from .widgets.debugger import Debugger, LocalsView
from .widgets.cq_object_inspector import CQObjectInspector
from .widgets.log import LogViewer

from . import __version__
from .utils import (
    dock,
    add_actions,
    open_url,
    about_dialog,
    check_gtihub_for_updates,
    confirm,
)
from .mixins import MainMixin
from .icons import icon
from pyqtgraph.parametertree import Parameter
from .preferences import PreferencesWidget

    # 重定向标准输出到日志窗口
class _PrintRedirectorSingleton(QObject):
    """
    这个类通过monkey-patch方式重定向sys.stdout.write，使其发出信号。
    它被实例化为.main_window.PRINT_REDIRECTOR，不应该再次实例化。
    这样做的目的是
    将标准输出重定向到GUI界面的日志窗口中。
    """

    sigStdoutWrite = Signal(str)  # 定义信号，用于传递标准输出文本

    def __init__(self):
        super().__init__()

        # 保存原始的stdout.write函数
        original_stdout_write = sys.stdout.write

        def new_stdout_write(text: str):
            """重定向stdout.write的新实现
            Args:
                text: 要输出的文本
            Returns:
                调用原始stdout.write的结果
            """
            self.sigStdoutWrite.emit(text)  # 发出信号
            return original_stdout_write(text)  # 调用原始函数

        # 替换sys.stdout.write
        sys.stdout.write = new_stdout_write


# 创建全局单例实例
PRINT_REDIRECTOR = _PrintRedirectorSingleton()


class MainWindow(QMainWindow, MainMixin):
    """主窗口类，继承自QMainWindow和MainMixin
    负责整个应用程序的主界面布局和功能组织
    """

    name = "CQ-Editor"  # 应用程序名称
    org = "CadQuery"    # 组织名称

    # 定义应用程序偏好设置
    preferences = Parameter.create(
        name="Preferences",
        children=[
            {
                "name": "Light/Dark Theme",
                "type": "list",
                "value": "Light",
                "values": [
                    "Light",
                    "Dark",
                ],
            },
        ],
    )

    def __init__(self, parent=None, filename=None):  # 前面没有任何窗体，parent=None
        # 调用父类QMainWindow的构造函数
        super(MainWindow, self).__init__(parent)
        MainMixin.__init__(self)

        # 设置应用程序图标
        self.setWindowIcon(icon("app"))

        # Windows系统下的任务栏图标修复
        if sys.platform == "win32":
            import ctypes
            myappid = "cq-editor"  # 应用程序ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # 中央区域，创建3D视图作为中央窗口
        self.viewer = OCCViewer(self)
        self.setCentralWidget(self.viewer.canvas)

        # 初始化各个组件
        self.prepare_panes()        # 面板注册，注册多个 Dock 面板并设置默认显示位置
        self.registerComponent("viewer", self.viewer)  # 注册视图组件
        self.prepare_toolbar()      # 工具栏添加工具栏并连接各组件的按钮
        self.prepare_menubar()      # 设置菜单（文件、编辑、运行、帮助等）
        self.prepare_statusbar()    # 显示状态信息（如当前编辑文件状态）
        self.prepare_actions()      # 各组件之间的事件反应逻辑
        self.components["object_tree"].addLines()  # 添加对象树
        self.prepare_console()      # 准备控制台
        self.fill_dummy()          # 填充示例内容
        self.setup_logging()       # 设置日志系统

        # 连接偏好设置变化信号
        self.preferences.sigTreeStateChanged.connect(self.preferencesChanged)

        # 恢复窗口和偏好设置
        self.restorePreferences()
        self.restoreWindow()

        # 监听文件修改状态
        self.components["editor"].document().modificationChanged.connect(
            self.update_window_title
        )

        # 如果提供了文件名，则打开该文件
        if filename:
            self.components["editor"].load_from_file(filename)

        # 恢复组件状态
        self.restoreComponentState()

    def preferencesChanged(self, param, changes):
        """处理偏好设置变化
        当用户更改主题设置时，更新整个应用程序的外观
        
        Args:
            param: 发生变化的参数对象
            changes: 变化信息
        """
        # 根据主题设置更新界面
        if self.preferences["Light/Dark Theme"] == "Light":
            # 恢复默认浅色主题
            QApplication.instance().setStyleSheet("")
            QApplication.instance().setPalette(QApplication.style().standardPalette())
            self.components["console"].app_theme_changed("Light")
        elif self.preferences["Light/Dark Theme"] == "Dark":
            # 设置深色主题
            QApplication.instance().setStyle("Fusion")
            
            # 创建深色主题调色板
            white_color = QColor(255, 255, 255)
            black_color = QColor(0, 0, 0)
            red_color = QColor(255, 0, 0)
            palette = QPalette()
            
            # 设置各种界面元素的颜色
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, white_color)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, black_color)
            palette.setColor(QPalette.ToolTipText, white_color)
            palette.setColor(QPalette.Text, white_color)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, white_color)
            palette.setColor(QPalette.BrightText, red_color)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, black_color)
            
            # 应用调色板
            QApplication.instance().setPalette(palette)
            self.components["console"].app_theme_changed("Dark")

        # 调整工具栏颜色
        p = self.toolbar.palette()
        if self.preferences["Light/Dark Theme"] == "Dark":
            p.setColor(QPalette.Background, QColor(120, 120, 120))
            menu_palette = self.menuBar().palette()
            menu_palette.setColor(QPalette.Base, QColor(80, 80, 80))
            for menu in self.menuBar().findChildren(QMenu):
                menu.setPalette(menu_palette)
        else:
            p.setColor(QPalette.Background, QColor(240, 240, 240))
            menu_palette = self.menuBar().palette()
            menu_palette.setColor(QPalette.Base, QColor(240, 240, 240))
            for menu in self.menuBar().findChildren(QMenu):
                menu.setPalette(menu_palette)
        self.toolbar.setPalette(p)

    def closeEvent(self, event):
        """处理窗口关闭事件
        在关闭窗口前保存状态，并检查是否有未保存的更改
        
        Args:
            event: 关闭事件对象
        """
        # 保存窗口状态和偏好设置
        self.saveWindow()
        self.savePreferences()
        self.saveComponentState()

        # 检查是否有未保存的更改
        if self.components["editor"].document().isModified():
            rv = confirm(self, "Confirm close", "Close without saving?")
            if rv:
                event.accept()
                super(MainWindow, self).closeEvent(event)
            else:
                event.ignore()
        else:
            super(MainWindow, self).closeEvent(event)

    # 准备和初始化所有面板组件
    def prepare_panes(self):
        # 注册编辑器组件
        self.registerComponent(
            "editor",
            Editor(self),
            lambda c: dock(c, "Editor", self, defaultArea="left"),
        )

        # 注册对象树组件
        self.registerComponent(
            "object_tree",
            ObjectTree(self),
            lambda c: dock(c, "Objects", self, defaultArea="right"),
        )

        # 注册错误追踪面板
        self.registerComponent(
            "traceback_viewer",
            TracebackPane(self),
            lambda c: dock(c, "Current traceback", self, defaultArea="bottom"),
        )

        # 注册调试器
        self.registerComponent("debugger", Debugger(self))

        # 注册控制台
        self.registerComponent(
            "console",
            ConsoleWidget(self),
            # 调用dock函数将这个组件添加到主窗口的底部区域，设置停靠窗口的标题为console
            lambda c: dock(c, "Console", self, defaultArea="bottom"),
        )

        # 注册变量查看器
        self.registerComponent(
            "variables_viewer",
            LocalsView(self),
            lambda c: dock(c, "Variables", self, defaultArea="right"),
        )

        # 注册CQ对象检查器
        self.registerComponent(
            "cq_object_inspector",
            CQObjectInspector(self),
            lambda c: dock(c, "CQ object inspector", self, defaultArea="right"),
        )

        # 注册日志查看器
        self.registerComponent(
            "log",
            LogViewer(self),
            lambda c: dock(c, "Log viewer", self, defaultArea="bottom"),
        )

        # 显示所有面板
        for d in self.docks.values():
            d.show()

        # 连接标准输出重定向
        PRINT_REDIRECTOR.sigStdoutWrite.connect(
            lambda text: self.components["log"].append_log(text)
        )

    def prepare_menubar(self):
        """准备菜单栏
        创建并组织所有菜单项
        """
        menu = self.menuBar()
        # 创建主要菜单，app顶部那些菜单
        menu_file = menu.addMenu("&File")
        menu_edit = menu.addMenu("&Edit")
        menu_tools = menu.addMenu("&Tools")
        menu_run = menu.addMenu("&Run")
        menu_view = menu.addMenu("&View")
        menu_help = menu.addMenu("&Help")

        # 组织菜单结构
        menus = {
            "File": menu_file,
            "Edit": menu_edit,
            "Run": menu_run,
            "Tools": menu_tools,
            "View": menu_view,
            "Help": menu_help,
        }

        # 为每个组件添加菜单项
        for comp in self.components.values():
            self.prepare_menubar_component(menus, comp.menuActions())

        # 添加视图菜单项
        menu_view.addSeparator()
        for d in self.findChildren(QDockWidget):
            menu_view.addAction(d.toggleViewAction())

        menu_view.addSeparator()
        for t in self.findChildren(QToolBar):
            menu_view.addAction(t.toggleViewAction())

        # 添加编辑菜单项
        menu_edit.addAction(
            QAction(
                icon("toggle-comment"),
                "Toggle Comment",
                self,
                shortcut="ctrl+/",
                triggered=self.components["editor"].toggle_comment,
            )
        )
        menu_edit.addAction(
            QAction(
                icon("preferences"),
                "Preferences",
                self,
                triggered=self.edit_preferences,
            )
        )

        # 添加帮助菜单项
        menu_help.addAction(
            QAction(icon("help"), "Documentation", self, triggered=self.documentation)
        )
        menu_help.addAction(
            QAction("CQ documentation", self, triggered=self.cq_documentation)
        )
        menu_help.addAction(QAction(icon("about"), "About", self, triggered=self.about))
        menu_help.addAction(
            QAction(
                "Check for CadQuery updates", self, triggered=self.check_for_cq_updates
            )
        )

    def prepare_menubar_component(self, menus, comp_menu_dict):
        """为组件准备菜单项
            menus: 菜单字典
            comp_menu_dict: 组件菜单字典
        """
        for name, action in comp_menu_dict.items():
            menus[name].addActions(action)

    def prepare_toolbar(self):
        """准备工具栏
        创建并组织工具栏按钮
        """
        self.toolbar = QToolBar("Main toolbar", self, objectName="Main toolbar")

        # 添加组件工具栏动作
        for c in self.components.values():
            add_actions(self.toolbar, c.toolbarActions())

        self.addToolBar(self.toolbar)

    def prepare_statusbar(self):
        """准备状态栏
        创建状态栏标签
        """
        self.status_label = QLabel("", parent=self)
        self.statusBar().insertPermanentWidget(0, self.status_label)

    def prepare_actions(self):
        """准备所有动作和信号连接
        建立组件之间的通信
        """
        # 连接调试器信号
        self.components["debugger"].sigRendered.connect(
            self.components["object_tree"].addObjects
        )
        self.components["debugger"].sigTraceback.connect(
            self.components["traceback_viewer"].addTraceback
        )
        self.components["debugger"].sigLocals.connect(
            self.components["variables_viewer"].update_frame
        )
        self.components["debugger"].sigLocals.connect(
            self.components["console"].push_vars
        )

        # 连接对象树信号
        self.components["object_tree"].sigObjectsAdded.connect(
            lambda *args: self.components["viewer"].display_many(*args)
        )
        '''self.components["object_tree"].sigObjectsAdded[list, bool].connect(
            self.components["viewer"].display_many
        )'''
        self.components["object_tree"].sigItemChanged.connect(
            self.components["viewer"].update_item
        )
        self.components["object_tree"].sigObjectsRemoved.connect(
            self.components["viewer"].remove_items
        )
        self.components["object_tree"].sigCQObjectSelected.connect(
            self.components["cq_object_inspector"].setObject
        )
        self.components["object_tree"].sigObjectPropertiesChanged.connect(
            self.components["viewer"].redraw
        )
        self.components["object_tree"].sigAISObjectsSelected.connect(
            self.components["viewer"].set_selected
        )

        # 连接视图信号
        self.components["viewer"].sigObjectSelected.connect(
            self.components["object_tree"].handleGraphicalSelection
        )

        # 连接错误追踪信号
        self.components["traceback_viewer"].sigHighlightLine.connect(
            self.components["editor"].go_to_line
        )

        # 连接CQ对象检查器信号
        self.components["cq_object_inspector"].sigDisplayObjects.connect(
            self.components["viewer"].display_many
        )
        self.components["cq_object_inspector"].sigRemoveObjects.connect(
            self.components["viewer"].remove_items
        )
        self.components["cq_object_inspector"].sigShowPlane.connect(
            self.components["viewer"].toggle_grid
        )
        self.components["cq_object_inspector"].sigShowPlane.connect(
            lambda visible, scale: self.components["viewer"].toggle_grid(visible, scale)
        )
        self.components["cq_object_inspector"].sigChangePlane.connect(
            self.components["viewer"].set_grid_orientation
        )

        # 连接调试器信号
        self.components["debugger"].sigLocalsChanged.connect(
            self.components["variables_viewer"].update_frame
        )
        self.components["debugger"].sigLineChanged.connect(
            self.components["editor"].go_to_line
        )
        self.components["debugger"].sigDebugging.connect(
            self.components["object_tree"].stashObjects
        )
        self.components["debugger"].sigCQChanged.connect(
            self.components["object_tree"].addObjects
        )
        self.components["debugger"].sigTraceback.connect(
            self.components["traceback_viewer"].addTraceback
        )

        # 连接编辑器信号
        self.components["editor"].triggerRerender.connect(
            self.components["debugger"].render
        )
        self.components["editor"].sigFilenameChanged.connect(
            self.handle_filename_change
        )

    def prepare_console(self):
        """准备控制台
        设置控制台环境和变量
        """
        console = self.components["console"]
        obj_tree = self.components["object_tree"]

        # 添加应用程序相关变量
        console.push_vars({"self": self})

        # 添加CQ相关变量
        console.push_vars(
            {
                "show": obj_tree.addObject,
                "show_object": obj_tree.addObject,
                "rand_color": self.components["debugger"]._rand_color,
                "cq": cq,
                "log": Logger(self.name).info,
            }
        )

    def fill_dummy(self):
        """填充示例内容
        在编辑器中添加示例代码
        """
        self.components["editor"].set_text(
            'import cadquery as cq\nresult = cq.Workplane("XY" ).box(3, 3, 0.5).edges("|Z").fillet(0.125)\nshow_object(result)'
        )

    def setup_logging(self):
        """设置日志系统
        配置日志记录和异常处理
        """
        from logbook.compat import redirect_logging
        from logbook import INFO, Logger

        # 重定向日志
        redirect_logging()
        self.components["log"].handler.level = INFO
        self.components["log"].handler.push_application()
        self._logger = Logger(self.name)

        def handle_exception(exc_type, exc_value, exc_traceback):
            """处理未捕获的异常
            
            Args:
                exc_type: 异常类型
                exc_value: 异常值
                exc_traceback: 异常追踪信息
            """
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            self._logger.error(
                "Uncaught exception occurred",
                exc_info=(exc_type, exc_value, exc_traceback),
            )

        # 设置全局异常处理器
        sys.excepthook = handle_exception

    def edit_preferences(self):
        """打开偏好设置对话框"""
        prefs = PreferencesWidget(self, self.components)
        prefs.exec()

    def about(self):
        """显示关于对话框"""
        about_dialog(
            self,
            f"About CQ-editor",
            f"PyQt GUI for CadQuery.\nVersion: {__version__}.\nSource Code: https://github.com/CadQuery/CQ-editor",
        )

    def check_for_cq_updates(self):
        """检查CadQuery更新"""
        check_gtihub_for_updates(self, cq)

    def documentation(self):
        """打开文档链接"""
        open_url("https://github.com/CadQuery")

    def cq_documentation(self):
        """打开CadQuery文档链接"""
        open_url("https://cadquery.readthedocs.io/en/latest/")

    def handle_filename_change(self, fname):
        """处理文件名变化
        
        Args:
            fname: 新的文件名
        """
        new_title = fname if fname else "*"
        self.setWindowTitle(f"{self.name}: {new_title}")

    def update_window_title(self, modified):
        """更新窗口标题以显示文件修改状态
        Args:
            modified: 文件是否被修改
        """
        title = self.windowTitle().rstrip("*")
        if modified:
            title += "*"
        self.setWindowTitle(title)


if __name__ == "__main__":
    pass
