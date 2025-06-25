"""
简化的控制台组件
避免使用 qtconsole 来防止段错误
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QHBoxLayout
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor, QColor, QPalette

import sys
import traceback
from io import StringIO


class SimpleConsole(QWidget):
    """简化的控制台组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 添加 preferences 属性
        self.preferences = None
        
        # 设置布局
        layout = QVBoxLayout(self)
        
        # 输出区域
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Monaco", 10))
        
        # 输入区域
        input_layout = QHBoxLayout()
        self.prompt_label = QLineEdit(">>> ")
        self.prompt_label.setReadOnly(True)
        self.prompt_label.setMaximumWidth(50)
        self.prompt_label.setAlignment(Qt.AlignRight)
        
        self.input_area = QLineEdit()
        self.input_area.returnPressed.connect(self.execute_command)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input_area)
        
        layout.addWidget(self.output_area)
        layout.addLayout(input_layout)
        
        # 设置样式
        self.set_dark_theme()
        
        # 初始化命名空间
        self.namespace = {}
        
        # 显示欢迎信息
        self.print_text("Simple Python Console\nType 'help()' for more information.\n")
    
    def set_dark_theme(self):
        """设置深色主题"""
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor(53, 53, 53))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        self.setPalette(palette)
        
        # 设置输出区域样式
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: none;
            }
        """)
        
        # 设置输入区域样式
        self.input_area.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 2px;
            }
        """)
        
        self.prompt_label.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #00ff00;
                border: none;
                font-weight: bold;
            }
        """)
    
    def set_light_theme(self):
        """设置浅色主题"""
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # 重置样式
        self.output_area.setStyleSheet("")
        self.input_area.setStyleSheet("")
        self.prompt_label.setStyleSheet("")
    
    def print_text(self, text):
        """打印文本到输出区域"""
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output_area.setTextCursor(cursor)
        self.output_area.insertPlainText(text)
        
        # 滚动到底部
        self.output_area.ensureCursorVisible()
    
    def execute_command(self):
        """执行命令"""
        command = self.input_area.text().strip()
        if not command:
            return
        
        # 清空输入区域
        self.input_area.clear()
        
        # 显示命令
        self.print_text(f">>> {command}\n")
        
        try:
            # 捕获输出
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # 执行命令
            result = eval(command, self.namespace)
            
            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # 显示输出
            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()
            
            if stderr_text:
                self.print_text(f"Error: {stderr_text}\n")
            elif stdout_text:
                self.print_text(stdout_text)
            elif result is not None:
                self.print_text(f"{result}\n")
                
        except Exception as e:
            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # 显示错误信息
            error_msg = f"Error: {type(e).__name__}: {str(e)}\n"
            self.print_text(error_msg)
    
    def push_vars(self, variable_dict):
        """推送变量到命名空间"""
        self.namespace.update(variable_dict)
    
    def clear(self):
        """清空输出区域"""
        self.output_area.clear()
    
    def reset_console(self):
        """重置控制台"""
        self.clear()
        self.namespace.clear()
        self.print_text("Console reset.\n")
    
    def app_theme_changed(self, theme):
        """主题变化处理"""
        if theme == "Dark":
            self.set_dark_theme()
        else:
            self.set_light_theme()
    
    def toolbarActions(self):
        """返回工具栏动作列表"""
        return []
    
    def menuActions(self):
        """返回菜单动作列表"""
        return {}