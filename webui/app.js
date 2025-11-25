// 全局变量存储当前合成结果
let currentResults = null;

// 用于取消请求的AbortController
let currentAbortController = null;

// 跟踪当前是否正在进行合成
let isSynthesizing = false;

// 存储当前输出目录
let currentOutputDir = null;

// DOM元素引用
const elements = {
    inputText: document.getElementById('input-text'),
    fileUpload: document.getElementById('file-upload'),
    fileName: document.getElementById('file-name'),
    speaker: document.getElementById('speaker'),
    emotion: document.getElementById('emotion'),
    noiseType: document.getElementById('noise-type'),
    snr: document.getElementById('snr'),
    snrValue: document.getElementById('snr-value'),
    randomNoise: document.getElementById('random-noise'),
    randomNoiseCount: document.getElementById('random-noise-count'),
    randomNoiseCountValue: document.getElementById('random-noise-count-value'),
    randomNoiseCountGroup: document.getElementById('random-noise-count-group'),
    speed: document.getElementById('speed'),
    speedValue: document.getElementById('speed-value'),
    temperature: document.getElementById('temperature'),
    temperatureValue: document.getElementById('temperature-value'),
    topK: document.getElementById('top-k'),
    topKValue: document.getElementById('top-k-value'),
    synthesizeBtn: document.getElementById('synthesize-btn'),
    resetParamsBtn: document.getElementById('reset-params-btn'),
    clearBtn: document.getElementById('clear-btn'),
    cancelJobBtn: document.getElementById('cancel-job-btn'),
    statusMessage: document.getElementById('status-message'),
    processingTime: document.getElementById('processing-time'),
    totalTime: document.getElementById('total-time'),
    originalAudioContainer: document.getElementById('original-audio-container'),
    originalAudioList: document.getElementById('original-audio-list'),
    noiseAudioContainer: document.getElementById('noise-audio-container'),
    noiseAudioList: document.getElementById('noise-audio-list'),
    batchDownloadAll: document.getElementById('batch-download-all')
};

// 初始化页面
function init() {
    // 设置滑块事件监听
    setupSliderListeners();
    
    // 设置按钮事件监听
    setupButtonListeners();
    
    // 设置文件上传事件监听
    setupFileUploadListener();
    
    // 加载可用的情绪和噪音类型
    loadEmotionsAndNoiseTypes();
    
    // 设置工具提示
    setupTooltips();
}

// 设置工具提示
function setupTooltips() {
    // 为所有信息图标添加工具提示功能
    const infoIcons = document.querySelectorAll('.info-icon');
    
    infoIcons.forEach(icon => {
        const tooltipText = icon.getAttribute('data-tooltip');
        
        // 创建工具提示元素
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        // 创建容器
        const container = document.createElement('div');
        container.className = 'param-info';
        
        // 将图标和工具提示放入容器
        icon.parentNode.insertBefore(container, icon);
        container.appendChild(icon);
        container.appendChild(tooltip);
    });
}

// 设置滑块事件监听
function setupSliderListeners() {
    elements.snr.addEventListener('input', () => {
        elements.snrValue.textContent = `${elements.snr.value} dB`;
    });
    
    // 随机噪声复选框事件
    elements.randomNoise.addEventListener('change', () => {
        if (elements.randomNoise.checked) {
            elements.randomNoiseCountGroup.style.display = 'block';
            elements.noiseType.disabled = true;
        } else {
            elements.randomNoiseCountGroup.style.display = 'none';
            elements.noiseType.disabled = false;
        }
    });
    
    // 随机噪声数量滑块
    elements.randomNoiseCount.addEventListener('input', () => {
        elements.randomNoiseCountValue.textContent = elements.randomNoiseCount.value;
    });
    
    elements.speed.addEventListener('input', () => {
        elements.speedValue.textContent = `${elements.speed.value}x`;
    });
    
    elements.temperature.addEventListener('input', () => {
        elements.temperatureValue.textContent = elements.temperature.value;
    });
    
    elements.topK.addEventListener('input', () => {
        elements.topKValue.textContent = elements.topK.value;
    });
    
    // Top-P滑块
    const topPSlider = document.getElementById('top-p');
    const topPValue = document.getElementById('top-p-value');
    
    if (topPSlider && topPValue) {
        topPSlider.addEventListener('input', function() {
            topPValue.textContent = this.value;
        });
    }
    
    // 长度惩罚滑块
    const lengthPenaltySlider = document.getElementById('length-penalty');
    const lengthPenaltyValue = document.getElementById('length-penalty-value');
    
    if (lengthPenaltySlider && lengthPenaltyValue) {
        lengthPenaltySlider.addEventListener('input', function() {
            lengthPenaltyValue.textContent = this.value;
        });
    }
    
    // 重复惩罚滑块
    const repetitionPenaltySlider = document.getElementById('repetition-penalty');
    const repetitionPenaltyValue = document.getElementById('repetition-penalty-value');
    
    if (repetitionPenaltySlider && repetitionPenaltyValue) {
        repetitionPenaltySlider.addEventListener('input', function() {
            repetitionPenaltyValue.textContent = this.value;
        });
    }
}

