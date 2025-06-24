# 代码编辑器组件
import os
from modulefinder import ModuleFinder
from .simple_code_editor import SimpleCodeEditor
from PySide6.QtCore import Signal, QFileSystemWatcher, QTimer
from PySide6.QtWidgets import QFileDialog, QApplication
from PySide6.QtGui import QFontDatabase, QTextCursor, QAction
from path import Path
import sys
from pyqtgraph.parametertree import Parameter
from ..mixins import ComponentMixin
from ..utils import get_save_filename, get_open_filename, confirm
from ..icons import icon

class Editor(SimpleCodeEditor, ComponentMixin):
    """
    编辑器组件类
    继承自自定义的 SimpleCodeEditor 和 ComponentMixin
    """
    name = "Code Editor"
    triggerRerender = Signal(bool)
    sigFilenameChanged = Signal(str)
    preferences = Parameter.create(
        name="Preferences",
        children=[
            {"name": "Font size", "type": "int", "value": 12},
            {"name": "Autoreload", "type": "bool", "value": False},
            {"name": "Autoreload delay", "type": "int", "value": 50},
            {"name": "Autoreload: watch imported modules", "type": "bool", "value": False},
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
    was_modified_by_self = False
    def __init__(self, parent=None):
        self._watched_file = None
        super().__init__(parent)
        ComponentMixin.__init__(self)
        # 文件监视器
        self._file_watcher = QFileSystemWatcher(self)
        self._file_watch_timer = QTimer(self)
        self._file_watch_timer.setInterval(self.preferences["Autoreload delay"])
        self._file_watch_timer.setSingleShot(True)
        self._file_watcher.fileChanged.connect(lambda val: self._file_watch_timer.start())
        self._file_watch_timer.timeout.connect(self._file_changed)
        self.updatePreferences()
    def updatePreferences(self, *args):
        font = self.font()
        font.setPointSize(self.preferences["Font size"])
        self.setFont(font)
        self.toggle_wrap_mode(self.preferences["Line wrap"])
    def _file_changed(self):
        # 文件变动处理逻辑
        pass
    def new(self):
        if self.modified:
            rv = confirm(self, "请确认", "当前文档未保存，确定要新建吗？")
            if not rv:
                return
        self.set_text("")
        self.filename = ""
        self.reset_modified()
    def open(self):
        fname = get_open_filename(self, "打开文件", filter="*.py")
        if fname:
            with open(fname, "r", encoding="utf-8") as f:
                self.set_text(f.read())
            self.filename = fname
            self.reset_modified()
    def save(self):
        if not self.filename:
            return self.save_as()
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(self.get_text_with_eol())
        self.reset_modified()
    def save_as(self):
        fname = get_save_filename(self, "另存为", filter="*.py")
        if fname:
            self.filename = fname
            self.save()
    def load_from_file(self, fname):
        with open(fname, "r", encoding="utf-8") as f:
            self.set_text(f.read())
        self.filename = fname
        self.reset_modified()


if __name__ == "__main__":

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = Editor()
    editor.show()

    sys.exit(app.exec_())
