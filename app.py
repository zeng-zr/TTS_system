import os
import sys
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
from typing import List, Dict, Any, Optional
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入自定义模块
from src.tts_synthesizer import TTSSynthesizer
from src.modules.noise_mixer import NoiseMixer, NoiseLibrary
from src.modules.model_manager import ModelManager
from src.modules.text_loader import TextLoader

# 创建Flask应用
app = Flask(__name__)

# 初始化模型管理器、噪声混合器
model_manager = ModelManager()
noise_library = NoiseLibrary()
noise_mixer = NoiseMixer(noise_library)

# 初始化TTS合成器
tts_synthesizer = TTSSynthesizer(model_manager=model_manager)

# 配置上传文件的允许扩展名
ALLOWED_EXTENSIONS = {'txt', 'csv', 'json'}

# 获取当前时间戳用于输出目录
def get_timestamp():
    return datetime.now().strftime("%m%d_%H%M%S")

# 检查文件扩展名是否被允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 创建临时目录用于存储上传的文件
def create_temp_dir():
    temp_dir = tempfile.mkdtemp()
    return temp_dir

# 根路由，提供Web UI界面
@app.route('/')
def index():
    # 读取index.html内容
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webui', 'index.html')
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Web UI文件未找到，请确保webui目录存在并且包含index.html文件"

# 提供静态文件服务
@app.route('/webui/<path:filename>')
def serve_webui_files(filename):
    webui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webui')
    return send_from_directory(webui_dir, filename)

# 提供音频文件下载服务
@app.route('/audio/<path:filename>')
def serve_audio_files(filename):
    # 确保路径安全，防止目录遍历攻击
    safe_path = os.path.normpath(filename)
    if '..' in safe_path:
        return jsonify({'success': False, 'error': 'Invalid file path'})
    
    # 拼接完整路径
    audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), safe_path)
    if not os.path.exists(audio_path):
        return jsonify({'success': False, 'error': 'File not found'})
    
    # 发送文件
    directory = os.path.dirname(audio_path)
    filename = os.path.basename(audio_path)
    return send_from_directory(directory, filename)

