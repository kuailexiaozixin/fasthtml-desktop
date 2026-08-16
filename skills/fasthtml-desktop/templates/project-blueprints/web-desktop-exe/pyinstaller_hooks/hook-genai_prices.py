# pyinstaller_hooks/hook-genai_prices.py
"""如果应用使用了 pydantic-ai，需要此钩子收集 genai_prices 元数据包"""
from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata("genai_prices")
