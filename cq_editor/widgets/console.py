# 控制台组件
from PySide6.QtWidgets import QApplication  # 应用程序和动作
from PySide6.QtCore import Slot  # 信号和槽机制
from PySide6.QtGui import QAction

from qtconsole.rich_jupyter_widget import RichJupyterWidget  # Jupyter小部件
from qtconsole.inprocess import QtInProcessKernelManager  # 内核管理器

from ..mixins import ComponentMixin  # 组件混合

from ..icons import icon  # 图标

# 设置日志级别，关闭调试输出
import logging
logging.getLogger('ipykernel').setLevel(logging.ERROR)
logging.getLogger('jupyter_client').setLevel(logging.ERROR)
logging.getLogger('qtconsole').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)


class ConsoleWidget(RichJupyterWidget, ComponentMixin):  

    name = "Console"

    def __init__(self, customBanner=None, namespace=dict(), *args, **kwargs):
        # 调用父类的构造函数，传递剩余的位置参数和关键字参数
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        # 定义控制台的操作列表，这里包含一个清除控制台的操作
        self._actions = {
            "Run": [
                QAction(
                    # 设置操作的图标，图标名称为 'delete'
                    icon("delete"), 
                    # 设置操作的显示文本为 'Clear Console'
                    "Clear Console", 
                    # 设置操作的父对象为当前实例
                    self, 
                    # 当操作被触发时，调用 reset_console 方法
                    triggered=self.reset_console
                ),
            ]
        }
        # 设置控制台的字体大小
        self.font_size = 6
        # 定义控制台的样式表，用于设置文本编辑区域的外观
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
        # 设置控制台的语法高亮样式
        self.syntax_style = "zenburn"

        # 创建一个 Qt 进程内的内核管理器实例，那么和editor区域有什么区别
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        # 启动内核，并且不显示默认的欢迎信息
        kernel_manager.start_kernel(show_banner=False)


        # 设置内核的 GUI 类型为 Qt
        kernel_manager.kernel.gui = "qt"
        # 设置内核 shell 的 banner 为空字符串
        kernel_manager.kernel.shell.banner1 = ""

        # 创建内核客户端实例
        self.kernel_client = kernel_client = self._kernel_manager.client()
        # 启动内核客户端的通道
        kernel_client.start_channels()

        def stop():
            # 停止内核客户端的通道
            kernel_client.stop_channels()
            # 关闭内核管理器的内核
            kernel_manager.shutdown_kernel()
            # 退出当前的 Qt 应用程序
            QApplication.instance().exit()

        # 当控制台发出退出请求信号时，调用 stop 函数
        self.exit_requested.connect(stop)

        # 清除控制台的内容
        self.clear()

        # 将命名空间中的变量推送到 Jupyter 控制台
        self.push_vars(namespace)

    @Slot(dict)
    def push_vars(self, variableDict):
        """
        给定一个包含名称 / 值对的字典，将这些变量推送到 Jupyter 控制台小部件中。

        Args:
            variableDict (dict): 包含要推送到 Jupyter 控制台的变量名称和对应值的字典。
        """
        # 调用内核 shell 的 push 方法，将变量字典中的变量推送到 Jupyter 控制台
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):  # 清除控制台
        """
        Clears the terminal
        """
        self._control.clear()

    def reset_console(self):
        """
        重置终端，将其清空并恢复到只有一个输入提示符的状态。
        """
        # 调用 reset 方法重置控制台，设置 clear 参数为 True 以清除控制台内容
        self.reset(clear=True)

    def print_text(self, text):
        """
        将一些纯文本打印到控制台。

        Args:
            text (str): 要打印到控制台的纯文本内容。
        """
        # 调用 _append_plain_text 方法，将传入的纯文本追加到控制台显示区域
        self._append_plain_text(text)

    def execute_command(self, command):
        """
        在控制台小部件的环境中执行一条命令。

        Args:
            command (str): 要在控制台中执行的命令，通常是一段有效的 Python 代码字符串。
        """
        # 调用 _execute 方法执行传入的命令，第二个参数 False 表示不立即显示输出结果
        self._execute(command, False)

    def _banner_default(self):
        # 返回一个空字符串，表示不显示默认的 banner 信息
        return ""

    def app_theme_changed(self, theme):
        """
        根据应用程序的整体主题（亮色或暗色）来更改控制台的样式。

        Args:
            theme (str): 应用程序的主题名称，取值应为 "Dark" 或其他值（代表亮色主题）。
        """

        # 检查应用主题是否为暗色主题
        if theme == "Dark":
            # 若为暗色主题，将控制台的默认样式设置为 "linux" 风格
            self.set_default_style("linux")
        else:
            # 若为亮色主题，将控制台的默认样式设置为 "lightbg" 风格
            self.set_default_style("lightbg")


if __name__ == "__main__":

    import sys
    # 创建一个 QApplication 实例，用于管理应用程序的资源和事件循环
    app = QApplication(sys.argv)
    # 创建一个 ConsoleWidget 实例，并设置自定义的 banner 信息
    console = ConsoleWidget(customBanner="IPython console test")
    console.show()
    # 启动应用程序的事件循环，并返回退出代码
    sys.exit(app.exec_())
