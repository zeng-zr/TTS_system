import os
import logging
from src.modules.model_manager import model_manager
from src.modules.voice_library import voice_library
from src.modules.text_loader import TextLoader
from src.modules.tts_input import TTSInput
from src.tts_synthesizer import TTSSynthesizer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # 1. 加载模型（只需加载一次）
        logger.info("Loading TTS model...")
        tts_model = model_manager.load_model()
        logger.info(f"Model loaded: {model_manager.list_loaded_models()}")
        
        # 2. 创建语音合成器
        synthesizer = TTSSynthesizer(output_dir="./output")
        
        # 3. 从音色库中随机选择一个音色
        logger.info("Selecting a random voice from library...")
        random_prompt = voice_library.get_random_prompt()
        logger.info(f"Selected prompt: {random_prompt}")
        
        # 4. 准备要合成的文本
        texts = [
"Kokoro 是一系列体积虽小但功能强大的 TTS 模型。该模型是经过短期训练的结果，从专业数据集中添加了100名中文使用者。中文数据由专业数据集公司「龙猫数据」免费且无偿地提供给我们。感谢你们让这个模型成为可能。另外，一些众包合成英语数据也进入了训练组合：1小时的 Maple，美国女性。1小时的 Sol，另一位美国女性。和1小时的 Vale，一位年长的英国女性。由于该模型删除了许多声音，因此它并不是对其前身的严格升级，但它提前发布以收集有关新声音和标记化的反馈。除了中文数据集和3小时的英语之外，其余数据都留在本次训练中。目标是推动模型系列的发展，并最终恢复一些被遗留的声音。美国版权局目前的指导表明，合成数据通常不符合版权保护的资格。由于这些合成数据是众包的，因此模型训练师不受任何服务条款的约束。该 Apache 许可模式也符合 OpenAI 所宣称的广泛传播 AI 优势的使命。如果您愿意帮助进一步完成这一使命，请考虑为此贡献许可的音频数据。"
        ]
        
        # 5. 逐个合成文本
        for i, text in enumerate(texts):
            output_file = os.path.join("./output", f"example_{i}.wav")
            logger.info(f"Synthesizing text {i+1}: {text[:30]}...")
            
            result = synthesizer.synthesize_text(
                text=text,
                speaker_wav=random_prompt,
                output_path=output_file,
                language="zh-cn"
            )
            
            if result.success:
                logger.info(f"Successfully synthesized to {result.output_file}")
            else:
                logger.error(f"Failed to synthesize text: {result.error_message}")
        
        # 6. 也可以处理文件输入（例如Excel文件）
        # 如果您有Excel文件，可以使用以下代码
        # text_loader = TextLoader()
        # excel_path = "path/to/your/excel.xlsx"
        # texts_data = text_loader.load_text_file(excel_path, sheet_name="Sheet1", text_column="text")
        # synthesizer.process_file(excel_path, output_meta="output/meta.csv")
        
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
    finally:
        # 可选：卸载模型以释放内存
        model_manager.unload_all_models()
        pass

if __name__ == "__main__":
    main()