from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
device = "cpu"
manager = ModelManager()
model_path, config_path, model_item = manager.download_model("tts_models/zh-CN/baker/tacotron2-DDC-GST")
synthesizer = Synthesizer(
    model_path, config_path, None, None, None,
)

from IPython.display import Audio, display

example_text = '你好吗？我很好。'

wavs = synthesizer.tts(example_text)

display(Audio(wavs, rate=synthesizer.output_sample_rate))