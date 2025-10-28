# 核心模块文档

本文档详细描述了项目中的各个核心模块及其功能。

## 1. 模型管理库类 (ModelManager)

**文件路径**: `src/modules/model_manager.py`

ModelManager负责加载和管理TTS模型，支持一次加载多次使用，避免重复加载模型的开销。

### 主要功能

- 加载TTS模型（默认加载xtts_v2模型）
- 缓存已加载的模型，避免重复加载
- 卸载指定模型或所有模型以释放资源
- 检查模型是否已加载
- 列出所有已加载的模型

### 类结构

```python
class ModelManager:
    def __init__(self):
        # 初始化模型管理器
        pass
    
    def load_model(self, model_name=None, device="cpu"):
        # 加载指定的TTS模型
        pass
    
    def get_model(self, model_name=None):
        # 获取指定的模型实例
        pass
    
    def unload_model(self, model_name=None):
        # 卸载指定的模型
        pass
    
    def unload_all_models(self):
        # 卸载所有已加载的模型
        pass
    
    def list_loaded_models(self):
        # 列出所有已加载的模型名称
        pass
    
    def is_model_loaded(self, model_name=None):
        # 检查指定的模型是否已加载
        pass
```

### 使用示例

```python
from modules.model_manager import model_manager

# 加载默认模型
tts = model_manager.load_model()

# 检查模型是否已加载
is_loaded = model_manager.is_model_loaded()

# 列出所有已加载的模型
loaded_models = model_manager.list_loaded_models()

# 卸载模型
model_manager.unload_model()
```

## 2. TTS输入数据结构 (tts_input.py)

**文件路径**: `src/modules/tts_input.py`

定义了TTS模型的输入和输出数据结构，用于标准化数据传递。

### 主要类

- **TTSInput**: 单个TTS请求的输入数据结构
- **TTSBatchInput**: 批量TTS请求的输入数据结构
- **TTSSynthesisResult**: 单个TTS请求的输出结果
- **TTSBatchResult**: 批量TTS请求的输出结果

### 数据结构

```python
@dataclass
class TTSInput:
    text: str              # 要合成语音的文本
    speaker_wav: str       # 音色参考音频文件路径
    output_path: str       # 输出文件路径
    language: str = "zh-cn" # 语言代码，默认为中文
    model_name: Optional[str] = None # 模型名称
    split_sentences: bool = True     # 是否分割句子
    additional_params: Dict[str, Any] = field(default_factory=dict) # 其他参数

@dataclass
class TTSBatchInput:
    inputs: List[TTSInput] # 批量输入列表
    max_concurrency: int = 1 # 批处理的最大并发数

@dataclass
class TTSSynthesisResult:
    input_data: TTSInput   # 对应的输入
    success: bool          # 是否成功
    error_message: Optional[str] = None # 错误信息
    output_file: Optional[str] = None   # 输出文件路径
    processing_time: Optional[float] = None # 处理时间（秒）

@dataclass
class TTSBatchResult:
    results: List[TTSSynthesisResult] # 单个处理结果列表
    total_processing_time: Optional[float] = None # 总处理时间（秒）
    success_count: int = 0 # 成功的数量
    failure_count: int = 0 # 失败的数量
```

## 3. 文本文件加载模块 (TextLoader)

**文件路径**: `src/modules/text_loader.py`

TextLoader负责加载和解析各种格式的文本文件，支持TXT、CSV、Excel和JSON格式。

### 主要功能

- 自动识别文件格式并使用相应的解析方法
- 支持从不同格式文件中提取文本
- 提供将文本转换为TTS输入格式的功能
- 错误处理和日志记录

### 类结构

