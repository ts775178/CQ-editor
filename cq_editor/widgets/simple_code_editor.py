from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QFrame
from PySide6.QtGui import QColor, QPainter, QTextFormat, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtCore import Qt, QRect, QSize, Signal

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self._highlighting_rules = []
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0077aa"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else",
            "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
            "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield"
        ]
        for word in keywords:
            self._highlighting_rules.append((rf"\\b{word}\\b", keyword_format))
        # 字符串
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#bb6600"))
        self._highlighting_rules.append((r'".*?"', string_format))
        self._highlighting_rules.append((r"'.*?'", string_format))
        # 注释
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#888888"))
        self._highlighting_rules.append((r"#.*", comment_format))

    def highlightBlock(self, text):
        import re
        for pattern, fmt in self._highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)
    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class SimpleCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Monaco", 12))
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.highlighter = PythonHighlighter(self.document())
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits
    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#f0f0f0"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#888888"))
                painter.drawText(0, top, self.line_number_area.width() - 2, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#eaf2fb")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)
    def get_text_with_eol(self):
        return self.toPlainText()
    def set_text(self, text):
        self.setPlainText(text)
    def get_selected_text(self):
        return self.textCursor().selectedText()
    def get_cursor_line_number(self):
        return self.textCursor().blockNumber() + 1
    def go_to_line(self, line_number):
        if line_number > 0:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number - 1)
            self.setTextCursor(cursor)
    @property
    def filename(self):
        return getattr(self, '_filename', "")
    @filename.setter
    def filename(self, value):
        self._filename = value
    @property
    def modified(self):
        return self.document().isModified()
    def reset_modified(self):
        self.document().setModified(False)
    def toggle_wrap_mode(self, enabled):
        if enabled:
            self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.NoWrap)
    def set_color_scheme(self, scheme):
        if scheme == "Dark":
            # 深色主题
            palette = self.palette()
            palette.setColor(QPalette.Base, QColor(53, 53, 53))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            self.setPalette(palette)
        else:
            # 浅色主题
            palette = self.palette()
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            self.setPalette(palette)
    def toggle_comment(self):
        """切换注释状态"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.LineUnderCursor)
        text = cursor.selectedText()
        lines = text.split('\u2029')  # QTextEdit 用 \u2029 作为换行符
        
        # 判断是注释还是取消注释
        if all(line.strip().startswith('#') for line in lines if line.strip()):
            # 取消注释
            new_lines = [line.replace('#', '', 1) if line.strip().startswith('#') else line for line in lines]
        else:
            # 添加注释
            new_lines = ['#' + line if line.strip() else line for line in lines]
        
        new_text = '\n'.join(new_lines)
        cursor.insertText(new_text)
    def setup_editor(self, **kwargs):
        """设置编辑器参数"""
        for key, value in kwargs.items():
            if key == 'linenumbers':
                self.line_numbers = value
            elif key == 'font':
                self.setFont(value)
            elif key == 'language':
                # 可以在这里设置语言特定的高亮
                pass
            elif key == 'markers':
                # 标记功能
                pass
            elif key == 'edge_line':
                # 行长度限制
                pass
            elif key == 'tab_mode':
                # Tab模式
                pass
            elif key == 'show_blanks':
                # 显示空白字符
                pass
            elif key == 'filename':
                # 文件名
                self.filename = value
    def addActions(self, actions):
        """添加动作到编辑器"""
        for action in actions:
            self.addAction(action)
    def menu(self):
        """返回菜单对象"""
        return None
    def run_cell_action(self):
        """运行单元格动作（占位符）"""
        return None
    def run_cell_and_advance_action(self):
        """运行单元格并前进动作（占位符）"""
        return None
    def run_selection_action(self):
        """运行选中内容动作（占位符）"""
        return None
    def re_run_last_cell_action(self):
        """重新运行最后一个单元格动作（占位符）"""
        return None
    def debugger(self):
        """返回调试器对象（简化版本）"""
        class SimpleDebugger:
            def get_breakpoints(self):
                return []
        return SimpleDebugger() 