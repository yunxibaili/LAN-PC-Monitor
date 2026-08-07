# -*- coding: utf-8 -*-
"""
副机端启动脚本 —— 从项目根目录启动 client 子包。

用法：
    python -m client
    或双击 start_client.bat
"""
import os
import sys

# 确保项目根目录在 sys.path 中
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.main import main

if __name__ == "__main__":
    sys.exit(main())
