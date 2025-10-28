# 语音合成项目

本项目基于Coqui TTS框架，在本地CPU环境下部署开发的语音合成系统。系统采用模块化设计，支持一次加载模型持续运行，能够处理多文件输入并生成meta文件。

## 项目结构

```
├── src/
│   ├── modules/              # 模块目录
│   │   ├── model_manager.py  # 模型管理库类
│   │   ├── tts_input.py      # TTS输入数据结构
│   │   ├── text_loader.py    # 文本文件加载模块
│   │   └── voice_library.py  # 音色库类
│   ├── tts_synthesizer.py    # 主程序
│   └── example_usage.py      # 使用示例
├── data_voice/               # 语音数据集
│   └── seedtts_testset/
│       └── zh/
│           ├── meta.lst      # 元数据文件
│           ├── prompt-wavs/  # 音色参考音频
│           └── wavs/         # 目标音频
├── output/                   # 输出目录
├── docs/                     # 文档目录
└── requirements.txt          # 项目依赖
```

## 功能特点

- 一次加载模型，持续运行，提高效率
- 支持多种文件格式输入（TXT、CSV、Excel、JSON）
- 自动从音色库中选择音色参考
- 生成包含原文、音色路径和输出路径的meta文件
- 模块化设计，便于扩展和维护

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行方式

```bash
python src/tts_synthesizer.py --input your_file.xlsx --output_meta output/meta.csv
```

### 编程方式

参见 `src/example_usage.py` 文件的示例代码。

## 系统要求

- Python 3.8+ 
- 足够的磁盘空间用于存储模型和输出文件
- 推荐8GB以上内存以获得更好的性能

## 主要模块说明

- **ModelManager**: 负责加载和管理TTS模型，支持一次加载多次使用
- **TTSInput**: 定义TTS模型的输入数据结构
- **TextLoader**: 支持多种格式的文本文件加载和解析
- **VoiceLibrary**: 管理和选择音色参考音频
- **TTSSynthesizer**: 主程序类，整合各模块功能

## 注意事项

- 首次运行时会自动下载TTS模型，可能需要一些时间
- 处理大量文本时，建议分批处理以避免内存不足
- 如果遇到性能问题，可以尝试减小批量处理的并发数