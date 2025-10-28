# Coqui TTS 语音合成项目

这是一个基于Coqui TTS的语音合成项目，用于在本地CPU环境下进行高效的语音合成。该项目设计了模块化的架构，支持一次加载模型持续运行，处理多文件输入并生成meta文件。

## 项目结构

```
├── .vscode/            # VS Code配置文件
├── data_voice/         # 语音数据集
│   ├── cv-corpus-22.0-delta-2025-06-20/  # Common Voice数据集
│   ├── cv-corpus-3/    # Common Voice数据集
│   └── seedtts_testset/# SeedTTS测试集
├── docs/               # 项目文档
├── logs/               # 日志文件
├── models/             # 模型存储目录
│   └── tts/            # TTS模型
├── output/             # 输出文件目录
├── src/                # 源代码
│   ├── modules/        # 核心模块
│   └── utils/          # 工具函数
├── tests/              # 测试用例
└── requirements.txt    # 项目依赖
```

## 系统架构

该项目采用模块化设计，主要包含以下核心模块：

1. **ModelManager** - 模型管理库类，负责加载、管理和卸载TTS模型
2. **TextLoader** - 文本文件加载模块，支持多种格式的文本文件加载和解析
3. **VoiceLibrary** - 音色库类，用于管理和选择音色参考音频
4. **TTSSynthesizer** - 主程序类，整合各模块功能，提供语音合成服务

## 核心功能

1. **模型管理** - 支持一次加载模型持续运行，避免重复加载开销
2. **多格式文本输入** - 支持TXT、CSV、Excel和JSON等多种格式的文本文件输入
3. **音色管理** - 从数据集中自动加载并管理音色参考音频
4. **批量处理** - 支持批量文本处理和并发合成
5. **meta文件生成** - 自动生成包含合成信息的meta文件

## 环境要求

- Python 3.8+ 
- 依赖项详见 requirements.txt
- CPU环境运行（也支持GPU加速）

## 安装方法

1. 克隆项目代码
2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 简单使用示例

```python
from src.modules.model_manager import model_manager
from src.modules.voice_library import voice_library
from src.tts_synthesizer import TTSSynthesizer

# 加载模型
model_manager.load_model()

# 创建合成器
 synthesizer = TTSSynthesizer(output_dir="./output")

# 选择音色
prompt_wav = voice_library.get_random_prompt()

# 合成语音
result = synthesizer.synthesize_text(
    text="你好，这是一段测试文本。",
    speaker_wav=prompt_wav,
    output_path="./output/test.wav",
    language="zh-cn"
)

# 处理文件
files_processed = synthesizer.process_file("/path/to/text.txt", meta_file="output/meta.lst")
```

### 2. 运行示例脚本

```bash
python src/example_usage.py
```

### 3. 运行测试用例

```bash
python -m unittest discover tests
# 或直接运行测试脚本
python tests/test_tts_synthesizer.py
```

## 命令行使用

可以直接使用tts_synthesizer.py作为命令行工具：

```bash
python src/tts_synthesizer.py --text "你好，世界！" --output output/hello.wav
# 处理文件
python src/tts_synthesizer.py --file data.txt --output_dir output
```

## 文档

详细文档请查看 `docs` 目录下的文档文件。

## 注意事项

1. 首次运行时，系统会自动下载所需的TTS模型，可能需要一定时间和网络带宽
2. 在CPU环境下，合成速度可能较慢，建议处理较短的文本或调整批处理参数
3. 如需使用其他TTS模型，请修改model_manager.py中的默认模型配置

## License

[MIT](https://opensource.org/licenses/MIT)