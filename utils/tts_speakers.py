from TTS.api import TTS

# 加载模型
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

# 检查是否为多说话人模型
if hasattr(tts, "speaker_manager") and tts.speaker_manager is not None:
    print("Available speaker names:", tts.speaker_manager.names)
elif hasattr(tts.synthesizer.tts_model, "speakers"):
    # 备用方式：直接访问模型 speakers 字典
    print("Available speaker IDs:", list(tts.synthesizer.tts_model.speakers.keys()))
else:
    print("This model does not have a speakers list (e.g., single-speaker).")