```python
class TextLoader:
    def __init__(self):
        # 初始化文本加载器
        pass
    
    def load_text_file(self, file_path, **kwargs):
        # 加载文本文件并返回解析后的文本列表
        pass
    
    def _load_txt_file(self, file_path, encoding='utf-8', **kwargs):
        # 加载TXT文件
        pass
    
    def _load_csv_file(self, file_path, text_column='text', encoding='utf-8', **kwargs):
        # 加载CSV文件
        pass
    
    def _load_excel_file(self, file_path, sheet_name=0, text_column='text', **kwargs):
        # 加载Excel文件
        pass
    
    def _load_json_file(self, file_path, text_key='text', **kwargs):
        # 加载JSON文件
        pass
    
    def convert_to_tts_inputs(self, texts_data, output_dir, speaker_wav, **kwargs):
        # 将文本数据转换为TTSInput对象列表
        pass
```

### 使用示例

```python
from modules.text_loader import TextLoader

loader = TextLoader()

# 加载TXT文件
texts = loader.load_text_file("data.txt")

# 加载CSV文件
excel_texts = loader.load_text_file("data.xlsx", sheet_name="Sheet1", text_column="content")

# 转换为TTS输入
tts_inputs = loader.convert_to_tts_inputs(
    texts,
    output_dir="./output",
    speaker_wav="./voice.wav"
)
```

## 4. 音色库类 (VoiceLibrary)

**文件路径**: `src/modules/voice_library.py`

VoiceLibrary负责管理和选择音色参考音频，从数据集加载meta数据和prompt音频。

### 主要功能

- 从数据目录加载meta数据
- 获取所有可用的prompt音频文件
- 随机选择prompt音频
- 根据名称获取特定的prompt音频
- 根据prompt音频查找对应的target音频和文本

### 类结构

```python
class VoiceLibrary:
    def __init__(self, data_dir="data_voice/seedtts_testset/zh"):
        # 初始化音色库
        pass
    
    def _load_meta_data(self):
        # 加载meta数据
        pass
    
    def _get_available_prompts(self):
        # 获取所有可用的prompt wav文件
        pass
    
    def get_random_prompt(self):
        # 随机选择一个prompt音频
        pass
    
    def get_prompt_by_name(self, name):
        # 根据名称获取特定的prompt音频
        pass
    
    def get_target_wav_for_prompt(self, prompt_path):
        # 根据prompt音频查找对应的target音频和文本
        pass
```

### 使用示例

```python
from modules.voice_library import voice_library

# 随机选择一个音色
random_prompt = voice_library.get_random_prompt()

# 根据名称获取音色
specific_prompt = voice_library.get_prompt_by_name("000451")

# 获取对应的target信息
target_info = voice_library.get_target_wav_for_prompt(random_prompt)
if target_info:
    target_wav, target_text = target_info
```

## 5. TTS合成器 (tts_synthesizer.py)

**文件路径**: `src/tts_synthesizer.py`

TTSSynthesizer是主程序类，整合了模型管理、文本加载和音色库模块，提供完整的语音合成功能。

### 主要功能

- 合成单个文本为语音
- 批量合成多个文本
- 处理文本文件并生成语音
- 生成meta文件，包含文本、音色路径和输出路径的对应关系
- 命令行参数解析

### 类结构

```python
class TTSSynthesizer:
    def __init__(self, output_dir="output"):
        # 初始化TTS合成器
        pass
    
    def synthesize_text(self, text, speaker_wav, output_path, language="zh-cn", split_sentences=True):
        # 合成单个文本为语音
        pass
    
    def synthesize_batch(self, inputs):
        # 批量合成多个文本
        pass
    
    def process_file(self, file_path, meta_file=None, **kwargs):
        # 处理文本文件并生成语音
        pass
    
    def process_files(self, file_paths, meta_file=None, **kwargs):
        # 处理多个文本文件
        pass
    
    def _generate_meta_file(self, results, meta_file_path):
        # 生成meta文件
        pass
```

### 使用示例

```python
from tts_synthesizer import TTSSynthesizer

# 创建合成器实例
synthesizer = TTSSynthesizer(output_dir="./output")

# 合成单个文本
result = synthesizer.synthesize_text(
    text="你好，这是一段测试文本。",
    speaker_wav="./voice.wav",
    output_path="./output/test.wav"
)

# 处理文件
synthesizer.process_file("data.txt", meta_file="./output/meta.lst")
```