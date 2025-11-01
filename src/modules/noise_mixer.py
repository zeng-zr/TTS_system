import os
import random
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NoiseLibrary:
    def __init__(self, noise_dir: str="data_noise"):
        self.noise_dir = Path(noise_dir)
        self.noises = []
        self.load_noises()

    def load_noises(self):
        if not self.noise_dir.exists():
            logger.warning(f"Noise directory not found: {self.noise_dir}")
            return
        
        # 递归扫描所有子目录中的音频文件
        for root, dirs, files in os.walk(self.noise_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in ['.wav', '.mp3']:
                    self.noises.append(file_path)
        
        logger.info(f"Loaded {len(self.noises)} noise files from {self.noise_dir} (including subdirectories)")
        
    def get_noise_file(self, noise_type: str = 'random') -> Optional[Path]:
        """
        获取指定类型的噪声文件
        
        Args:
            noise_type: 噪声类型，文件名、'random'或'random_from_list'
            
        Returns:
            噪声文件路径，如果找不到则返回None
        """
        if not self.noises:
            logger.warning("No noise files available")
            return None
        
        if noise_type == 'random' or noise_type == 'random_from_list':
            # 从所有可用噪声文件中随机选择一个
            selected_noise = random.choice(self.noises)
            logger.info(f"Randomly selected noise file: {selected_noise.name}")
            return selected_noise
        
        # 尝试按文件名查找噪声文件
        for noise_file in self.noises:
            if noise_file.stem == noise_type:
                return noise_file
        
        logger.warning(f"Noise type '{noise_type}' not found")
        return None
    
    def get_random_noise_files(self, count: int = 1) -> List[Path]:
        """
        随机获取指定数量的噪声文件
        
        Args:
            count: 要获取的噪声文件数量
            
        Returns:
            随机噪声文件路径列表
        """
        if not self.noises:
            logger.warning("No noise files available")
            return []
        
        # 确保请求数量不超过可用文件数量
        count = min(count, len(self.noises))
        
        # 随机选择指定数量的噪声文件
        selected_noises = random.sample(self.noises, count)
        logger.info(f"Randomly selected {count} noise files: {[f.name for f in selected_noises]}")
        
        return selected_noises

class NoiseMixer:
    """
    噪声混合器，用于将噪声与语音混合
    """
    def __init__(self, noise_library: NoiseLibrary = None):
        """
        初始化噪声混合器
        
        Args:
            noise_library: 噪声库实例，如果为None则创建默认实例
        """
        self.noise_library = noise_library or NoiseLibrary()
        
    def mix_noise(self, audio_path: str, noise_type: str = 'random', snr_db: float = 10.0, output_dir = None) -> Optional[str]:
        """
        将噪声与语音混合
        
        Args:
            audio_path: 原始音频文件路径
            noise_type: 噪声类型，文件名、'random'或'random_from_list'
            snr_db: 信噪比(dB)，范围0-20
            
        Returns:
            混合后的音频文件路径，如果混合失败则返回None
        """
        # 验证SNR值在有效范围内
        if snr_db < 0 or snr_db > 20:
            logger.warning(f"SNR value {snr_db} is out of range [0, 20], using default 10dB")
            snr_db = 10.0
        
        # 加载原始音频
        try:
            audio_data, sr = librosa.load(audio_path, sr=None)
            logger.info(f"Loaded audio file: {audio_path}, sample rate: {sr}")
        except Exception as e:
            logger.error(f"Failed to load audio file {audio_path}: {str(e)}")
            return None
        
        # 获取噪声文件
        noise_file = self.noise_library.get_noise_file(noise_type)
        if not noise_file:
            logger.error("No noise file available for mixing")
            return None
        
        # 加载噪声文件
        try:
            noise_data, noise_sr = librosa.load(noise_file, sr=None)
            logger.info(f"Loaded noise file: {noise_file}, sample rate: {noise_sr}")
        except Exception as e:
            logger.error(f"Failed to load noise file {noise_file}: {str(e)}")
            return None
        
        # 确保噪声和音频具有相同的采样率
        if noise_sr != sr:
            noise_data = librosa.resample(noise_data, orig_sr=noise_sr, target_sr=sr)
            logger.info(f"Resampled noise to match audio sample rate: {sr}")
        
        # 调整噪声长度以匹配音频
        if len(noise_data) < len(audio_data):
            # 如果噪声太短，重复噪声
            repeat_factor = (len(audio_data) // len(noise_data)) + 1
            noise_data = np.tile(noise_data, repeat_factor)[:len(audio_data)]
        else:
            # 如果噪声太长，随机截取一段
            start_idx = random.randint(0, len(noise_data) - len(audio_data))
            noise_data = noise_data[start_idx:start_idx + len(audio_data)]
        
        # 计算SNR并混合
        try:
            mixed_audio = self._apply_snr(audio_data, noise_data, snr_db)
            logger.info(f"Mixed audio with noise '{noise_file.stem}' at {snr_db}dB SNR")
        except Exception as e:
            logger.error(f"Failed to mix audio with noise: {str(e)}")
            return None
        
        # 生成输出路径
        output_dir = output_dir or Path("output/tts_with_noise")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名，包含噪声种类、信噪比和日期时间
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(audio_path).stem
        noise_name = noise_file.stem
        output_file = Path(output_dir) / f"{base_name}_{noise_name}_snr{int(snr_db)}_{timestamp}.wav"
        
        # 保存混合后的音频
        try:
            sf.write(str(output_file), mixed_audio, sr)
            logger.info(f"Saved mixed audio to: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Failed to save mixed audio to {output_file}: {str(e)}")
            return None
    
    def mix_random_noise(self, audio_path: str, snr_db: float = 10.0, output_dir = None, count: int = 1) -> List[str]:
        """
        使用随机噪声与语音混合，可生成多个不同噪声的混合结果
        
        Args:
            audio_path: 原始音频文件路径
            snr_db: 信噪比(dB)，范围0-20
            output_dir: 输出目录
            count: 要生成的混合文件数量
            
        Returns:
            混合后的音频文件路径列表
        """
        # 验证SNR值在有效范围内
        if snr_db < 0 or snr_db > 20:
            logger.warning(f"SNR value {snr_db} is out of range [0, 20], using default 10dB")
            snr_db = 10.0
        
        # 加载原始音频
        try:
            audio_data, sr = librosa.load(audio_path, sr=None)
            logger.info(f"Loaded audio file: {audio_path}, sample rate: {sr}")
        except Exception as e:
            logger.error(f"Failed to load audio file {audio_path}: {str(e)}")
            return []
        
        # 获取随机噪声文件
        noise_files = self.noise_library.get_random_noise_files(count)
        if not noise_files:
            logger.error("No noise files available for mixing")
            return []
        
        # 生成输出路径
        output_dir = output_dir or Path("output/tts_with_noise")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名前缀
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(audio_path).stem
        
        mixed_files = []
        
        # 对每个噪声文件进行混合
        for i, noise_file in enumerate(noise_files):
            try:
                # 加载噪声文件
                noise_data, noise_sr = librosa.load(noise_file, sr=None)
                logger.info(f"Loaded noise file: {noise_file}, sample rate: {noise_sr}")
                
                # 确保噪声和音频具有相同的采样率
                if noise_sr != sr:
                    noise_data = librosa.resample(noise_data, orig_sr=noise_sr, target_sr=sr)
                    logger.info(f"Resampled noise to match audio sample rate: {sr}")
                
                # 调整噪声长度以匹配音频
                if len(noise_data) < len(audio_data):
                    # 如果噪声太短，重复噪声
                    repeat_factor = (len(audio_data) // len(noise_data)) + 1
                    noise_data = np.tile(noise_data, repeat_factor)[:len(audio_data)]
                else:
                    # 如果噪声太长，随机截取一段
                    start_idx = random.randint(0, len(noise_data) - len(audio_data))
                    noise_data = noise_data[start_idx:start_idx + len(audio_data)]
                
                # 计算SNR并混合
                mixed_audio = self._apply_snr(audio_data, noise_data, snr_db)
                logger.info(f"Mixed audio with noise '{noise_file.stem}' at {snr_db}dB SNR")
                
                # 生成输出文件名
                noise_name = noise_file.stem
                output_file = Path(output_dir) / f"{base_name}_{noise_name}_snr{int(snr_db)}_{timestamp}_{i+1}.wav"
                
                # 保存混合后的音频
                sf.write(str(output_file), mixed_audio, sr)
                logger.info(f"Saved mixed audio to: {output_file}")
                mixed_files.append(str(output_file))
                
            except Exception as e:
                logger.error(f"Failed to mix audio with noise {noise_file}: {str(e)}")
                continue
        
        return mixed_files
    
    def _apply_snr(self, signal: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
        """
        根据指定的SNR将噪声与信号混合
        
        Args:
            signal: 原始信号
            noise: 噪声信号
            snr_db: 信噪比(dB)
            
        Returns:
            混合后的信号
        """
        # 计算信号和噪声的功率
        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)
        
        # 计算所需的噪声缩放因子
        snr_ratio = 10 ** (snr_db / 10)
        scale_factor = np.sqrt(signal_power / (snr_ratio * noise_power + 1e-10))
        
        # 混合信号和噪声
        mixed_signal = signal + noise * scale_factor
        
        # 归一化以避免削波
        max_val = np.max(np.abs(mixed_signal))
        if max_val > 1.0:
            mixed_signal = mixed_signal / max_val
        
        return mixed_signal

# 创建全局噪声混合器实例
noise_mixer = NoiseMixer()