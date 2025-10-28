from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
print(tts.speakers)

# Text to speech to a file
tts.tts_to_file(text="拿一只中型平底锅，用中大火融化奶油，加入面粉搅拌至滑顺。", speaker_wav="/Users/ray/work/DataGen/data_voice/seedtts_testset/zh/prompt-wavs/00004501-00000032.wav", language="zh-cn", file_path="000451.wav")
