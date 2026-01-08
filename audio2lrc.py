import sys
import os
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator

def format_lrc_timestamp(seconds):
    """将秒数转换为 LRC 时间戳格式 [mm:ss.xx]"""
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"[{minutes:02d}:{remaining_seconds:05.2f}]"

def generate_dual_lrc(audio_path, output_lrc_path, model_size="large-v3", device="auto"):
    # 1. 加载模型
    print(f"正在加载模型 ({model_size})...")
    # device 设置为 "cuda" 使用显卡，"cpu" 使用处理器
    # compute_type 设置为 "int8" 可以减少内存占用，"float32" 可避免你之前的 warning，如果在 GPU 上可用 "float16"
    model = WhisperModel(model_size, device=device, compute_type="default")

    # 2. 转录音频
    print(f"正在转录音频: {audio_path} ...")
    segments, info = model.transcribe(audio_path, beam_size=5)
    print(f"检测到语言: {info.language}, 概率: {info.language_probability:.2f}")

    # 3. 初始化翻译器 (源语言自动识别，目标语言设为中文)
    translator = GoogleTranslator(source='auto', target='zh-CN')

    # 4. 写入 LRC 文件
    print("开始生成双语歌词...\n" + "-"*30)
    with open(output_lrc_path, "w", encoding="utf-8") as lrc_file:
        lrc_file.write("[by:Whisper-AI-Dual-Language]\n")
        
        for segment in segments:
            start_time = segment.start
            original_text = segment.text.strip()
            
            if not original_text:
                continue

            # 翻译文本
            try:
                translated_text = translator.translate(original_text)
            except Exception as e:
                print(f"翻译出错: {e}")
                translated_text = ""

            # 格式化时间戳
            timestamp = format_lrc_timestamp(start_time)
            
            # 组合行: [时间] 原文 | 译文
            line = f"{timestamp}{original_text} | {translated_text}\n"
            
            lrc_file.write(line)
            # 实时打印预览
            print(line.strip())

    print("-"*30 + f"\n成功！双语 LRC 文件已保存至: {output_lrc_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python audio2lrc.py <音频路径>")
    else:
        input_audio = sys.argv[1]
        
        # 自动生成同名的 .lrc 文件名
        base_name = os.path.splitext(input_audio)[0]
        output_lrc = f"{base_name}.lrc"
        
        # 执行转换
        generate_dual_lrc(input_audio, output_lrc)