// 设置按钮事件监听
function setupButtonListeners() {
    elements.synthesizeBtn.addEventListener('click', handleSynthesize);
    elements.resetParamsBtn.addEventListener('click', handleResetParams);
    elements.clearBtn.addEventListener('click', handleClear);
    elements.cancelJobBtn.addEventListener('click', handleCancel);
    elements.batchDownloadAll.addEventListener('click', handleBatchDownloadAll);
}

// 设置文件上传事件监听
function setupFileUploadListener() {
    elements.fileUpload.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            elements.fileName.textContent = file.name;
            
            // 显示解析状态
            showStatus('正在解析文件内容...', 'processing');
            
            // 创建FormData并上传文件到后端解析
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/api/parse-file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 将解析后的文本内容填充到文本输入框
                    const textContent = data.texts.join('\n');
                    elements.inputText.value = textContent;
                    showStatus(`成功解析文件，共 ${data.total_texts} 条文本`, 'success');
                } else {
                    showStatus(`文件解析失败: ${data.error}`, 'error');
                    // 清空文件名显示
                    elements.fileName.textContent = '未选择文件';
                    // 重置文件输入
                    elements.fileUpload.value = '';
                }
            })
            .catch(error => {
                console.error('文件解析请求失败:', error);
                showStatus('文件解析请求失败，请检查网络连接', 'error');
                // 清空文件名显示
                elements.fileName.textContent = '未选择文件';
                // 重置文件输入
                elements.fileUpload.value = '';
            });
        } else {
            elements.fileName.textContent = '未选择文件';
        }
    });
}

// 加载可用的音色、情绪和噪音类型
function loadEmotionsAndNoiseTypes() {
    // 加载音色列表
    fetch('/api/speakers')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.speakers && data.speakers.length > 0) {
                // 清空现有选项
                elements.speaker.innerHTML = '';
                // 添加新选项
                data.speakers.forEach(speaker => {
                    const option = document.createElement('option');
                    option.value = speaker.value;
                    option.textContent = speaker.display_name;
                    elements.speaker.appendChild(option);
                });
                // 设置默认选中第一个选项
                elements.speaker.selectedIndex = 0;
            } else {
                // 如果加载失败，使用默认选项
                loadDefaultSpeakers();
            }
        })
        .catch(error => {
            console.error('加载音色列表失败:', error);
            // 如果加载失败，使用默认选项
            loadDefaultSpeakers();
        });
    
    // 加载情绪列表
    fetch('/api/emotions')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.emotions && data.emotions.length > 0) {
                // 清空现有选项
                elements.emotion.innerHTML = '';
                // 添加新选项
                data.emotions.forEach(emotion => {
                    const option = document.createElement('option');
                    option.value = emotion;
                    option.textContent = getEmotionDisplayName(emotion);
                    elements.emotion.appendChild(option);
                });
                // 设置默认选中第一个选项
                elements.emotion.selectedIndex = 0;
            } else {
                // 如果加载失败，使用默认选项
                loadDefaultEmotions();
            }
        })
        .catch(error => {
            console.error('加载情绪列表失败:', error);
            // 如果加载失败，使用默认选项
            loadDefaultEmotions();
        });
    
    // 加载噪音类型列表
    fetch('/api/noise-types')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.noise_types && data.noise_types.length > 0) {
                // 清空现有选项
                elements.noiseType.innerHTML = '';
                // 添加新选项
                data.noise_types.forEach(noiseType => {
                    const option = document.createElement('option');
                    option.value = noiseType;
                    option.textContent = getNoiseTypeDisplayName(noiseType);
                    elements.noiseType.appendChild(option);
                });
                // 设置默认选中第一个选项
                elements.noiseType.selectedIndex = 0;
            } else {
                // 如果加载失败，使用默认选项
                loadDefaultNoiseTypes();
            }
        })
        .catch(error => {
            console.error('加载噪音类型列表失败:', error);
            // 如果加载失败，使用默认选项
            loadDefaultNoiseTypes();
        });
}

