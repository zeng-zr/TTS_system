import os
import random
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceLibrary:
    """
    音色库类，用于管理和选择音色参考音频
    """
    def __init__(self, data_dir: str = "data_voice/seedtts_testset/zh"):
        """
        初始化音色库
        
        Args:
            data_dir: 数据目录，默认为"data_voice/seedtts_testset/zh"
        """
        self.data_dir = data_dir
        self.data_emotion_dir = Path('/Users/ray/work/DataGen/data_voice/emotion')
        self.selected_voice_dir = Path('/Users/ray/work/DataGen/data_voice/selected_voice')
        self.prompt_wavs_dir = os.path.join(data_dir, "prompt-wavs")
        self.wavs_dir = os.path.join(data_dir, "wavs")
        self.meta_file = os.path.join(data_dir, "meta.lst")
        
        # 检查目录是否存在
        if not os.path.exists(self.data_dir):
            logger.error(f"Data directory does not exist: {self.data_dir}")
            raise ValueError(f"Data directory does not exist: {self.data_dir}")
        
        if not os.path.exists(self.prompt_wavs_dir):
            logger.error(f"Prompt wavs directory does not exist: {self.prompt_wavs_dir}")
            raise ValueError(f"Prompt wavs directory does not exist: {self.prompt_wavs_dir}")
        
        if not os.path.exists(self.meta_file):
            logger.error(f"Meta file does not exist: {self.meta_file}")
            raise ValueError(f"Meta file does not exist: {self.meta_file}")
        
        # 加载meta数据
        self.meta_data = self._load_meta_data()
        
        # 获取所有可用的prompt wav文件
        self.available_prompts = self._get_available_prompts()
        
        logger.info(f"VoiceLibrary initialized with {len(self.available_prompts)} available prompts")
    
    def _load_meta_data(self) -> Dict[str, Dict[str, str]]:
        """
        加载meta数据
        
        Returns:
            字典，键为target_wav文件名，值为包含其他信息的字典
        """
        logger.info(f"Loading meta data from {self.meta_file}")
        meta_data = {}
        try:
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 分割行数据，格式为：filename | the text of the prompt | the audio of the prompt | the text to be synthesized | ...
                    parts = line.split('|')
                    if len(parts) < 4:
                        logger.warning(f"Invalid meta line (less than 4 parts): {line}")
                        continue
                    
                    target_wav = parts[0].strip()
                    prompt_text = parts[1].strip()
                    prompt_wav_rel_path = parts[2].strip()
                    target_text = parts[3].strip()
                    
                    # 构建完整的prompt_wav路径
                    prompt_wav = os.path.join(self.data_dir, prompt_wav_rel_path)
                    
                    # 存储数据
                    meta_data[target_wav] = {
                        'prompt_text': prompt_text,
                        'prompt_wav': prompt_wav,
                        'target_text': target_text,
                        'full_line': line
                    }
            
            logger.info(f"Loaded meta data for {len(meta_data)} target wavs")
            return meta_data
        except Exception as e:
            logger.error(f"Failed to load meta data: {str(e)}")
            raise
    
    def _get_available_prompts(self) -> List[str]:
        """
        获取所有可用的prompt wav文件
        
        Returns:
            prompt wav文件路径列表
        """
        prompts = []
        try:
            # 从meta数据中提取所有唯一的prompt_wav
            prompt_wavs = set()
            for info in self.meta_data.values():
                prompt_wav = info['prompt_wav']
                if os.path.exists(prompt_wav):
                    prompt_wavs.add(prompt_wav)
            
            # 转换为列表
            prompts = list(prompt_wavs)
            
            # 如果没有从meta数据中找到足够的prompt wav，尝试直接扫描目录
            if not prompts:
                logger.warning("No prompts found in meta data, scanning directory directly")
                for file in os.listdir(self.prompt_wavs_dir):
                    if file.endswith('.wav'):
                        prompts.append(os.path.join(self.prompt_wavs_dir, file))
            
            logger.info(f"Found {len(prompts)} available prompt wav files")
            return prompts
        except Exception as e:
            logger.error(f"Failed to get available prompts: {str(e)}")
            raise
    
    def get_random_prompt(self) -> str:
        """
        随机选择一个prompt wav文件
        
        Returns:
            随机选择的prompt wav文件路径
        """
        if not self.available_prompts:
            logger.error("No available prompts")
            raise ValueError("No available prompts")
        
        selected_prompt = random.choice(self.available_prompts)
        logger.info(f"Selected random prompt: {selected_prompt}")
        return selected_prompt
    
    def get_prompt_by_name(self, prompt_name: str) -> Optional[str]:
        """
        根据名称获取prompt wav文件
        
        Args:
            prompt_name: prompt名称，可以是文件名或完整路径
            
        Returns:
            prompt wav文件路径，如果未找到则返回None
        """
        # 检查是否是完整路径
        if os.path.isabs(prompt_name) and os.path.exists(prompt_name):
            return prompt_name
        
        # 检查是否是相对于selected_voice_dir的路径
        selected_voice_path = os.path.join(self.selected_voice_dir, prompt_name)
        if os.path.exists(selected_voice_path):
            return selected_voice_path
        
        # 检查是否是相对于prompt_wavs_dir的路径
        prompt_path = os.path.join(self.prompt_wavs_dir, prompt_name)
        if os.path.exists(prompt_path):
            return prompt_path
        
        # 检查是否是相对于data_dir的路径
        prompt_path = os.path.join(self.data_dir, prompt_name)
        if os.path.exists(prompt_path):
            return prompt_path
        
        # 在available_prompts中查找文件名匹配的项
        for prompt in self.available_prompts:
            if os.path.basename(prompt) == prompt_name:
                return prompt
        
        logger.warning(f"Prompt not found: {prompt_name}")
        return None

    def get_emotion_wav(self, prompt_name: str)-> Optional[str]:
        # 检查是否是完整路径
        if os.path.isabs(prompt_name) and os.path.exists(prompt_name):
            return prompt_name
        
        # 检查是否是相对于prompt_wavs_dir的路径
        prompt_path = os.path.join(self.data_emotion_dir , prompt_name)
        if os.path.exists(prompt_path):
            return prompt_path
        
        # 检查是否是相对于data_emotion的路径
        prompt_path = os.path.join(self.data_dir, prompt_name)
        if os.path.exists(prompt_path):
            return prompt_path
        
        # 在available_prompts中查找文件名匹配的项
        for prompt in self.available_prompts:
            if os.path.basename(prompt) == prompt_name:
                return prompt
        
        logger.warning(f"Prompt not found: {prompt_name}")
        return None

    def get_target_wav_for_prompt(self, prompt_wav: str) -> Optional[Tuple[str, str]]:
        """
        为给定的prompt wav找到对应的target wav和target text
        
        Args:
            prompt_wav: prompt wav文件路径
            
        Returns:
            包含(target_wav_path, target_text)的元组，如果未找到则返回None
        """
        # 获取prompt_wav的相对路径（相对于data_dir）
        prompt_wav_rel = os.path.relpath(prompt_wav, self.data_dir)
        
        # 在meta数据中查找匹配的prompt_wav
        for target_wav_name, info in self.meta_data.items():
            if info['prompt_wav'] == prompt_wav or info['prompt_wav'].endswith(prompt_wav) or info['prompt_wav'].endswith(prompt_wav_rel):
                # 构建target_wav的完整路径
                target_wav_path = os.path.join(self.wavs_dir, target_wav_name + ".wav") if not target_wav_name.endswith('.wav') else os.path.join(self.wavs_dir, target_wav_name)
                
                # 检查target_wav文件是否存在
                if not os.path.exists(target_wav_path):
                    logger.warning(f"Target wav file does not exist: {target_wav_path}")
                    # 尝试不添加.wav后缀
                    target_wav_path_without_ext = os.path.splitext(target_wav_path)[0]
                    if os.path.exists(target_wav_path_without_ext):
                        target_wav_path = target_wav_path_without_ext
                    else:
                        # 如果文件不存在，仍然返回信息，但记录警告
                        logger.warning(f"Target wav file not found for prompt: {prompt_wav}")
                        return (None, info['target_text'])
                
                return (target_wav_path, info['target_text'])
        
        logger.warning(f"No target wav found for prompt: {prompt_wav}")
        return None
    
    def get_all_prompts(self) -> List[str]:
        """
        获取所有可用的prompt wav文件
        
        Returns:
            prompt wav文件路径列表
        """
        return self.available_prompts.copy()
    
    def count_available_prompts(self) -> int:
        """
        获取可用的prompt wav文件数量
        
        Returns:
            prompt wav文件数量
        """
        return len(self.available_prompts)
    
    def refresh(self) -> None:
        """
        刷新音色库，重新加载meta数据和可用的prompt wav文件
        """
        logger.info("Refreshing voice library")
        self.meta_data = self._load_meta_data()
        self.available_prompts = self._get_available_prompts()
        logger.info(f"Voice library refreshed with {len(self.available_prompts)} available prompts")

# 创建全局音色库实例，方便应用程序使用
voice_library = VoiceLibrary()

if __name__ == "__main__":
    try:
        # 创建音色库实例
        voice_lib = VoiceLibrary()
        
        # 获取可用prompt数量
        count = voice_lib.count_available_prompts()
        print(f"Available prompts: {count}")
        
        # 随机选择一个prompt
        if count > 0:
            random_prompt = voice_lib.get_random_prompt()
            print(f"Random prompt: {random_prompt}")
            
            # 获取对应的target wav和text
            target_info = voice_lib.get_target_wav_for_prompt(random_prompt)
            if target_info:
                target_wav, target_text = target_info
                print(f"Target wav: {target_wav}")
                print(f"Target text: {target_text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")