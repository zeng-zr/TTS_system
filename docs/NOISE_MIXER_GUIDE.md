# 噪声混合模块使用指南

本文档详细介绍了DataGen项目中噪声混合模块的功能、使用方法和测试方式。

## 1. 噪声混合模块概述

噪声混合模块（Noise Mixer）的主要功能是将TTS生成的语音与预设的噪声文件混合，以模拟不同环境下的语音效果。该模块支持：

- 选择不同类型的噪声（通过文件名指定）
- 支持随机选择噪声
- 控制信噪比（Signal-to-Noise Ratio, SNR），范围0-20dB
- 自动保存混合后的音频文件到指定目录

## 2. 模块结构

噪声混合模块主要包含两个核心类：

### 2.1 NoiseLibrary类

负责加载和管理噪声文件库：

- 自动加载`data_noise/Noisex92`目录下的所有噪声文件
- 提供按名称或随机获取噪声文件的功能

### 2.2 NoiseMixer类

负责执行噪声混合操作：

- 加载原始音频和噪声文件
- 确保采样率匹配
- 调整噪声长度以匹配音频
- 根据指定的SNR混合音频和噪声
- 保存混合后的音频文件

## 3. 支持的噪声类型

目前，项目提供了以下类型的噪声（位于`data_noise/Noisex92`目录）：

- **babble.wav** - 人声嘈杂背景
- **pink.wav** - 粉噪声（频率与功率成反比）
- **volvo.wav** - 汽车噪声
- **white.wav** - 白噪声（均匀分布的噪声）

## 4. 使用方法

### 4.1 直接使用噪声混合器

```python
from src.modules.noise_mixer import noise_mixer

# 混合噪声，使用默认参数（随机噪声，10dB SNR）
mixed_file = noise_mixer.mix_noise(audio_path="path/to/your/audio.wav")

# 混合指定类型的噪声，设置特定SNR
mixed_file = noise_mixer.mix_noise(
    audio_path="path/to/your/audio.wav",
    noise_type="babble",  # 可以是具体噪声文件名或"random"
    snr_db=5.0  # 信噪比，范围0-20dB
)

if mixed_file:
    print(f"成功生成混合噪声的音频文件: {mixed_file}")
else:
    print("噪声混合失败")
```

### 4.2 使用测试脚本

项目提供了专门的测试脚本，用于批量测试噪声混合功能：

```bash
python tests/noise_mixer_test.py
```

测试脚本会：
1. 从CSV文件读取文本数据
2. 对文本进行TTS合成
3. 为每个合成的语音文件混合多种类型的噪声（默认测试babble、white、pink和随机噪声）
4. 测试不同信噪比（默认5dB、10dB、15dB）
5. 生成详细的日志和meta文件

## 5. 输出文件说明

混合后的音频文件默认保存到`output/tts_with_noise`目录，文件名格式为：

```
{原始文件名}_{噪声类型}_snr{信噪比}_{时间戳}.wav
```

例如：
```
test_output_0_babble_snr5_20250915_143025.wav
```

## 6. 噪声混合的技术细节

### 6.1 信噪比（SNR）计算

信噪比计算公式：

```
SNR(dB) = 10 * log10(信号功率 / 噪声功率)
```

当指定SNR值时，系统会自动计算并调整噪声的增益，以达到所需的信噪比。

### 6.2 噪声处理

- **采样率匹配**：自动将噪声的采样率调整为与目标音频一致
- **长度调整**：如果噪声长度短于音频，则重复噪声；如果噪声长度长于音频，则随机截取一段
- **归一化处理**：混合后的音频会进行归一化，避免音频削波

## 7. 扩展指南

### 7.1 添加新的噪声文件

要添加新的噪声文件，只需将WAV或MP3格式的噪声文件复制到`data_noise/Noisex92`目录中，系统会自动加载并识别这些文件。

### 7.2 集成到现有流程

可以在现有的TTS合成流程中集成噪声混合功能，例如：

```python
from src.tts_synthesizer import TTSSynthesizer
from src.modules.noise_mixer import noise_mixer

# 创建合成器
synthesizer = TTSSynthesizer(output_dir="./output")

# 合成语音
result = synthesizer.synthesize_text(
    text="这是一段测试文本",
    speaker_wav="path/to/speaker.wav",
    output_path="./output/test.wav"
)

# 如果合成成功，混合噪声
if result.success:
    mixed_file = noise_mixer.mix_noise(
        audio_path=result.output_file,
        noise_type="white",
        snr_db=10.0
    )
    print(f"噪声混合完成: {mixed_file}")
```

## 8. 日志和调试

噪声混合模块会生成详细的日志信息，包括：
- 加载的噪声文件信息
- 噪声混合的参数设置
- 处理过程中的错误信息
- 输出文件的保存路径

这些日志可以帮助排查和解决使用过程中遇到的问题。