// 加载默认音色选项
function loadDefaultSpeakers() {
    const defaultSpeakers = [
        { value: 'random', display_name: '随机选择' },
        { value: 'female_1', display_name: '女声1号' }
    ];
    elements.speaker.innerHTML = '';
    defaultSpeakers.forEach(speaker => {
        const option = document.createElement('option');
        option.value = speaker.value;
        option.textContent = speaker.display_name;
        elements.speaker.appendChild(option);
    });
    elements.speaker.selectedIndex = 0;
}

// 加载默认情绪选项
function loadDefaultEmotions() {
    const defaultEmotions = ['neutral', 'happy', 'sad', 'angry', 'surprise'];
    elements.emotion.innerHTML = '';
    defaultEmotions.forEach(emotion => {
        const option = document.createElement('option');
        option.value = emotion;
        option.textContent = getEmotionDisplayName(emotion);
        elements.emotion.appendChild(option);
    });
    elements.emotion.selectedIndex = 0;
}

// 加载默认噪音类型选项
function loadDefaultNoiseTypes() {
    const defaultNoiseTypes = ['none', 'white', 'pink', 'babble', 'volvo'];
    elements.noiseType.innerHTML = '';
    defaultNoiseTypes.forEach(noiseType => {
        const option = document.createElement('option');
        option.value = noiseType;
        option.textContent = getNoiseTypeDisplayName(noiseType);
        elements.noiseType.appendChild(option);
    });
    elements.noiseType.selectedIndex = 0;
}

// 获取情绪的显示名称
function getEmotionDisplayName(emotion) {
    const emotionMap = {
        'happy': '开心 (Happy)',
        'neutral': '中性 (Neutral)',
        'sad': '悲伤 (Sad)',
        'angry': '生气 (Angry)',
        'surprise': '惊讶 (Surprise)'
    };
    return emotionMap[emotion] || emotion;
}

// 获取噪音类型的显示名称
function getNoiseTypeDisplayName(noiseType) {
    const noiseMap = {
        'volvo': '汽车噪音 (Volvo)',
        'none': '无噪音',
        'white': '白噪音 (White)',
        'pink': '粉噪音 (Pink)',
        'babble': '人声噪音 (Babble)',
        '风噪': '风噪 (Wind)'
    };
    
    // 如果噪音类型在映射表中，返回对应的显示名称
    if (noiseMap[noiseType]) {
        return noiseMap[noiseType];
    }
    
    // 对于未知的噪音类型，生成友好的显示名称
    // 移除特殊字符和数字，保留主要描述
    const cleanName = noiseType.replace(/[^\u4e00-\u9fa5a-zA-Z]/g, ' ').trim();
    
    // 如果包含中文，直接使用
    if (/[\u4e00-\u9fa5]/.test(cleanName)) {
        return cleanName;
    }
    
    // 如果是英文，添加中文翻译
    const englishToChinese = {
        'wind': '风噪',
        'rain': '雨声',
        'traffic': '交通噪音',
        'office': '办公室噪音',
        'street': '街道噪音',
        'cafe': '咖啡馆噪音',
        'factory': '工厂噪音',
        'nature': '自然噪音'
    };
    
    const lowerCaseName = cleanName.toLowerCase();
    if (englishToChinese[lowerCaseName]) {
        return englishToChinese[lowerCaseName];
    }
    
    // 默认情况下返回原始名称
    return noiseType;
}

