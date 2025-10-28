# 语音合成项目使用指南

## 1. 环境准备

### 1.1 安装依赖

在使用本项目之前，需要安装必要的依赖包：

```bash
pip install -r requirements.txt
```

主要依赖包括：
- TTS (Coqui TTS框架)
- pandas (数据处理)
- openpyxl (Excel文件支持)

### 1.2 系统要求

- Python 3.8或更高版本
- 足够的磁盘空间（首次运行会下载模型文件，约需几GB空间）
- 推荐8GB以上内存以获得更好的性能
- CPU环境即可运行，无需GPU

## 2. 快速开始

### 2.1 命令行方式

最简单的使用方式是通过命令行直接运行主程序：

```bash
python src/tts_synthesizer.py --input your_file.xlsx --output_meta output/meta.csv
```

### 2.2 编程方式

也可以在自己的Python代码中使用本项目的模块：

```python
from modules.model_manager import model_manager
from modules.voice_library import voice_library
from tts_synthesizer import TTSSynthesizer

# 加载模型
model_manager.load_model()

# 创建合成器
 synthesizer = TTSSynthesizer(output_dir="./output")

# 合成文本
result = synthesizer.synthesize_text(
    text="这是一段测试文本",
    speaker_wav=voice_library.get_random_prompt(),
    output_path="./output/test.wav"
)
```

## 3. 详细使用说明

### 3.1 命令行参数

主程序 `tts_synthesizer.py` 支持以下命令行参数：

```
--input, -i: 输入文件路径（支持TXT、CSV、Excel、JSON格式）
--output_meta, -m: 输出meta文件路径
--output_dir, -o: 音频输出目录（默认为"output"）
--model_name, -mn: TTS模型名称（默认为xtts_v2）
--language, -l: 语言代码（默认为"zh-cn"）
```

示例：

```bash
python src/tts_synthesizer.py -i data/texts.xlsx -m output/results.csv -o output/audio -l zh-cn
```

### 3.2 支持的输入文件格式

#### 3.2.1 TXT文件

纯文本文件，每行一个文本条目。

```
这是第一条文本
这是第二条文本
这是第三条文本
```

#### 3.2.2 CSV文件

逗号分隔值文件，需要包含文本列。默认查找"text"列，也可以通过参数指定。

```csv
id,text
1,这是第一条文本
2,这是第二条文本
3,这是第三条文本
```

#### 3.2.3 Excel文件

支持.xlsx和.xls格式，同样需要包含文本列。可以通过参数指定工作表名称和文本列。

#### 3.2.4 JSON文件

支持JSON数组格式，每个对象需要包含文本字段。

```json
[
  {"text": "这是第一条文本"},
  {"text": "这是第二条文本"},
  {"text": "这是第三条文本"}
]
```

### 3.3 输出文件

#### 3.3.1 音频文件

合成的语音文件以WAV格式保存在指定的输出目录中，文件命名格式为：`{index}_{random_id}.wav`。

#### 3.3.2 Meta文件

生成的meta文件记录了合成任务的详细信息，格式为CSV，包含以下列：

- `text`: 原始文本内容
- `speaker_wav`: 使用的音色参考音频路径
- `output_wav`: 合成的音频文件路径
- `success`: 合成是否成功
- `processing_time`: 处理时间（秒）

## 4. 音色库使用

### 4.1 音色选择

系统会自动从音色库中随机选择一个音色参考音频。音色库位于`data_voice/seedtts_testset/zh/prompt-wavs/`目录下。

### 4.2 自定义音色

如果需要使用自定义音色，可以将音频文件（WAV格式）放入音色库目录，然后更新`meta.lst`文件。

## 5. 常见问题解决

### 5.1 内存不足

症状：程序运行过程中出现内存错误

解决方法：
- 减小批量处理的文本数量
- 处理大量文本时，分批进行处理
- 增加系统内存

### 5.2 模型下载失败

症状：首次运行时模型下载失败

解决方法：
- 检查网络连接
- 手动下载模型文件并放入TTS模型目录（通常位于用户目录下的`.local/share/tts/`）

### 5.3 合成语音质量问题

症状：合成的语音质量不理想

解决方法：
- 尝试使用不同的音色参考音频
- 对于长文本，确保`split_sentences`参数设置为True
- 检查输入文本的质量，避免使用过于复杂或不符合语言习惯的文本

### 5.4 文件格式不支持

症状：无法加载或解析输入文件

解决方法：
- 检查文件格式是否为支持的格式（TXT、CSV、Excel、JSON）
- 确保文件编码为UTF-8
- 对于CSV和Excel文件，确保包含文本列

## 6. 高级用法

### 6.1 批量处理

对于大量文本，可以使用批量处理功能提高效率：

```python
from modules.tts_input import TTSInput, TTSBatchInput
from tts_synthesizer import TTSSynthesizer

# 准备批量输入
batch_input = TTSBatchInput(
    inputs=[
        TTSInput(
            text="第一条文本",
            speaker_wav="/path/to/speaker1.wav",
            output_path="/path/to/output1.wav"
        ),
        TTSInput(
            text="第二条文本",
            speaker_wav="/path/to/speaker2.wav",
            output_path="/path/to/output2.wav"
        )
    ],
    max_concurrency=2  # 设置最大并发数
)

# 创建合成器并处理批量输入
synthesizer = TTSSynthesizer()
batch_result = synthesizer.synthesize_batch(batch_input)

# 处理结果
for result in batch_result.results:
    if result.success:
        print(f"成功合成到: {result.output_file}")
    else:
        print(f"合成失败: {result.error_message}")
```

### 6.2 自定义模型

如果需要使用不同的TTS模型，可以在加载模型时指定：

```python
from modules.model_manager import model_manager

# 加载特定模型
model_manager.load_model(model_name="tts_models/en/ljspeech/tacotron2-DDC")
```

### 6.3 集成到其他项目

可以将本项目的模块集成到其他Python项目中：

```python
from your_project import TTSSynthesizer

# 创建合成器实例
synthesizer = TTSSynthesizer()

# 在你的项目中使用
def text_to_speech_api(text):
    output_path = f"/tmp/{hash(text)}.wav"
    result = synthesizer.synthesize_text(
        text=text,
        speaker_wav=synthesizer.get_random_voice(),
        output_path=output_path
    )
    
    if result.success:
        return output_path
    else:
        raise Exception(result.error_message)
```

## 7. 性能优化建议

1. **模型复用**：尽量复用已加载的模型，避免频繁加载和卸载
2. **批量处理**：对于大量文本，优先使用批量处理功能
3. **合理设置并发数**：根据系统资源情况，设置适当的最大并发数
4. **定期清理**：对于长时间运行的服务，定期清理不再需要的音频文件
5. **日志级别**：生产环境中可以将日志级别设置为WARNING，减少日志开销