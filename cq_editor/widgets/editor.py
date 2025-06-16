# 代码编辑器组件
import os
import spyder.utils.encoding
from modulefinder import ModuleFinder

from spyder.plugins.editor.widgets.codeeditor import CodeEditor
from PyQt5.QtCore import pyqtSignal, QFileSystemWatcher, QTimer
from PyQt5.QtWidgets import QAction, QFileDialog, QApplication
from PyQt5.QtGui import QFontDatabase, QTextCursor
from path import Path

import sys

from pyqtgraph.parametertree import Parameter

from ..mixins import ComponentMixin
from ..utils import get_save_filename, get_open_filename, confirm

from ..icons import icon


class Editor(CodeEditor, ComponentMixin):
    """
    编辑器组件类
    继承自Spyder的CodeEditor和自定义的ComponentMixin
    这样既获得了专业的代码编辑功能,又保持了与主程序的组件化集成
    """

    name = "Code Editor"

    # 定义信号用于通知文件变化和自动重载
    # 使用信号机制实现组件间的松耦合通信
    triggerRerender = pyqtSignal(bool)
    sigFilenameChanged = pyqtSignal(str)

    # 使用参数树定义编辑器配置
    # 这种方式便于统一管理和持久化配置
    preferences = Parameter.create(
        name="Preferences",
        children=[
            {"name": "Font size", "type": "int", "value": 12},
            {"name": "Autoreload", "type": "bool", "value": False},
            {"name": "Autoreload delay", "type": "int", "value": 50},
            {
                "name": "Autoreload: watch imported modules",
                "type": "bool",
                "value": False,
            },
            {"name": "Line wrap", "type": "bool", "value": False},
            {
                "name": "Color scheme",
                "type": "list",
                "values": ["Spyder", "Monokai", "Zenburn"],
                "value": "Spyder",
            },
            {"name": "Maximum line length", "type": "int", "value": 88},
        ],
    )

    EXTENSIONS = "py"

    # 标记文件是否由编辑器自身修改
    # 这个标记用于区分外部修改和内部修改,避免自动重载时的冲突
    was_modified_by_self = False

    def __init__(self, parent=None):
        """初始化编辑器
        采用多继承的方式,需要分别调用父类的初始化方法
        这样可以确保所有功能都被正确初始化
        """
        self._watched_file = None

        # 调用父类初始化
        super(Editor, self).__init__(parent)
        ComponentMixin.__init__(self)

        # 配置编辑器基本属性
        # 这些设置直接影响编辑器的外观和行为
        self.setup_editor(
            linenumbers=True,  # 显示行号
            markers=True,      # 显示标记
            edge_line=self.preferences["Maximum line length"],  # 设置行长度限制
            tab_mode=False,    # 禁用Tab模式
            show_blanks=True,  # 显示空白字符
            font=QFontDatabase.systemFont(QFontDatabase.FixedFont),  # 使用等宽字体
            language="Python", # 设置语言为Python
            filename="",       # 初始无文件名
        )

        # 定义编辑器动作
        # 使用字典组织动作,便于管理和扩展
        self._actions = {
            "File": [
                QAction(
                    icon("new"), "New", self, shortcut="ctrl+N", triggered=self.new
                ),
                QAction(
                    icon("open"), "Open", self, shortcut="ctrl+O", triggered=self.open
                ),
                QAction(
                    icon("save"), "Save", self, shortcut="ctrl+S", triggered=self.save
                ),
                QAction(
                    icon("save_as"),
                    "Save as",
                    self,
                    shortcut="ctrl+shift+S",
                    triggered=self.save_as,
                ),
                QAction(
                    icon("autoreload"),
                    "Automatic reload and preview",
                    self,
                    triggered=self.autoreload,
                    checkable=True,
                    checked=False,
                    objectName="autoreload",
                ),
            ]
        }

        # 添加动作到编辑器
        for a in self._actions.values():
            self.addActions(a)

        # 修复上下文菜单
        self._fixContextMenu()

        # 设置文件监视器
        # 使用QFileSystemWatcher实现文件自动重载
        self._file_watcher = QFileSystemWatcher(self)
        # 使用定时器延迟处理文件变化
        # 这样可以避免文件写入未完成就触发重载
        self._file_watch_timer = QTimer(self)
        self._file_watch_timer.setInterval(self.preferences["Autoreload delay"])
        self._file_watch_timer.setSingleShot(True)
        self._file_watcher.fileChanged.connect(
            lambda val: self._file_watch_timer.start()
        )
        self._file_watch_timer.timeout.connect(self._file_changed)

        # 更新编辑器配置
        self.updatePreferences()

    def _fixContextMenu(self):
        """修复上下文菜单
        移除不需要的Spyder编辑器动作
        这样可以保持界面简洁,只保留必要的功能
        """
        menu = self.menu
        menu.removeAction(self.run_cell_action)
        menu.removeAction(self.run_cell_and_advance_action)
        menu.removeAction(self.run_selection_action)
        menu.removeAction(self.re_run_last_cell_action)

    def updatePreferences(self, *args):
        """更新编辑器配置
        当配置改变时,需要同步更新编辑器的外观和行为
        这样可以保持界面的一致性
        """
        # 更新颜色方案
        self.set_color_scheme(self.preferences["Color scheme"])

        # 更新字体
        font = self.font()
        font.setPointSize(self.preferences["Font size"])
        self.set_font(font)

        # 更新自动重载状态
        self.findChild(QAction, "autoreload").setChecked(self.preferences["Autoreload"])

        # 更新文件监视延迟
        self._file_watch_timer.setInterval(self.preferences["Autoreload delay"])

        # 更新换行模式
        self.toggle_wrap_mode(self.preferences["Line wrap"])

        # 更新行长度限制
        self.edge_line.set_enabled(True)
        self.edge_line.set_columns(self.preferences["Maximum line length"])

        # 更新文件监视
        self._clear_watched_paths()
        self._watch_paths()

    def confirm_discard(self):

        if self.modified:
            rv = confirm(
                self,
                "Please confirm",
                "Current document is not saved - do you want to continue?",
            )
        else:
            rv = True

        return rv

    def new(self):
        """
        创建一个新的文档。在创建新文档之前，会先确认是否丢弃当前未保存的更改。
        如果用户选择不丢弃未保存的更改，则会取消创建新文档的操作。
        若操作继续，会清空编辑器内容，重置文件名，并标记文档为未修改状态。
        """
        # 调用 confirm_discard 方法确认是否丢弃未保存的更改
        # 如果用户选择不丢弃，该方法返回 False，此时直接返回，终止创建新文档的操作
        if not self.confirm_discard():
            return

        # 清空编辑器中的文本内容
        self.set_text("")
        # 将文件名重置为空字符串，表示这是一个未命名的新文档
        self.filename = ""
        # 重置文档的修改状态，标记为未修改
        self.reset_modified()

    def open(self):

        if not self.confirm_discard():
            return

        curr_dir = Path(self.filename).absolute().dirname()
        fname = get_open_filename(self.EXTENSIONS, curr_dir)
        if fname != "":
            self.load_from_file(fname)

    def load_from_file(self, fname):

        self.set_text_from_file(fname)
        self.filename = fname
        self.reset_modified()

    def save(self):
        """
        Saves the current document to the current filename if it exists, otherwise it triggers a
        save-as dialog.
        """

        if self._filename != "":
            with open(self._filename, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())

            # Let the editor and the rest of the app know that the file is no longer dirty
            self.reset_modified()

            self.was_modified_by_self = True

        else:
            self.save_as()

    def save_as(self):

        fname = get_save_filename(self.EXTENSIONS)
        if fname != "":
            with open(fname, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())
                self.filename = fname

            self.reset_modified()

    def toggle_comment(self):
        """
        Allows us to mark the document as modified when the user toggles a comment.
        """
        super(Editor, self).toggle_comment()
        self.document().setModified(True)

    def _update_filewatcher(self):
        if self._watched_file and (
            self._watched_file != self.filename or not self.preferences["Autoreload"]
        ):
            self._clear_watched_paths()
            self._watched_file = None
        if (
            self.preferences["Autoreload"]
            and self.filename
            and self.filename != self._watched_file
        ):
            self._watched_file = self._filename
            self._watch_paths()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, fname):
        self._filename = fname
        self._update_filewatcher()
        self.sigFilenameChanged.emit(fname)

    def _clear_watched_paths(self):
        paths = self._file_watcher.files()
        if paths:
            self._file_watcher.removePaths(paths)

    def _watch_paths(self):
        if Path(self._filename).exists():
            self._file_watcher.addPath(self._filename)
            if self.preferences["Autoreload: watch imported modules"]:
                module_paths = self.get_imported_module_paths(self._filename)
                if module_paths:
                    self._file_watcher.addPaths(module_paths)

    # callback triggered by QFileSystemWatcher
    def _file_changed(self):
        # neovim writes a file by removing it first so must re-add each time
        self._watch_paths()

        # Save the current cursor position and selection
        cursor = self.textCursor()
        cursor_position = cursor.position()
        anchor_position = cursor.anchor()

        # Save the current scroll position
        vertical_scroll_pos = self.verticalScrollBar().value()
        horizontal_scroll_pos = self.horizontalScrollBar().value()

        # Block signals to avoid reset issues
        self.blockSignals(True)

        # Read the contents of the file into a string
        with open(self._filename, "r", encoding="utf-8") as f:
            file_contents = f.read()

            # Insert new text while preserving history
            cursor = self.textCursor()
            cursor.select(QTextCursor.Document)
            cursor.insertText(file_contents)

            # The editor will not always update after a text insertion, so we force it
            QApplication.processEvents()

        # Stop blocking signals
        self.blockSignals(False)

        self.document().setModified(True)

        # Undo has to be backed up one step to compensate for the text insertion
        if self.was_modified_by_self:
            self.document().undo()
            self.was_modified_by_self = False

        # Restore the cursor position and selection
        cursor.setPosition(anchor_position)
        cursor.setPosition(cursor_position, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

        # Restore the scroll position
        self.verticalScrollBar().setValue(vertical_scroll_pos)
        self.horizontalScrollBar().setValue(horizontal_scroll_pos)

        # Reset the dirty state and trigger a 3D render
        self.reset_modified()
        self.triggerRerender.emit(True)

    # Turn autoreload on/off.
    def autoreload(self, enabled):
        self.preferences["Autoreload"] = enabled
        self._update_filewatcher()

    def reset_modified(self):

        self.document().setModified(False)

    @property
    def modified(self):

        return self.document().isModified()

    def saveComponentState(self, store):

        if self.filename != "":
            store.setValue(self.name + "/state", self.filename)

    def restoreComponentState(self, store):

        filename = store.value(self.name + "/state")

        if filename and self.filename == "":
            try:
                self.load_from_file(filename)
            except IOError:
                self._logger.warning(f"could not open {filename}")

    def get_imported_module_paths(self, module_path):
        """获取导入模块的路径
        使用ModuleFinder分析Python文件中的导入语句
        这样可以实现模块级别的文件监视
        """
        finder = ModuleFinder([os.path.dirname(module_path)])
        imported_modules = []

        try:
            finder.run_script(module_path)
        except SyntaxError as err:
            self._logger.warning(f"Syntax error in {module_path}: {err}")
        except Exception as err:
            # 处理CadQuery导入的特殊情况
            if "cadquery" not in finder.badmodules or (
                "cadquery" in finder.badmodules and len(finder.badmodules) > 1
            ):
                self._logger.warning(
                    f"Cannot determine imported modules in {module_path}: {type(err).__name__} {err}"
                )
        else:
            # 收集所有导入模块的路径
            for module_name, module in finder.modules.items():
                if module_name != "__main__":
                    path = getattr(module, "__file__", None)
                    if path is not None and os.path.isfile(path):
                        imported_modules.append(path)

        return imported_modules


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = Editor()
    editor.show()

    sys.exit(app.exec_())