// 处理语音合成
function handleSynthesize() {
    // 检查是否有输入
    const text = elements.inputText.value.trim();
    const hasFile = elements.fileUpload.files && elements.fileUpload.files.length > 0;
    
    if (!text && !hasFile) {
        showStatus('请输入文本或上传文件', 'error');
        return;
    }
    
    // 如果已经有合成在进行，显示提示并返回
    if (isSynthesizing) {
        showStatus('语音合成正在进行中，请等待完成或取消当前任务', 'error');
        return;
    }
    
    // 创建新的AbortController用于取消请求
    currentAbortController = new AbortController();
    isSynthesizing = true;
    
    // 显示处理中状态
    showStatus('正在合成语音，请稍候...', 'processing');
    elements.synthesizeBtn.disabled = true;
    elements.cancelJobBtn.disabled = false;
    
    // 创建FormData
    const formData = new FormData();
    
    // 添加文本（如果有）
    if (text) {
        formData.append('text', text);
    }
    
    // 添加文件（如果有）
    if (hasFile) {
        formData.append('file', elements.fileUpload.files[0]);
    }
    
    // 添加参数
    formData.append('speaker_wav', elements.speaker.value);
    formData.append('emotion', elements.emotion.value);
    formData.append('speed', elements.speed.value);
    formData.append('temperature', elements.temperature.value);
    formData.append('top_k', elements.topK.value);
    formData.append('top_p', document.getElementById('top-p').value);
    formData.append('length_penalty', document.getElementById('length-penalty').value);
    formData.append('repetition_penalty', document.getElementById('repetition-penalty').value);
    
    // 发送请求
    fetch('/api/tts', {
        method: 'POST',
        body: formData,
        signal: currentAbortController.signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // 重置状态
        isSynthesizing = false;
        elements.synthesizeBtn.disabled = false;
        elements.cancelJobBtn.disabled = true;
        
        if (data.success) {
            // 保存结果
            currentResults = data;
            currentOutputDir = data.output_dir; // 保存输出目录路径
            
            // 显示成功状态
            showStatus(`成功合成 ${data.success_count} 个语音文件`, 'success');
            
            // 显示处理时间
            elements.totalTime.textContent = data.total_processing_time;
            elements.processingTime.classList.remove('hidden');
            
            // 显示原始音频结果
            displayAudioResults(data.audio_files, elements.originalAudioList);
            elements.originalAudioContainer.classList.remove('hidden');
            
            // 检查是否需要自动进行噪音混合
            const noiseType = elements.noiseType.value;
            if (elements.randomNoise.checked) {
                // 如果随机噪声选项被勾选，直接调用随机噪声混合
                autoMixRandomNoise(data.audio_files, parseInt(elements.snr.value));
            } else if (noiseType !== 'none') {
                // 否则进行普通噪音混合
                autoMixNoise(data.audio_files, noiseType, parseInt(elements.snr.value));
            } else {
                // 隐藏噪音混合结果
                elements.noiseAudioContainer.classList.add('hidden');
            }
        } else {
            // 显示错误信息
            let errorMessage = data.error || '语音合成失败';
            if (data.error_details && data.error_details.length > 0) {
                errorMessage += '<br>详细错误:<br>' + data.error_details.join('<br>');
            }
            showStatus(errorMessage, 'error');
        }
    })
    .catch(error => {
        // 重置状态
        isSynthesizing = false;
        elements.synthesizeBtn.disabled = false;
        elements.cancelJobBtn.disabled = true;
        
        // 如果是取消操作，不显示错误信息
        if (error.name === 'AbortError') {
            showStatus('语音合成已取消', 'success');
        } else {
            showStatus('网络错误或服务器未响应', 'error');
            console.error('语音合成请求失败:', error);
        }
    });
}

