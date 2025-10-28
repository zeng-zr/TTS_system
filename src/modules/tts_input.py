from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class TTSInput:
    """
    TTS模型的输入数据结构，包含所有需要传递给TTS模型的参数
    """
    # 要合成语音的文本
    text: str
    
    # 音色参考音频文件路径
    speaker_wav: str
    
    # 输出文件路径
    output_path: str
    
    # 语言代码，默认为中文
    language: str = "zh-cn"
    
    # 模型名称，默认为None（使用默认模型）
    model_name: Optional[str] = None
    
    # 是否分割句子（对于长文本可能有用）
    split_sentences: bool = True
    
    # 其他可选参数，用于扩展
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后的验证和处理"""
        # 验证文本不为空
        if not self.text or not self.text.strip():
            raise ValueError("Text cannot be empty")
        
        # 验证文件路径格式（这里只是简单检查，实际使用时可以更严格）
        if not self.speaker_wav:
            raise ValueError("Speaker wav file path cannot be empty")
        
        if not self.output_path:
            raise ValueError("Output file path cannot be empty")

@dataclass
class TTSBatchInput:
    """
    批量TTS输入的数据结构，包含多个TTSInput实例
    """
    # 批量输入列表
    inputs: List[TTSInput]
    
    # 批处理的最大并发数，默认为1（不并行）
    max_concurrency: int = 1
    
    def __post_init__(self):
        """初始化后的验证和处理"""
        if not self.inputs:
            raise ValueError("Inputs list cannot be empty")
        
        if self.max_concurrency < 1:
            raise ValueError("Max concurrency must be at least 1")

@dataclass
class TTSSynthesisResult:
    """
    TTS合成结果的数据结构
    """
    # 对应的输入
    input_data: TTSInput
    
    # 是否成功
    success: bool
    
    # 错误信息，如果有的话
    error_message: Optional[str] = None
    
    # 输出文件路径
    output_file: Optional[str] = None
    
    # 处理时间（秒）
    processing_time: Optional[float] = None

@dataclass
class TTSBatchResult:
    """
    批量TTS合成结果的数据结构
    """
    # 单个处理结果列表
    results: List[TTSSynthesisResult]
    
    # 总处理时间（秒）
    total_processing_time: Optional[float] = None
    
    # 成功的数量
    success_count: int = 0
    
    # 失败的数量
    failure_count: int = 0
    
    def __post_init__(self):
        """初始化后的计算"""
        self.success_count = sum(1 for result in self.results if result.success)
        self.failure_count = len(self.results) - self.success_count

# 示例用法
if __name__ == "__main__":
    try:
        # 创建单个TTS输入
        tts_input = TTSInput(
            text="你好，这是一个测试文本。",
            speaker_wav="/path/to/speaker.wav",
            output_path="/path/to/output.wav",
            language="zh-cn"
        )
        print(f"TTSInput created: {tts_input}")
        """
        # 创建批量输入
        batch_input = TTSBatchInput(
            inputs=[tts_input],
            max_concurrency=2
        )
        print(f"TTSBatchInput created: {batch_input}")
        """
    except Exception as e:
        print(f"Error: {str(e)}")