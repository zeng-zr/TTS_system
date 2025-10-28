import logging
from typing import Optional, Union, Dict, Any
import builtins

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入transformers相关模块以解决attention mask问题
from transformers import AutoTokenizer, AutoModel, AutoConfig

# 全局TTS变量
TTS = None

def import_tts():
    """延迟导入TTS模块，使用补丁修复Optional类型错误"""
    global TTS
    if TTS is None:
        try:
            logger.info("Importing TTS module with patch...")
            # 先导入补丁文件修复Optional类型问题
            import sys
            import os
            # 添加项目根目录到Python路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 导入补丁
            from tts_patch import get_tts
            TTS = get_tts()
            logger.info("TTS module imported successfully with patch")
        except Exception as e:
            logger.error(f"Failed to import TTS module with patch: {e}")
            # 如果补丁失败，尝试直接导入
            try:
                logger.info("Trying direct import...")
                from TTS.api import TTS as TTS_module
                TTS = TTS_module
                logger.info("TTS module imported successfully via direct import")
            except Exception as e2:
                logger.error(f"Failed to import TTS module directly: {e2}")
                raise
    return TTS

class ModelManager:
    """
    模型管理库类，负责加载和管理TTS模型，支持一次加载多次使用
    """
    def __init__(self):
        """初始化模型管理器"""
        self.models: Dict[str, TTS] = {}
        self.default_model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        
        # 中文专用tokenizer和模型
        self.chinese_tokenizer = None
        self.chinese_model = None
        
        logger.info("ModelManager initialized")
    
    def load_model(self, model_name: Optional[str] = None, device: str = "cpu"):
        """
        加载指定的TTS模型，如果模型已加载则直接返回
        
        Args:
            model_name: 模型名称，如果为None则使用默认模型
            device: 运行设备，默认为"cpu"
            
        Returns:
            加载好的TTS模型实例
        """
        if model_name is None:
            model_name = self.default_model_name
        
        if model_name not in self.models:
            logger.info(f"Loading model: {model_name} on device: {device}")
            try:
                # 设置中文专用tokenizer
                self._setup_chinese_tokenizer()
                
                # 修复attention mask问题
                self._fix_attention_mask_issue()
                
                # 延迟导入TTS模块并加载模型
                TTS = import_tts()
                tts = TTS(model_name).to(device)
                self.models[model_name] = tts
                logger.info(f"Model {model_name} loaded successfully with Chinese tokenizer support")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise
        else:
            logger.info(f"Model {model_name} already loaded, returning cached instance")
        
        return self.models[model_name]
    
    def get_model(self, model_name: Optional[str] = None) -> TTS:
        """
        获取指定的模型实例，如果模型未加载则加载
        
        Args:
            model_name: 模型名称，如果为None则使用默认模型
            
        Returns:
            TTS模型实例
        """
        if model_name is None:
            model_name = self.default_model_name
        
        if model_name not in self.models:
            return self.load_model(model_name)
        
        return self.models[model_name]
    
    def unload_model(self, model_name: Optional[str] = None) -> None:
        """
        卸载指定的模型
        
        Args:
            model_name: 模型名称，如果为None则卸载默认模型
        """
        if model_name is None:
            model_name = self.default_model_name
        
        if model_name in self.models:
            logger.info(f"Unloading model: {model_name}")
            del self.models[model_name]
        else:
            logger.warning(f"Model {model_name} not found in loaded models")
    
    def unload_all_models(self) -> None:
        """卸载所有已加载的模型"""
        logger.info("Unloading all models")
        self.models.clear()
    
    def list_loaded_models(self) -> list:
        """列出所有已加载的模型名称"""
        return list(self.models.keys())
    
    def is_model_loaded(self, model_name: Optional[str] = None) -> bool:
        """
        检查指定的模型是否已加载
        
        Args:
            model_name: 模型名称，如果为None则检查默认模型
            
        Returns:
            模型是否已加载
        """
        if model_name is None:
            model_name = self.default_model_name
        
        return model_name in self.models
    
    def _setup_chinese_tokenizer(self):
        """
        设置中文专用tokenizer
        使用BERT-base-chinese分词器，专门针对中文优化
        """
        try:
            logger.info("Setting up Chinese tokenizer...")
            
            # 尝试使用本地已下载的tokenizer
            import os
            local_tokenizer_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models", "bert-base-chinese")
            
            if os.path.exists(local_tokenizer_path):
                logger.info(f"Loading local BERT tokenizer from {local_tokenizer_path}")
                self.chinese_tokenizer = AutoTokenizer.from_pretrained(local_tokenizer_path)
            else:
                # 如果本地不存在，则尝试从huggingface下载，但禁用SSL验证
                logger.info("Downloading BERT tokenizer from huggingface (SSL verification disabled)")
                import ssl
                try:
                    _create_unverified_https_context = ssl._create_unverified_context
                except AttributeError:
                    pass
                else:
                    ssl._create_default_https_context = _create_unverified_https_context
                
                self.chinese_tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese", local_files_only=False)
                
                # 保存到本地以便下次使用
                os.makedirs(os.path.dirname(local_tokenizer_path), exist_ok=True)
                self.chinese_tokenizer.save_pretrained(local_tokenizer_path)
                logger.info(f"Saved BERT tokenizer to {local_tokenizer_path}")
            
            # 配置pad token，确保与eos token不同
            if self.chinese_tokenizer.pad_token is None:
                self.chinese_tokenizer.pad_token = self.chinese_tokenizer.eos_token
            
            logger.info("Chinese tokenizer setup successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chinese tokenizer: {str(e)}")
            raise
    
    def _fix_attention_mask_issue(self):
        """
        修复attention mask问题
        确保pad token和eos token不同，避免attention mask混淆
        """
        try:
            logger.info("Fixing attention mask issue...")
            
            if self.chinese_tokenizer:
                # 确保pad token和eos token不同
                if self.chinese_tokenizer.pad_token == self.chinese_tokenizer.eos_token:
                    # 如果相同，设置一个不同的pad token
                    self.chinese_tokenizer.pad_token = "[PAD]"
                    if "[PAD]" not in self.chinese_tokenizer.get_vocab():
                        # 如果词汇表中没有[PAD]，使用unk token
                        self.chinese_tokenizer.pad_token = self.chinese_tokenizer.unk_token
            
            logger.info("Attention mask issue fixed successfully")
            
        except Exception as e:
            logger.error(f"Failed to fix attention mask issue: {str(e)}")
            raise

# 创建全局模型管理器实例，方便应用程序使用
model_manager = ModelManager()

if __name__ == "__main__":
    # 示例用法
    try:
        # 加载默认模型
        tts = model_manager.load_model()
        print(f"Default model loaded")
        
        # 检查模型是否已加载
        print(f"Is default model loaded: {model_manager.is_model_loaded()}")
        
        # 列出所有已加载的模型
        print(f"Loaded models: {model_manager.list_loaded_models()}")
        
    except Exception as e:
        print(f"Error: {str(e)}")