# 日志查看器
import logbook as logging
import re

from PySide6 import QtGui
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QAction

from ..mixins import ComponentMixin

from ..icons import icon


def strip_escape_sequences(input_string):
    # Regular expression pattern to match ANSI escape codes
    escape_pattern = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

    # Use re.sub to replace escape codes with an empty string
    clean_string = re.sub(escape_pattern, "", input_string)

    return clean_string


class _QtLogHandlerQObject(QObject):
    sigRecordEmit = Signal(str)


class QtLogHandler(logging.Handler, logging.StringFormatterHandlerMixin):

    def __init__(self, log_widget, *args, **kwargs):

        super(QtLogHandler, self).__init__(*args, **kwargs)

        log_format_string = (
            "[{record.time:%H:%M:%S%z}] {record.level_name}: {record.message}"
        )

        logging.StringFormatterHandlerMixin.__init__(self, log_format_string)

        self._qobject = _QtLogHandlerQObject()
        self._qobject.sigRecordEmit.connect(log_widget.append)

    def emit(self, record):
        self._qobject.sigRecordEmit.emit(self.format(record) + "\n")


class LogViewer(QPlainTextEdit, ComponentMixin):

    name = "Log viewer"

    def __init__(self, *args, **kwargs):

        super(LogViewer, self).__init__(*args, **kwargs)
        self._MAX_ROWS = 500

        self._actions = {
            "Run": [
                QAction(icon("delete"), "Clear Log", self, triggered=self.clear),
            ]
        }

        self.setReadOnly(True)
        self.setMaximumBlockCount(self._MAX_ROWS)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.handler = QtLogHandler(self)

    def append(self, msg):
        """Append text to the panel with ANSI escape sequences stipped."""
        self.moveCursor(QtGui.QTextCursor.End)
        self.insertPlainText(strip_escape_sequences(msg))

    def clear_log(self):
        """
        Clear the log content.
        """
        self.clear()