// 自动噪音混合函数
function autoMixNoise(audioFiles, noiseType, snr) {
    if (!audioFiles || audioFiles.length === 0) {
        return;
    }
    
    // 显示处理中状态
    showStatus('正在添加噪音，请稍候...', 'processing');
    
    const totalFiles = audioFiles.length;
    let processedCount = 0;
    const noiseMixedFiles = [];
    
    audioFiles.forEach(audioFile => {
        // 发送噪音混合请求
        fetch('/api/mix-noise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                audio_path: audioFile.path,
                noise_type: noiseType,
                snr: snr
            })
        })
        .then(response => response.json())
        .then(data => {
            processedCount++;
            
            if (data.success) {
                noiseMixedFiles.push({
                    path: data.noise_mixed_path,
                    filename: data.noise_mixed_filename
                });
            }
            
            // 检查是否所有文件都已处理完成
            if (processedCount === totalFiles) {
                if (noiseMixedFiles.length > 0) {
                    showStatus(`成功为 ${noiseMixedFiles.length} 个文件添加噪音`, 'success');
                    displayAudioResults(noiseMixedFiles, elements.noiseAudioList);
                    elements.noiseAudioContainer.classList.remove('hidden');
                } else {
                    showStatus('噪音混合失败，请重试', 'error');
                }
            }
        })
        .catch(error => {
            processedCount++;
            console.error('噪音混合请求失败:', error);
            
            if (processedCount === totalFiles) {
                showStatus('部分文件噪音混合失败', 'error');
            }
        });
    });
}

// 自动随机噪声混合函数
function autoMixRandomNoise(audioFiles, snr) {
    if (!audioFiles || audioFiles.length === 0) {
        return;
    }
    
    // 显示处理中状态
    showStatus('正在添加随机噪声，请稍候...', 'processing');
    
    const totalFiles = audioFiles.length;
    let processedCount = 0;
    const noiseMixedFiles = [];
    
    audioFiles.forEach(audioFile => {
        // 发送随机噪声混合请求
        fetch('/api/mix-random-noise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                audio_path: audioFile.path,
                count: parseInt(elements.randomNoiseCount.value),
                snr: snr
            })
        })
        .then(response => response.json())
        .then(data => {
            processedCount++;
            
            // 添加调试日志
            console.log('Random noise response:', data);
            
            if (data.success && data.noise_mixed_paths && data.noise_mixed_paths.length > 0) {
                // 优先处理API返回的相对路径
                data.noise_mixed_paths.forEach((path, index) => {
                    noiseMixedFiles.push({
                        path: path,
                        filename: data.noise_mixed_files ? data.noise_mixed_files[index] : `file_${index+1}.wav`
                    });
                });
            } else if (data.success && data.noise_mixed_files && data.noise_mixed_files.length > 0) {
                // 处理API返回的文件名数组
                data.noise_mixed_files.forEach((filename, index) => {
                    // 构建完整的文件路径
                    const path = `output/tts_with_noise/${filename}`;
                    noiseMixedFiles.push({
                        path: path,
                        filename: filename
                    });
                });
            } else {
                // 添加错误日志
                console.error('Random noise failed:', data);
                if (!data.success) {
                    showStatus(`随机噪声混合失败: ${data.error || '未知错误'}`, 'error');
                }
            }
            
            // 检查是否所有文件都已处理完成
            if (processedCount === totalFiles) {
                if (noiseMixedFiles.length > 0) {
                    showStatus(`成功为 ${noiseMixedFiles.length} 个文件添加随机噪声`, 'success');
                    displayAudioResults(noiseMixedFiles, elements.noiseAudioList);
                    elements.noiseAudioContainer.classList.remove('hidden');
                } else {
                    showStatus('随机噪声混合失败，请重试', 'error');
                }
            }
        })
        .catch(error => {
            processedCount++;
            console.error('随机噪声混合请求失败:', error);
            
            if (processedCount === totalFiles) {
                showStatus('部分文件随机噪声混合失败', 'error');
            }
        });
    });
}

