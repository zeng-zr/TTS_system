#!/usr/bin/env python3
"""
测试XTTS参数传递是否正确
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入模块
import src.modules.text_loader
import src.modules.voice_library
import src.modules.tts_input
import src.modules.model_manager
from src.tts_synthesizer import TTSSynthesizer

def test_parameter_passing():
    """测试参数传递功能"""
    print("=== 测试XTTS参数传递 ===")
    
    try:
        # 创建合成器实例
        synthesizer = TTSSynthesizer(output_dir="test_output")
        
        # 测试文本
        test_text = "这是一个测试文本，用于验证参数传递功能。"
        
        # 测试音频文件
        speaker_wav = "/Users/ray/work/DataGen/data_voice/seedtts_testset/zh/prompt-wavs/00004501-00000032.wav"
        
        # 输出文件路径
        output_path = "test_output/test_parameter_passing.wav"
        
        print(f"\n1. 测试基本参数传递:")
        print(f"   文本: {test_text}")
        print(f"   参考音频: {speaker_wav}")
        print(f"   输出路径: {output_path}")
        
        # 测试基本参数
        result = synthesizer.synthesize_text(
            text=test_text,
            speaker_wav=speaker_wav,
            output_path=output_path,
            language="zh-cn",
            split_sentences=True
        )
        
        print(f"   结果: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"   处理时间: {result.processing_time:.2f}秒")
        else:
            print(f"   错误信息: {result.error_message}")
        
        # 测试XTTS特定参数
        print(f"\n2. 测试XTTS特定参数传递:")
        
        output_path_xtts = "test_output/test_xtts_params.wav"
        
        result_xtts = synthesizer.synthesize_text(
            text=test_text,
            speaker_wav=speaker_wav,
            output_path=output_path_xtts,
            language="zh-cn",
            split_sentences=True,
            # XTTS特定参数
            temperature=0.7,
            length_penalty=1.2,
            repetition_penalty=1.5,
            top_k=40,
            top_p=0.8,
            speed=1.0,
            emotion="happy"
        )
        
        print(f"   结果: {'成功' if result_xtts.success else '失败'}")
        if result_xtts.success:
            print(f"   处理时间: {result_xtts.processing_time:.2f}秒")
            
            # 检查输入数据中的参数
            input_data = result_xtts.input_data
            if input_data and input_data.additional_params:
                print(f"   传递的参数:")
                for param_name, param_value in input_data.additional_params.items():
                    print(f"     {param_name}: {param_value}")
        else:
            print(f"   错误信息: {result_xtts.error_message}")
        
        # 测试随机参数
        print(f"\n3. 测试随机参数传递:")
        
        output_path_random = "test_output/test_random_params.wav"
        
        result_random = synthesizer.synthesize_text(
            text=test_text,
            speaker_wav=speaker_wav,
            output_path=output_path_random,
            language="zh-cn",
            split_sentences=True,
            # 随机参数
            temperature='random',
            length_penalty='random',
            repetition_penalty='random',
            top_k='random',
            top_p='random',
            speed='random',
            emotion='random'
        )
        
        print(f"   结果: {'成功' if result_random.success else '失败'}")
        if result_random.success:
            print(f"   处理时间: {result_random.processing_time:.2f}秒")
            
            # 检查随机生成的参数值
            input_data = result_random.input_data
            if input_data and input_data.additional_params:
                print(f"   随机生成的参数:")
                for param_name, param_value in input_data.additional_params.items():
                    print(f"     {param_name}: {param_value}")
        else:
            print(f"   错误信息: {result_random.error_message}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parameter_passing()