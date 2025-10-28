from TTS.utils.manage import ModelManager
import os

# 获取默认模型管理器
manager = ModelManager()

# 打印模型下载根目录
print("Model download root:", manager.output_prefix)
