"""
TTS库Optional类型错误补丁
这个补丁文件用于修复TTS库中Optional类型未定义的问题
"""
import builtins

# 确保Optional类型在TTS库导入前可用
if 'Optional' not in builtins.__dict__:
    from typing import Optional
    builtins.Optional = Optional

# 导入TTS库
from TTS.api import TTS

# 导出TTS类
def get_tts():
    """获取TTS实例"""
    return TTS