# 处理文本转语音请求
@app.route('/api/tts', methods=['POST'])
def tts_api():
    start_time = time.time()
    
    try:
        # 解析请求参数
        data = request.form.to_dict()
        files = request.files
        
        # 处理文本输入
        text = data.get('text', '').strip()
        
        # 处理文件上传
        if 'file' in files and files['file'].filename:
            file = files['file']
            if allowed_file(file.filename):
                temp_dir = create_temp_dir()
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                is_file_input = True
            else:
                return jsonify({'success': False, 'error': '不支持的文件格式，请上传txt、csv或json文件'})
        elif text:
            # 创建临时文本文件
            temp_dir = create_temp_dir()
            file_path = os.path.join(temp_dir, f"input_{get_timestamp()}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            is_file_input = True
        else:
            return jsonify({'success': False, 'error': '请输入文本或上传文件'})
        
        # 创建输出目录
        output_dir = os.path.join(
            'output', 
            'tts_webui',
            f'{get_timestamp()}'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置参数
        emotion = data.get('emotion', 'neutral')
        selected_speaker_wav = data.get('speaker_wav', None)
        
        # 处理音色选择
        if selected_speaker_wav == 'random':
            selected_speaker_wav = None  # 设置为None，让后端使用随机选择
        elif selected_speaker_wav:
            # 构建完整的音色文件路径
            speakers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_voice', 'selected_voice')
            speaker_file_path = os.path.join(speakers_dir, f"{selected_speaker_wav}.wav")
            if os.path.exists(speaker_file_path):
                selected_speaker_wav = speaker_file_path
            else:
                logger.warning(f"音色文件不存在: {speaker_file_path}，将使用随机选择")
                selected_speaker_wav = None
        
        # 如果情绪为neutral，则传入None，表示不使用情绪
        if emotion == 'neutral':
            emotion = None
        
        # 使用已初始化的TTS合成器
        tts_synthesizer.output_dir = output_dir
        
        # 先加载文本内容，用于返回给前端
        text_loader = TextLoader()
        texts = text_loader.load_text_file(file_path)
        text_list = [item['text'] for item in texts]
        
        # 执行TTS合成
        results = tts_synthesizer.process_text_file(
            file_path,
            emotion=emotion,
            selected_speaker_wav=selected_speaker_wav
        )
        
        # 检查结果
        if not isinstance(results, list):
            return jsonify({'success': False, 'error': '语音合成返回了非列表结果'})
        
        # 过滤成功的结果
        success_results = [r for r in results if r.success and hasattr(r, 'output_file') and r.output_file]
        if not success_results:
            error_messages = []
            for r in results:
                if not r.success and hasattr(r, 'error_message'):
                    error_messages.append(r.error_message)
            return jsonify({
                'success': False, 
                'error': '没有成功的语音合成结果',
                'error_details': error_messages
            })
        
        # 提取音频文件路径
        audio_files = []
        for result in success_results:
            # 获取相对路径，用于前端访问
            rel_path = os.path.relpath(result.output_file, os.path.dirname(os.path.abspath(__file__)))
            audio_files.append({
                'path': rel_path,
                'filename': os.path.basename(result.output_file),
                'processing_time': getattr(result, 'processing_time', 0)
            })
        
        total_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'audio_files': audio_files,
            'output_dir': os.path.relpath(output_dir),
            'total_processing_time': round(total_time, 2),
            'success_count': len(success_results),
            'parsed_texts': text_list,
            'total_texts': len(text_list)
        })
        
    except Exception as e:
        logger.error(f"TTS API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 处理噪音混合请求
@app.route('/api/mix-noise', methods=['POST'])
def mix_noise_api():
    try:
        data = request.json
        
        # 验证参数
        if not data or 'audio_path' not in data:
            return jsonify({'success': False, 'error': '缺少音频文件路径'})
        
        audio_path = data['audio_path']
        noise_type = data.get('noise_type', 'white')
        snr = data.get('snr', 10)
        
        # 确保音频文件存在
        full_audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), audio_path)
        if not os.path.exists(full_audio_path):
            return jsonify({'success': False, 'error': '音频文件不存在'})
        
        # 获取输出目录
        output_dir = os.path.dirname(full_audio_path)
        
        # 执行噪音混合并捕获可能的异常
        try:
            noise_mixed = noise_mixer.mix_noise(
                audio_path=full_audio_path,
                noise_type=noise_type,
                snr_db=snr,
                output_dir=output_dir
            )
            
        except Exception as e:
            logger.error(f"噪音混合过程中出错: {str(e)}")
            return jsonify({'success': False, 'error': f'噪音混合过程中出错: {str(e)}'})

        if not noise_mixed:
            return jsonify({'success': False, 'error': '噪音混合失败'})
        
        # 获取相对路径
        rel_path = os.path.relpath(noise_mixed, os.path.dirname(os.path.abspath(__file__)))
        
        return jsonify({
            'success': True,
            'noise_mixed_path': rel_path,
            'noise_mixed_filename': os.path.basename(noise_mixed)
        })
        
    except Exception as e:
        logger.error(f"Mix noise API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 处理随机噪音混合请求
@app.route('/api/mix-random-noise', methods=['POST'])
def mix_random_noise_api():
    try:
        data = request.json
        
        # 验证参数
        if not data or 'audio_path' not in data:
            return jsonify({'success': False, 'error': '缺少音频文件路径'})
        
        audio_path = data['audio_path']
        snr = data.get('snr', 10)
        count = data.get('count', 1)  # 默认生成1个随机噪声混合文件
        
        # 确保音频文件存在
        full_audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), audio_path)
        if not os.path.exists(full_audio_path):
            return jsonify({'success': False, 'error': '音频文件不存在'})
        
        # 获取输出目录
        output_dir = os.path.dirname(full_audio_path)
        
        # 执行随机噪音混合并捕获可能的异常
        try:
            noise_mixed_files = noise_mixer.mix_random_noise(
                audio_path=full_audio_path,
                snr_db=snr,
                output_dir=output_dir,
                count=count
            )
            
        except Exception as e:
            logger.error(f"随机噪音混合过程中出错: {str(e)}")
            return jsonify({'success': False, 'error': f'随机噪音混合过程中出错: {str(e)}'})

        if not noise_mixed_files:
            return jsonify({'success': False, 'error': '随机噪音混合失败'})
        
        # 获取相对路径
        rel_paths = [os.path.relpath(file, os.path.dirname(os.path.abspath(__file__))) for file in noise_mixed_files]
        
        return jsonify({
            'success': True,
            'noise_mixed_paths': rel_paths,
            'noise_mixed_files': [os.path.basename(file) for file in noise_mixed_files],
            'count': len(noise_mixed_files)
        })
        
    except Exception as e:
        logger.error(f"Mix random noise API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 获取可用的情绪列表
@app.route('/api/emotions', methods=['GET'])
def get_emotions():
    try:
        emotions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_voice', 'emotion')
        emotions = []
        
        if os.path.exists(emotions_dir):
            for file in os.listdir(emotions_dir):
                if file.endswith('.wav'):
                    emotion_name = os.path.splitext(file)[0]
                    emotions.append(emotion_name)
        
        default_emotions = ['neutral', 'happy', 'sad', 'angry', 'surprise']
        final_emotions = []
        # 第一步：添加默认情绪列表中的情绪（确保顺序和中性情绪存在）
        for emotion in default_emotions:
            if emotion in emotions or emotion == 'neutral':  # 确保中性情绪始终存在
                final_emotions.append(emotion)
        # 第二步：添加目录中存在的其他情绪（不在默认列表中的）
        for emotion in emotions:
            if emotion not in final_emotions:
                final_emotions.append(emotion)
        
        # 如果没有任何情绪文件，使用默认列表
        if not final_emotions:
            final_emotions = default_emotions
        
        return jsonify({'success': True, 'emotions': final_emotions})
        
    except Exception as e:
        logger.error(f"Get emotions error: {str(e)}")
        # 返回默认情绪列表
        return jsonify({'success': True, 'emotions': ['neutral', 'happy', 'sad', 'angry', 'surprise']})

# 获取可用的音色列表
@app.route('/api/speakers', methods=['GET'])
def get_speakers():
    try:
        speakers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_voice', 'selected_voice')
        speakers = []
        
        # 添加随机选项
        speakers.append({'value': 'random', 'display_name': '随机选择'})
        
        if os.path.exists(speakers_dir):
            for file in os.listdir(speakers_dir):
                if file.endswith('.wav'):
                    speaker_name = os.path.splitext(file)[0]
                    # 根据文件名生成显示名称
                    display_name = get_speaker_display_name(speaker_name)
                    speakers.append({
                        'value': speaker_name,
                        'display_name': display_name
                    })
        
        # 如果没有找到任何音色文件，添加默认选项
        if len(speakers) == 1:  # 只有随机选项
            speakers.append({'value': 'female_1', 'display_name': '女声1号'})
        
        return jsonify({'success': True, 'speakers': speakers})
        
    except Exception as e:
        logger.error(f"Get speakers error: {str(e)}")
        # 返回默认音色列表
        return jsonify({'success': True, 'speakers': [
            {'value': 'random', 'display_name': '随机选择'},
            {'value': 'female_1', 'display_name': '女声1号'}
        ]})

# 解析上传的文件内容
@app.route('/api/parse-file', methods=['POST'])
def parse_file_api():
    """解析上传的文件并返回文本内容"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        # 检查文件类型
        allowed_extensions = {'.txt', '.csv', '.json', '.xlsx', '.xls'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': f'不支持的文件类型: {file_ext}。支持的文件类型: {list(allowed_extensions)}'
            }), 400
        
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        file.save(temp_file_path)
        
        try:
            # 使用TextLoader解析文件
            text_loader = TextLoader()
            texts = text_loader.load_text_file(temp_file_path)
            
            # 提取文本内容
            text_list = [item['text'] for item in texts]
            
            return jsonify({
                'success': True,
                'texts': text_list,
                'total_texts': len(text_list)
            })
            
        except Exception as e:
            logging.error(f'文件解析错误: {str(e)}')
            return jsonify({
                'success': False, 
                'error': f'文件解析失败: {str(e)}'
            }), 500
            
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                logging.warning(f'临时文件清理失败: {str(e)}')
                
    except Exception as e:
        logging.error(f'文件解析API错误: {str(e)}')
        return jsonify({
            'success': False, 
            'error': f'服务器内部错误: {str(e)}'
        }), 500

# 获取音色显示名称
import re
def get_speaker_display_name(speaker_name):
    """根据音色文件名生成友好的显示名称"""
    # 保留主要描述
    #clean_name = re.sub(' ', speaker_name).strip()
    
    # 根据常见模式生成显示名称
    if 'female' in speaker_name.lower():
        # 提取女性编号
        match = re.search(r'female[_-]?(\d+)', speaker_name.lower())
        if match:
            return f'女声{match.group(1)}号'
        else:
            return '女声'
    elif 'male' in speaker_name.lower():
        # 提取男性编号
        match = re.search(r'male[_-]?(\d+)', speaker_name.lower())
        if match:
            return f'男声{match.group(1)}号'
        else:
            return '男声'
    else:
        # 通用处理
        # if clean_name:
        #     return clean_name.title()
        # else:
        return speaker_name

# 获取可用的噪音类型列表
@app.route('/api/noise-types', methods=['GET'])
def get_noise_types():
    try:
        base_noise_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_noise')
        noise_types = []
        
        # 递归扫描所有子目录中的.wav文件
        def scan_noise_files(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.wav'):
                        # 获取相对路径作为噪音类型标识
                        rel_path = os.path.relpath(os.path.join(root, file), base_noise_dir)
                        # 使用文件名（不含扩展名）作为噪音类型
                        noise_type = os.path.splitext(file)[0]
                        noise_types.append(noise_type)
        
        if os.path.exists(base_noise_dir):
            scan_noise_files(base_noise_dir)

        default_noise_types = ['none', 'white', 'pink', 'babble', 'volvo']
        # 合并实际存在的噪音类型和默认类型，去重并保持默认顺序
        final_noise_types = []
        for noise_type in default_noise_types:
            if noise_type in noise_types or noise_type == 'none':  # 确保无噪音选项始终存在
                final_noise_types.append(noise_type)
        
        # 添加其他发现的噪音类型
        for noise_type in noise_types:
            if noise_type not in final_noise_types:
                final_noise_types.append(noise_type)
        
        # 如果没有任何噪音文件，使用默认列表
        if not final_noise_types:
            final_noise_types = default_noise_types
        
        return jsonify({'success': True, 'noise_types': final_noise_types})
        
    except Exception as e:
        logger.error(f"Get noise types error: {str(e)}")
        return jsonify({'success': True, 'noise_types': ['none', 'white', 'pink', 'babble', 'volvo']})

if __name__ == '__main__':
    webui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webui')
    os.makedirs(webui_dir, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5001, debug=True) #Flask