import os, sys, asyncio
import logging

# 在程序启动时就配置日志，关闭所有调试输出
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

# 关闭特定模块的调试输出
for logger_name in ['ipykernel', 'jupyter_client', 'qtconsole', 'asyncio', 'tornado', 'zmq', 'OCC', 'VTK']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# 设置环境变量
os.environ["PYTHONASYNCIODEBUG"] = "0"
os.environ["IPYTHONDIR"] = ""
os.environ["JUPYTER_CONFIG_DIR"] = ""
os.environ["JUPYTER_DATA_DIR"] = ""

if "CASROOT" in os.environ:
    del os.environ["CASROOT"]

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from cq_editor.__main__ import main


if __name__ == "__main__":
    main()

