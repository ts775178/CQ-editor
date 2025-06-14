# 控制台组件
from PyQt5.QtWidgets import QApplication, QAction  # 应用程序和动作
from PyQt5.QtCore import pyqtSlot  # 信号和槽机制

from qtconsole.rich_jupyter_widget import RichJupyterWidget  # Jupyter小部件
from qtconsole.inprocess import QtInProcessKernelManager  # 内核管理器

from ..mixins import ComponentMixin  # 组件混合

from ..icons import icon  # 图标


class ConsoleWidget(RichJupyterWidget, ComponentMixin):

    name = "Console"

    def __init__(self, customBanner=None, namespace=dict(), *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        self._actions = {
            "Run": [
                QAction(
                    icon("delete"), "Clear Console", self, triggered=self.reset_console
                ),
            ]
        }
        self.font_size = 6
        self.style_sheet = """<style>
                            QPlainTextEdit, QTextEdit {
                                background-color: #3f3f3f;
                                background-clip: padding;
                                color: #dcdccc;
                                selection-background-color: #484848;
                            }
                            .inverted {
                                background-color: #dcdccc;
                                color: #3f3f3f;
                            }
                            .error { color: red; }
                            .in-prompt-number { font-weight: bold; }
                            .out-prompt-number { font-weight: bold; }
                            .in-prompt { color: navy; }
                            .out-prompt { color: darkred; }
                            </style>
                            """
        self.syntax_style = "zenburn"

        self.kernel_manager = kernel_manager = QtInProcessKernelManager()  # 创建内核管理器
        kernel_manager.start_kernel(show_banner=False)  # 启动内核
        kernel_manager.kernel.gui = "qt"  # 设置内核GUI
        kernel_manager.kernel.shell.banner1 = ""  # 设置内核shell banner

        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            QApplication.instance().exit()

        self.exit_requested.connect(stop)

        self.clear()

        self.push_vars(namespace)

    @pyqtSlot(dict)
    def push_vars(self, variableDict):
        """
        Given a dictionary containing name / value pairs, push those variables
        to the Jupyter console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):  # 清除控制台
        """
        Clears the terminal
        """
        self._control.clear()

    def reset_console(self):
        """
        Resets the terminal, which clears it back to a single prompt.
        """
        self.reset(clear=True)

    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)

    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self._execute(command, False)

    def _banner_default(self):

        return ""

    def app_theme_changed(self, theme):
        """
        Allows this console to be changed to match the light or dark theme of the rest of the app.
        """

        if theme == "Dark":
            self.set_default_style("linux")
        else:
            self.set_default_style("lightbg")


if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)

    console = ConsoleWidget(customBanner="IPython console test")
    console.show()

    sys.exit(app.exec_())
