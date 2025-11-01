import os
import csv
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextLoader:
    """
    文本文件加载模块，支持多种格式的文本文件加载和解析
    """
    def __init__(self):
        """初始化文本加载器"""
        logger.info("TextLoader initialized")
    
    def convert_special_symbols(self, text: str) -> str:
        """
        将文本中的特殊符号转换为中文表达
        
        Args:
            text: 原始文本
            
        Returns:
            转换后的文本
        """
        # 定义符号到中文的映射
        symbol_map = {
            '<': '小于',
            '＜': '小于',
            '>': '大于',
            '＞': '大于',
            '≤': '小于等于',
            '≤': '小于等于',
            '≥': '大于等于',
            '≥': '大于等于',
            '=': '等于',
            '≠': '不等于',
            '≠': '不等于',
            '≈': '约等于',
            '≈': '约等于',
            '±': '正负',
            '±': '正负',
            '×': '乘以',
            '×': '乘以',
            '÷': '除以',
            '÷': '除以',
            '∞': '无穷大',
            '∞': '无穷大',
            '∑': '求和',
            '∑': '求和',
            '∏': '求积',
            '∏': '求积',
            '∫': '积分',
            '∫': '积分',
            '∂': '偏微分',
            '∂': '偏微分',
            '∇': '梯度',
            '∇': '梯度',
            '√': '平方根',
            '√': '平方根',
            '∛': '立方根',
            '∛': '立方根',
            '℃': '摄氏度',
            '℃': '摄氏度',
            '℉': '华氏度',
            '℉': '华氏度',
            '°': '度',
            '°': '度',
            '′': '分',
            '′': '分',
            '″': '秒',
            '″': '秒',
            '％': '百分之',
            '％': '百分之',
            '‰': '千分之',
            '‰': '千分之',
            '‱': '万分之',
            '‱': '万分之'
        }
        
        # 处理范围表示，如 "200-500" -> "200到500"
        text = re.sub(r'(\d+)-(\d+)', r'\1到\2', text)
        
        # 替换特殊符号
        for symbol, replacement in symbol_map.items():
            text = text.replace(symbol, replacement)
        
        # 处理百分比，如 "50%" -> "百分之五十"
        def replace_percent(match):
            num = match.group(1)
            # 如果是整数，尝试转换为中文数字
            try:
                if '.' not in num:
                    # 简单的数字到中文转换，只处理常见情况
                    num_int = int(num)
                    chinese_nums = {
                        0: '零', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 
                        6: '六', 7: '七', 8: '八', 9: '九', 10: '十'
                    }
                    if num_int in chinese_nums:
                        return f"百分之{chinese_nums[num_int]}"
                    # 对于更大的数字，保留阿拉伯数字
                    return f"百分之{num}"
                else:
                    # 小数情况，保留阿拉伯数字
                    return f"百分之{num}"
            except ValueError:
                return f"百分之{num}"
        
        text = re.sub(r'(\d+(?:\.\d+)?)%', replace_percent, text)
        
        return text
    
    def load_text_file(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        加载文本文件并返回解析后的文本列表
        
        Args:
            file_path: 文件路径
            **kwargs: 其他参数，根据文件类型不同而不同
            
        Returns:
            解析后的文本列表，每个元素是一个字典，包含文本和可能的其他信息
        """
        # 获取文件扩展名
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 根据文件扩展名选择不同的加载方法
        if file_ext == '.txt':
            return self._load_txt_file(file_path, **kwargs)
        elif file_ext == '.csv':
            return self._load_csv_file(file_path, **kwargs)
        elif file_ext in ['.xlsx', '.xls']:
            return self._load_excel_file(file_path, **kwargs)
        elif file_ext == '.json':
            return self._load_json_file(file_path, **kwargs)
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _load_txt_file(self, file_path: str, encoding: str = 'utf-8', **kwargs) -> List[Dict[str, Any]]:
        """
        加载TXT文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码，默认为'utf-8'
            **kwargs: 其他参数
            
        Returns:
            解析后的文本列表
        """
        logger.info(f"Loading TXT file: {file_path}")
        texts = []
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                for idx, line in enumerate(f):
                    line = line.strip()
                    if line:
                        # 转换特殊符号
                        processed_line = self.convert_special_symbols(line)
                        texts.append({
                            'id': f'{file_name}_{idx}',
                            'text': processed_line,
                            'original_text': line  # 保留原始文本
                        })
            logger.info(f"Loaded {len(texts)} texts from TXT file")
            return texts
        except Exception as e:
            logger.error(f"Failed to load TXT file: {str(e)}")
            raise
    
    def _load_csv_file(self, file_path: str, text_column: str = 'text', id_column: Optional[str] = None, 
                      encoding: str = 'utf-8', **kwargs) -> List[Dict[str, Any]]:
        """
        加载CSV文件
        
        Args:
            file_path: 文件路径
            text_column: 文本所在的列名，默认为'text'
            id_column: ID所在的列名，默认为None（使用行号作为ID）
            encoding: 文件编码，默认为'utf-8'
            **kwargs: 其他参数
            
        Returns:
            解析后的文本列表
        """
        logger.info(f"Loading CSV file: {file_path}")
        texts = []
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if text_column not in row:
                        raise ValueError(f"Text column '{text_column}' not found in CSV file")
                    
                    text = row[text_column].strip()
                    if text:
                        # 转换特殊符号
                        processed_text = self.convert_special_symbols(text)
                        text_dict = {
                            'text': processed_text,
                            'original_text': text  # 保留原始文本
                        }
                        
                        # 设置ID
                        if id_column and id_column in row:
                            text_dict['id'] = row[id_column]
                        else:
                            text_dict['id'] = f'text_{idx}'
                        
                        # 添加其他列的信息
                        for key, value in row.items():
                            if key not in [text_column, id_column]:
                                text_dict[key] = value
                        
                        texts.append(text_dict)
            logger.info(f"Loaded {len(texts)} texts from CSV file")
            return texts
        except Exception as e:
            logger.error(f"Failed to load CSV file: {str(e)}")
            raise
    
    def _load_excel_file(self, file_path: str, sheet_name: str = 0, text_column: str = 'text', 
                        id_column: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        加载Excel文件
        
        Args:
            file_path: 文件路径
            sheet_name: 工作表名称或索引，默认为0（第一个工作表）
            text_column: 文本所在的列名，默认为'text'
            id_column: ID所在的列名，默认为None（使用行号作为ID）
            **kwargs: 其他参数
            
        Returns:
            解析后的文本列表
        """
        logger.info(f"Loading Excel file: {file_path}")
        texts = []
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 检查文本列是否存在
            if text_column not in df.columns:
                raise ValueError(f"Text column '{text_column}' not found in Excel file")
            
            # 处理每一行
            for idx, row in df.iterrows():
                text = str(row[text_column]).strip()
                if text and text != 'nan':  # 处理空值
                    # 转换特殊符号
                    processed_text = self.convert_special_symbols(text)
                    text_dict = {
                        'text': processed_text,
                        'original_text': text  # 保留原始文本
                    }
                    
                    # 设置ID
                    if id_column and id_column in df.columns:
                        text_dict['id'] = str(row[id_column])
                    else:
                        text_dict['id'] = f'text_{idx}'
                    
                    # 添加其他列的信息
                    for col in df.columns:
                        if col not in [text_column, id_column]:
                            value = row[col]
                            # 转换numpy类型为Python原生类型
                            if hasattr(value, 'item'):
                                value = value.item()
                            text_dict[col] = str(value) if pd.isna(value) else value
                    
                    texts.append(text_dict)
            
            logger.info(f"Loaded {len(texts)} texts from Excel file")
            return texts
        except Exception as e:
            logger.error(f"Failed to load Excel file: {str(e)}")
            raise
    
    def _load_json_file(self, file_path: str, text_key: str = 'text', id_key: Optional[str] = None, 
                       encoding: str = 'utf-8', **kwargs) -> List[Dict[str, Any]]:
        """
        加载JSON文件
        
        Args:
            file_path: 文件路径
            text_key: 文本所在的键名，默认为'text'
            id_key: ID所在的键名，默认为None（使用索引作为ID）
            encoding: 文件编码，默认为'utf-8'
            **kwargs: 其他参数
            
        Returns:
            解析后的文本列表
        """
        logger.info(f"Loading JSON file: {file_path}")
        texts = []
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
                
                # 检查数据格式
                if isinstance(data, dict):
                    # 如果是字典，尝试将其转换为列表
                    if 'items' in data and isinstance(data['items'], list):
                        data = data['items']
                    else:
                        # 否则，将字典作为单个项目处理
                        data = [data]
                
                if not isinstance(data, list):
                    raise ValueError(f"JSON data must be a list or contain a 'items' list")
                
                # 处理每个项目
                for idx, item in enumerate(data):
                    if not isinstance(item, dict):
                        continue  # 跳过非字典项
                    
                    if text_key not in item:
                        continue  # 跳過没有文本键的项
                    
                    text = str(item[text_key]).strip()
                    if text and text != 'nan':
                        # 转换特殊符号
                        processed_text = self.convert_special_symbols(text)
                        text_dict = {
                            'text': processed_text,
                            'original_text': text  # 保留原始文本
                        }
                        
                        # 设置ID
                        if id_key and id_key in item:
                            text_dict['id'] = str(item[id_key])
                        else:
                            text_dict['id'] = f'text_{idx}'
                        
                        # 添加其他键的信息
                        for key, value in item.items():
                            if key not in [text_key, id_key]:
                                text_dict[key] = value
                        
                        texts.append(text_dict)
            
            logger.info(f"Loaded {len(texts)} texts from JSON file")
            return texts
        except Exception as e:
            logger.error(f"Failed to load JSON file: {str(e)}")
            raise
    
    def convert_to_tts_inputs(self, texts: List[Dict[str, Any]], output_dir: str, 
                             speaker_wav: Optional[str] = None, 
                             language: str = 'zh-cn', 
                             model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        将加载的文本转换为TTS输入格式
        
        Args:
            texts: 加载的文本列表
            output_dir: 输出目录
            speaker_wav: 音色参考音频文件路径
            language: 语言代码
            model_name: 模型名称
            
        Returns:
            TTS输入列表
        """
        logger.info(f"Converting {len(texts)} texts to TTS inputs")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        tts_inputs = []
        for text_info in texts:
            # 生成输出文件路径
            text_id = text_info.get('id', f"text_{len(tts_inputs)}")
            output_path = os.path.join(output_dir, f"{text_id}.wav")
            
            # 创建TTS输入
            tts_input = {
                'text': text_info['text'],
                'output_path': output_path,
                'language': language,
                'model_name': model_name,
                **text_info  # 包含其他信息
            }
            
            # 如果提供了speaker_wav，则添加到输入中
            if speaker_wav:
                tts_input['speaker_wav'] = speaker_wav
            
            tts_inputs.append(tts_input)
        
        logger.info(f"Converted {len(texts)} texts to TTS inputs successfully")
        return tts_inputs

# 示例用法
if __name__ == "__main__":
    try:
        loader = TextLoader()
        
        # 示例：假设当前目录下有一个texts.txt文件
        # texts = loader.load_text_file("texts.txt")
        # print(f"Loaded texts: {texts}")
        # 
        # # 转换为TTS输入
        # tts_inputs = loader.convert_to_tts_inputs(
        #     texts, 
        #     output_dir="./output",
        #     speaker_wav="./speaker.wav"
        # )
        # print(f"TTS inputs: {tts_inputs}")
        
    except Exception as e:
        print(f"Error: {str(e)}")