// 重置参数到默认值
function handleResetParams() {
    // 重置滑块参数到默认值
    elements.snr.value = 10;
    elements.snrValue.textContent = '10 dB';
    
    // 重置随机噪声选项
    elements.randomNoise.checked = false;
    elements.randomNoiseCount.value = 1;
    elements.randomNoiseCountValue.textContent = '1';
    elements.randomNoiseCountGroup.style.display = 'none';
    elements.noiseType.disabled = false;
    
    elements.speed.value = 1.0;
    elements.speedValue.textContent = '1.0x';
    
    elements.temperature.value = 0.85;
    elements.temperatureValue.textContent = '0.85';
    
    elements.topK.value = 50;
    elements.topKValue.textContent = '50';
    
    // 重置新增的参数
    const topPSlider = document.getElementById('top-p');
    const topPValue = document.getElementById('top-p-value');
    if (topPSlider && topPValue) {
        topPSlider.value = 0.8;
        topPValue.textContent = '0.8';
    }
    
    const lengthPenaltySlider = document.getElementById('length-penalty');
    const lengthPenaltyValue = document.getElementById('length-penalty-value');
    if (lengthPenaltySlider && lengthPenaltyValue) {
        lengthPenaltySlider.value = 1.0;
        lengthPenaltyValue.textContent = '1.0';
    }
    
    const repetitionPenaltySlider = document.getElementById('repetition-penalty');
    const repetitionPenaltyValue = document.getElementById('repetition-penalty-value');
    if (repetitionPenaltySlider && repetitionPenaltyValue) {
        repetitionPenaltySlider.value = 2.0;
        repetitionPenaltyValue.textContent = '2.0';
    }
    
    // 重置选择框到默认选项
    if (elements.speaker.options.length > 0) {
        elements.speaker.selectedIndex = 0;
    }
    
    if (elements.emotion.options.length > 0) {
        elements.emotion.selectedIndex = 0;
    }
    
    if (elements.noiseType.options.length > 0) {
        elements.noiseType.selectedIndex = 0;
    }
    
    showStatus('参数已重置到默认值', 'success');
    setTimeout(() => {
        elements.statusMessage.classList.add('hidden');
    }, 2000);
}

// 处理取消任务
function handleCancel(){
    if (!isSynthesizing || !currentAbortController) {
        return;
    }
    
    // 显示取消状态
    showStatus('正在取消语音合成任务...', 'processing');
    
    // 取消当前请求
    currentAbortController.abort();
    
    // 重置状态
    isSynthesizing = false;
    elements.synthesizeBtn.disabled = false;
    elements.cancelJobBtn.disabled = true;
    
    // 显示取消完成状态
    setTimeout(() => {
        showStatus('语音合成任务已取消', 'success');
        setTimeout(() => {
            elements.statusMessage.classList.add('hidden');
        }, 3000);
    }, 1000);
}

// 处理清空操作
function handleClear() {
    // 如果正在合成，先取消
    if (isSynthesizing) {
        handleCancel();
    }
    
    // 清空输入
    elements.inputText.value = '';
    elements.fileUpload.value = '';
    elements.fileName.textContent = '未选择文件';
    
    // 重置结果
    currentResults = null;
    currentOutputDir = null; // 清空输出目录
    
    // 重置取消相关状态
    isSynthesizing = false;
    currentAbortController = null;
    elements.synthesizeBtn.disabled = false;
    elements.cancelJobBtn.disabled = true;
    
    // 隐藏结果显示
    elements.originalAudioContainer.classList.add('hidden');
    elements.noiseAudioContainer.classList.add('hidden');
    elements.processingTime.classList.add('hidden');
    elements.statusMessage.classList.add('hidden');
    
    // 清空音频列表
    elements.originalAudioList.innerHTML = '';
    elements.noiseAudioList.innerHTML = '';
}

