import os
import time
import logging
import argparse
import random
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入自定义模块
from src.modules.text_loader import TextLoader
from src.modules.voice_library import voice_library
from src.modules.tts_input import TTSInput, TTSSynthesisResult

class TTSSynthesizer:
    def __init__(self, output_dir: str = "output", model_manager=None):
        """
        初始化TTS合成器
        Args:
            output_dir: 输出目录，默认为"output"
            model_manager: 模型管理器实例，如果为None则创建默认实例
        """
        self.output_dir = output_dir
        self.text_loader = TextLoader()
        self.model_manager = model_manager
        
        # 如果没有提供model_manager，则创建一个
        if self.model_manager is None:
            from src.modules.model_manager import ModelManager
            self.model_manager = ModelManager()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载模型（一次加载，多次使用）
        self.tts = self.model_manager.load_model()
        
        logger.info(f"TTSSynthesizer initialized with output directory: {output_dir}")
    
    def _process_param_value(self, param_name: str, param_value: Any, param_range: tuple) -> Any:
        """
        处理参数值，如果是'random'则在指定范围内随机生成
        
        Args:
            param_name: 参数名
            param_value: 参数值或'random'
            param_range: 参数的取值范围 (min, max)
            
        Returns:
            处理后的参数值
        """
        if param_value == 'random':
            if param_name in ['top_k']:
                # 对于整数类型参数
                return random.randint(int(param_range[0]), int(param_range[1]))
            else:
                # 对于浮点数类型参数
                return random.uniform(param_range[0], param_range[1])
        return param_value

    def _preprocess_chinese_text(self, text: str) -> str:
        """
        预处理中文文本，使用BERT-base-chinese分词器进行更精确的文本处理，解决断句问题
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        if not text:
            return text
        
        processed_text = text
        
        try:
            # 尝试使用BERT-base-chinese分词器进行分词
            if hasattr(self.model_manager, 'chinese_tokenizer') and self.model_manager.chinese_tokenizer:
                logger.debug("Using BERT-base-chinese tokenizer for text preprocessing")
                
                # 使用BERT分词器进行分词
                tokens = self.model_manager.chinese_tokenizer.tokenize(text)
                
                # 将分词后的结果重新组合成句子，注意处理标点符号
                temp_text = ""
                for token in tokens:
                    # 处理特殊字符和标点符号
                    if token in ['[UNK]', '[CLS]', '[SEP]', '[PAD]', '[MASK]']:
                        continue
                    # 标点符号前添加空格
                    elif any(p in token for p in ',.!?;:"'):
                        # 处理中文标点
                        for char in token:
                            if char in '，。！？；："':
                                temp_text = temp_text.rstrip() + char + ' '
                            else:
                                temp_text += char
                    # 英文字母和数字前后添加空格
                    elif any(c.isalnum() and not '\u4e00' <= c <= '\u9fff' for c in token):
                        temp_text += ' ' + token + ' '
                    else:
                        temp_text += token
                
                processed_text = temp_text
        except Exception as e:
            logger.warning(f"Failed to use BERT tokenizer for preprocessing: {str(e)}")
            # 如果BERT分词器使用失败，回退到原来的处理方式
            pass
        
        # 确保中文标点符号正确
        processed_text = processed_text.replace('，', ', ').replace('。', '. ')
        processed_text = processed_text.replace('！', '! ').replace('？', '? ')
        processed_text = processed_text.replace('；', '; ').replace('：', ': ')
        
        # 处理英文字母和数字，确保正确发音
        import re
        
        # 处理英文字母
        processed_text = re.sub(r'([a-zA-Z]+)', r' \1 ', processed_text)
        
        # 处理数字
        processed_text = re.sub(r'(\d+)', r' \1 ', processed_text)
        
        # 清理多余的空格
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        logger.debug(f"Text preprocessing: '{text}' -> '{processed_text}'")
        return processed_text
    
    def synthesize_text(self, text: str, speaker_wav: str, output_path: str, 
                       language: str = "zh-cn", split_sentences: bool = True,
                       # XTTS模型参数
                       temperature: Any = 0.65,
                       length_penalty: Any = 1.0,
                       repetition_penalty: Any = 2.0,
                       emotion: Any = "happy",
                       top_k: Any = 50,
                       top_p: Any = 0.8,
                       speed: Any = 1.0) -> TTSSynthesisResult:
        """
        合成单个文本为语音
        
        Args:
            text: 要合成的文本
            speaker_wav: 音色参考音频文件路径
            output_path: 输出文件路径
            language: 语言代码，默认为"zh-cn"
            split_sentences: 是否分割句子，默认为True
            temperature: 自回归模型的softmax温度，默认为0.65
            length_penalty: 应用于自回归解码器的长度惩罚，默认为1.0
            repetition_penalty: 防止自回归解码器在解码期间重复的惩罚，默认为2.0
            top_k: 较低的值会使解码器产生更"可能"（也就是更无聊）的输出，默认为50
            top_p: 较低的值会使解码器产生更"可能"（也就是更无聊）的输出，默认为0.8
            speed: 生成音频的速度比率，默认为1.0
            
        Returns:
            合成结果
        """
        start_time = time.time()
        
        # 处理随机参数
        temperature = self._process_param_value('temperature', temperature, (0.5, 1.0))
        length_penalty = self._process_param_value('length_penalty', length_penalty, (0.5, 2.0))
        repetition_penalty = self._process_param_value('repetition_penalty', repetition_penalty, (1.0, 3.0))
        top_k = self._process_param_value('top_k', top_k, (10, 100))
        top_p = self._process_param_value('top_p', top_p, (0.7, 1.0))
        speed = self._process_param_value('speed', speed, (0.9, 1.1))
        emotion = self._process_param_value('emotion', emotion, ('happy', 'sad', 'angry', 'surprise','neutral'))
        
        # 创建额外参数字典
        additional_params = {
            'temperature': temperature,
            'length_penalty': length_penalty,
            'repetition_penalty': repetition_penalty,
            'top_k': top_k,
            'top_p': top_p,
            'speed': speed,
            'emotion': emotion,
        }
        
        result = TTSSynthesisResult(
            input_data=TTSInput(
                text=text,
                speaker_wav=speaker_wav,
                output_path=output_path,
                language=language,
                split_sentences=split_sentences,
                additional_params=additional_params
            ),
            success=False
        )
        
        try:
            logger.info(f"Synthesizing text to {output_path} with params: {additional_params}")
            
            # 预处理中文文本
            processed_text = self._preprocess_chinese_text(text)
            
            # 执行TTS合成
            # 检查模型是否是XTTS类型，以便正确传递参数
            if hasattr(self.tts, 'tts_to_file'):
                # 如果tts_to_file方法支持这些参数，直接传递
                try:
                    self.tts.tts_to_file(
                        text=processed_text,
                        speaker_wav=speaker_wav,
                        language=language,
                        file_path=output_path,
                        split_sentences=split_sentences,
                        # XTTS特定参数
                        temperature=temperature,
                        length_penalty=length_penalty,
                        repetition_penalty=repetition_penalty,
                        top_k=top_k,
                        top_p=top_p,
                        speed=speed,
                        emotion=emotion,
                        gpt_cond_len= 12, # test 
                    )
                except TypeError:
                    # 如果不支持额外参数，回退到基本调用
                    logger.warning("Model doesn't support additional parameters, using basic call")
                    self.tts.tts_to_file(
                        text=processed_text,
                        speaker_wav=speaker_wav,
                        language=language,
                        file_path=output_path,
                        split_sentences=split_sentences
                    )
            
            # 检查输出文件是否存在
            if os.path.exists(output_path):
                result.success = True
                result.output_file = output_path
                result.processing_time = time.time() - start_time
                logger.info(f"Successfully synthesized text to {output_path} in {result.processing_time:.2f} seconds")
            else:
                raise Exception("Output file was not created")
            
        except Exception as e:
            error_msg = str(e)
            result.error_message = error_msg
            logger.error(f"Failed to synthesize text: {error_msg}")
        
        return result
    
    def process_text_file(self, input_file: str, output_meta_file: str = None, 
                         language: str = "zh-cn", split_sentences: bool = True, 
                         use_same_voice: bool = False,
                         # XTTS模型参数
                         temperature: Any = 0.65,
                         length_penalty: Any = 1.0,
                         repetition_penalty: Any = 2.0,
                         top_k: Any = 50,
                         top_p: Any = 0.8,
                         speed: Any = 1.0,
                         emotion: str = None,
                         selected_speaker_wav: str = None) -> List[TTSSynthesisResult]:
        """
        处理文本文件，将其中的文本转换为语音
        
        Args:
            input_file: 输入文本文件路径
            output_meta_file: 输出meta文件路径，默认为None（自动生成）
            language: 语言代码，默认为"zh-cn"
            split_sentences: 是否分割句子，默认为True
            use_same_voice: 是否对所有文本使用相同的音色，默认为False
            temperature: 自回归模型的softmax温度，默认为0.65
            length_penalty: 应用于自回归解码器的长度惩罚，默认为1.0
            repetition_penalty: 防止自回归解码器在解码期间重复的惩罚，默认为2.0
            top_k: 较低的值会使解码器产生更"可能"（也就是更无聊）的输出，默认为50
            top_p: 较低的值会使解码器产生更"可能"（也就是更无聊）的输出，默认为0.8
            speed: 生成音频的速度比率，默认为1.0
            emotion: 情感类型，如果指定，将使用data_voice/emotion目录下对应的音频作为额外参考
            
        Returns:
            合成结果列表
        """
        logger.info(f"Processing text file: {input_file}")
        
        # 加载文本
        texts = self.text_loader.load_text_file(input_file)
        logger.info(f"Loaded {len(texts)} texts")
        
        # 转换为TTS输入格式
        tts_inputs = self.text_loader.convert_to_tts_inputs(
            texts, 
            output_dir=self.output_dir,
            language=language
        )
        
       # 如果需要使用相同的音色，预先选择一个
       # selected_speaker_wav = selected_speaker_wav
        if use_same_voice and not selected_speaker_wav:
            selected_speaker_wav = voice_library.get_random_prompt()
            logger.info(f"Selected speaker wav for all texts: {selected_speaker_wav}")
        
        # 检查并获取情感音频文件路径
        emotion_wav = None
        if emotion and emotion != 'neutral':
            emotion_wav_path = os.path.join("data_voice", "emotion", f"{emotion}.wav")
            if os.path.exists(emotion_wav_path):
                emotion_wav = emotion_wav_path
                logger.info(f"Found emotion audio file: {emotion_wav}")
            else:
                logger.warning(f"Emotion audio file not found: {emotion_wav_path}")
        
        # 执行合成
        results = []
        for tts_input in tts_inputs:
            # 为每个文本选择一个音色（除非指定使用相同的音色）
            if selected_speaker_wav:
                # 如果指定了音色，使用指定的音色
                speaker_wav = selected_speaker_wav
                logger.info(f"Using selected speaker wav: {speaker_wav}")
            else:
                # 否则使用随机选择的音色
                speaker_wav = voice_library.get_random_prompt()
                logger.info(f"Using random speaker wav: {speaker_wav}")
            
            # 如果有情感音频，使用情感音频和随机选择的音频共同作为参考
            if emotion_wav:
                # 创建一个特殊的输出路径，包含emotion标记
                base_output_path = tts_input['output_path']
                dir_name = os.path.dirname(base_output_path)
                base_name = os.path.basename(base_output_path)
                name_without_ext, ext = os.path.splitext(base_name)
                emotion_output_path = os.path.join(dir_name, f"{name_without_ext}_{emotion}{ext}")

                # 同时使用随机选择的音频和情感音频进行一次合成
                result = self.synthesize_text(
                    text=tts_input['text'],
                    speaker_wav=[speaker_wav, emotion_wav],  # 同时传入随机参考音频和情感参考音频
                    output_path=emotion_output_path,
                    language=language,
                    split_sentences=split_sentences,
                    # XTTS特定参数
                    temperature=temperature,
                    length_penalty=length_penalty,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                    speed=speed,
                    emotion=emotion
                )
                results.append(result)

            else:
                # 没有情感音频，只使用随机选择的音频
                result = self.synthesize_text(
                    text=tts_input['text'],
                    speaker_wav=speaker_wav,
                    output_path=tts_input['output_path'],
                    language=language,
                    split_sentences=split_sentences,
                    # XTTS特定参数
                    temperature=temperature,
                    length_penalty=length_penalty,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                    speed=speed,
                    emotion=emotion or 'neutral'
                )
                results.append(result)
        
        # 生成meta文件
        self._generate_meta_file(results, output_meta_file)
        
        # 统计结果
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        logger.info(f"Text file processing completed: {success_count} succeeded, {failure_count} failed")
        
        return results
    
    def _generate_meta_file(self, results: List[TTSSynthesisResult], output_meta_file: str = None) -> str:
        """
        生成meta文件
        Args:
            results: 合成结果列表
            output_meta_file: 输出meta文件路径，默认为None（自动生成）
        Returns:
            生成的meta文件路径
        """
        # 如果未指定输出meta文件路径，自动生成一个
        if output_meta_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_meta_file = os.path.join(self.output_dir, f"meta_{timestamp}.csv")
        
        logger.info(f"Generating meta file: {output_meta_file}")
        
        # 准备数据
        meta_data = []
        for result in results:
            input_data = result.input_data
            # 获取XTTS参数值（如果有）
            additional_params = input_data.additional_params or {}
            
            meta_row = {
                'text': input_data.text,
                'prompt_wav_path': input_data.speaker_wav,
                'output_audio_path': result.output_file if result.success else '',
                'success': 'Yes' if result.success else 'No',
                'error_message': result.error_message if not result.success else '',
                'processing_time': result.processing_time if result.processing_time else '',
                # XTTS参数
                'temperature': additional_params.get('temperature', ''),
                'length_penalty': additional_params.get('length_penalty', ''),
                'repetition_penalty': additional_params.get('repetition_penalty', ''),
                'top_k': additional_params.get('top_k', ''),
                'top_p': additional_params.get('top_p', ''),
                'speed': additional_params.get('speed', ''),
                'emotion': additional_params.get('emotion', '')
            }
            meta_data.append(meta_row)
        
        # 创建DataFrame并保存为CSV
        df = pd.DataFrame(meta_data)
        df.to_csv(output_meta_file, index=False, encoding='utf-8')
        
        logger.info(f"Meta file generated: {output_meta_file}")
        return output_meta_file

def main():
    """\主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='TTS Text Synthesizer')
    parser.add_argument('--input', type=str, required=True, help='Input text file path (Excel, CSV, TXT, JSON)')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory path')
    parser.add_argument('--output-meta', type=str, help='Output meta file path')
    parser.add_argument('--language', type=str, default='zh-cn', help='Language code (default: zh-cn)')
    parser.add_argument('--no-split-sentences', action='store_true', help='Do not split sentences')
    parser.add_argument('--same-voice', action='store_true', help='Use the same voice for all texts')
    
    # 添加XTTS特定参数
    parser.add_argument('--temperature', type=float, default=0.65, help='XTTS temperature (default: 0.65)')
    parser.add_argument('--length-penalty', type=float, default=1.0, help='XTTS length penalty (default: 1.0)')
    parser.add_argument('--repetition-penalty', type=float, default=2.0, help='XTTS repetition penalty (default: 2.0)')
    parser.add_argument('--top-k', type=int, default=50, help='XTTS top-k (default: 50)')
    parser.add_argument('--top-p', type=float, default=0.8, help='XTTS top-p (default: 0.8)')
    parser.add_argument('--speed', type=float, default=1.0, help='XTTS speed (default: 1.0)')
    parser.add_argument('--random-params', action='store_true', help='Use random parameters for each text')
    
    args = parser.parse_args()
    
    try:
        # 创建TTS合成器
        synthesizer = TTSSynthesizer(output_dir=args.output_dir)
        
        # 处理文本文件
        results = synthesizer.process_text_file(
            input_file=args.input,
            output_meta_file=args.output_meta,
            language=args.language,
            split_sentences=not args.no_split_sentences,
            use_same_voice=args.same_voice,
            # XTTS参数
            temperature='random' if args.random_params else args.temperature,
            length_penalty='random' if args.random_params else args.length_penalty,
            repetition_penalty='random' if args.random_params else args.repetition_penalty,
            top_k='random' if args.random_params else args.top_k,
            top_p='random' if args.random_params else args.top_p,
            speed='random' if args.random_params else args.speed
        )
        
        # 统计结果
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        
        print(f"\nProcessing completed:")
        print(f"  Total texts: {len(results)}")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {failure_count}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        exit(1)
           
if __name__ == "__main__":
    main()