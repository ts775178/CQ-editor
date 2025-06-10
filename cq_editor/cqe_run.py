# 这个文件是命令行启动器，它作为CQ-editor工具的对外“入口包装层”，负责启动器环境配置
import os, sys, asyncio

# 删除可能干扰 OpenCASCADE 的环境变量（这和 cadquery 库有关）
# 负责启动前的环境变量清理，确保启动时环境变量的干净状态。
# 是为了解决 CadQuery + OpenCASCADE 在某些系统下会因为 CASROOT 环境变量冲突而报错的问题。
# 这种配置初始化不适合放到主逻辑中，单独分离能避免污染主界面代码。
if "CASROOT" in os.environ:
    del os.environ["CASROOT"]

# 如果是Windows 平台需要设置 asyncio 的事件循环策略
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 关键一行：从 __main__.py 中导入 main()
from cq_editor.__main__ import main

# 运行入口
if __name__ == "__main__":
    main()