// 显示状态消息
function showStatus(message, type) {
    elements.statusMessage.innerHTML = message;
    elements.statusMessage.className = 'status-message';
    
    if (type === 'success') {
        elements.statusMessage.classList.add('success');
    } else if (type === 'error') {
        elements.statusMessage.classList.add('error');
    } else if (type === 'processing') {
        elements.statusMessage.classList.add('processing');
        elements.statusMessage.innerHTML = '<span class="loading-spinner"></span>' + message;
    }
    
    elements.statusMessage.classList.remove('hidden');
    
    // 自动隐藏成功消息
    if (type === 'success') {
        setTimeout(() => {
            elements.statusMessage.classList.add('hidden');
        }, 5000);
    }
}

// 显示音频结果
function displayAudioResults(audioFiles, container) {
    container.innerHTML = '';
    
    audioFiles.forEach((audioFile, index) => {
        // 创建音频项
        const audioItem = document.createElement('div');
        audioItem.className = 'audio-item';
        
        // 创建音频播放器
        const audioPlayer = document.createElement('audio');
        audioPlayer.className = 'audio-player';
        audioPlayer.controls = true;
        audioPlayer.src = `/audio/${encodeURIComponent(audioFile.path)}`;
        audioPlayer.title = audioFile.filename;
        
        // 创建音频信息
        const audioInfo = document.createElement('div');
        audioInfo.className = 'audio-info';
        
        // 创建文件名显示
        const fileName = document.createElement('span');
        fileName.className = 'audio-filename';
        fileName.textContent = audioFile.filename;
        
        // 创建下载按钮
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.textContent = '下载';
        downloadBtn.addEventListener('click', () => {
            // 创建下载链接
            const downloadLink = document.createElement('a');
            downloadLink.href = `/audio/${encodeURIComponent(audioFile.path)}`;
            downloadLink.download = audioFile.filename;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        });
        
        // 组装音频信息
        audioInfo.appendChild(fileName);
        audioInfo.appendChild(downloadBtn);
        
        // 组装音频项
        audioItem.appendChild(audioPlayer);
        audioItem.appendChild(audioInfo);
        
        // 添加到容器
        container.appendChild(audioItem);
    });
}

// 批量下载原始音频
async function handleBatchDownloadOriginal() {
    if (!currentResults || !currentResults.original || currentResults.original.length === 0) {
        showStatus('没有可下载的原始音频文件', 'error');
        return;
    }
    
    try {
        // 禁用按钮并显示处理状态
        elements.batchDownloadOriginal.disabled = true;
        showStatus('正在打包原始音频文件...', 'processing');
        
        // 准备音频文件列表
        const audioFiles = currentResults.original.map(file => ({
            path: file.path,
            filename: file.filename
        }));
        
        // 调用批量下载API
        const response = await fetch('/api/batch-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ audio_files: audioFiles })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 创建下载链接
            const downloadLink = document.createElement('a');
            downloadLink.href = `/api/download-zip/${data.zip_filename}`;
            downloadLink.download = `original_audio_batch_${data.zip_filename}`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            showStatus('原始音频打包下载完成', 'success');
        } else {
            showStatus(`打包下载失败: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('批量下载请求失败:', error);
        showStatus('批量下载请求失败，请检查网络连接', 'error');
    } finally {
        elements.batchDownloadOriginal.disabled = false;
    }
}

// 批量下载整个输出目录
async function handleBatchDownloadAll() {
    if (!currentOutputDir) {
        showStatus('没有可下载的输出目录', 'error');
        return;
    }
    
    try {
        // 禁用按钮并显示处理状态
        elements.batchDownloadAll.disabled = true;
        showStatus('正在打包输出目录...', 'processing');
        
        // 调用输出目录下载API
        const response = await fetch('/api/download-output-dir', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ output_dir: currentOutputDir })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 创建下载链接
            const downloadLink = document.createElement('a');
            downloadLink.href = `/api/download-zip/${data.zip_filename}`;
            downloadLink.download = `output_directory_${data.zip_filename}`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            showStatus('输出目录打包下载完成', 'success');
        } else {
            showStatus(`打包下载失败: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('批量下载请求失败:', error);
        showStatus('批量下载请求失败，请检查网络连接', 'error');
    } finally {
        elements.batchDownloadAll.disabled = false;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);