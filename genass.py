import datetime
import argparse
import sys
import os
import re

# --- 默认配置 ---
CONFIG = {
    "SCREEN_W": 1920,
    "SCREEN_H": 1080,
    "CENTER_Y": 700,
    "LINE_SPACING": 180,       # 行间距

    "TRANSITION_TIME": 800,    # 动画过渡时间(毫秒)
    "FONT_SIZE_ACTIVE": 60,    # 激活行字号
    "FONT_SIZE_NORMAL": 40,    # 普通行字号
    "COLOR_ACTIVE": "&H00FFFF&", # 亮黄色
    "COLOR_NORMAL": "&H666666&", # 暗灰色
    "ALPHA_ACTIVE": "&H00&",     # 激活行透明度 (00是不透明)
    "ALPHA_NORMAL": "&H60&",     # 普通行透明度 (60是半透明)
    "BLUR_AMOUNT": 1.5,
    "FADE_TIME": 800,           # 淡入淡出时间
    # --- 新增：背景保护与阴影配置 ---
    "SHADOW_DEPTH": 3,           # 阴影深度
    "SHADOW_COLOR": "&H000000&", # 阴影颜色 (黑色)
    "SHADOW_ALPHA": "&H40&",     # 阴影透明度 (40代表较深)
    "GLOW_WIDTH": 2,             # 光晕(边框)宽度
    "GLOW_BLUR": 8,              # 光晕模糊度 (值越大越像柔和的背板) 小提示：如果你的视频背景特别乱（比如全是跳动的灯光），可以将 GLOW_BLUR 调大到 12 或 15，这样背板会更宽、更平滑。
}

def parse_time(time_str):
    """将 [mm:ss.xx] 格式转换为秒"""
    m, s = time_str.strip("[]").split(":")
    return int(m) * 60 + float(s)

def format_ass_time(seconds):
    if seconds < 0: seconds = 0
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = td.total_seconds() % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def generate_ass(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"错误: 找不到文件 {input_file}")
        return

    # 正则表达式匹配 [00:00.00] 文本
    pattern = re.compile(r"\[(\d+:\d+\.\d+)\](.*)")
    
    parsed_data = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line.strip())
            if match:
                time_val = parse_time(match.group(1))
                text_val = match.group(2).strip().replace(" | ", "\\N")
                parsed_data.append({"time": time_val, "text": text_val})

    if not parsed_data:
        print("未在文件中找到有效的时间戳格式。")
        return

    # 预处理：计算每一行的结束时间（下一行的开始即本行的结束）
    # 最后一行给一个默认的持续时间（例如5秒）
    for i in range(len(parsed_data)):
        if i < len(parsed_data) - 1:
            parsed_data[i]["end_time"] = parsed_data[i+1]["time"]
        else:
            parsed_data[i]["end_time"] = parsed_data[i]["time"] + 5.0

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CONFIG['SCREEN_W']}
PlayResY: {CONFIG['SCREEN_H']}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{CONFIG['FONT_SIZE_NORMAL']},&HFFFFFF,{CONFIG['SHADOW_COLOR']},{CONFIG['SHADOW_COLOR']},0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    content_lines = []
    num_lines = len(parsed_data)

    for i in range(num_lines):
        display_text = parsed_data[i]["text"]
        
        # 决定该行在哪些时间段内可见 (前2行到后2行激活时)
        # 这保证了平滑的滚动流
        visible_indices = range(max(0, i-2), min(num_lines, i+3))
        
        for stage_idx in visible_indices:
            # 当前时间段的起止点
            start_t = parsed_data[stage_idx]["time"]
            end_t = parsed_data[stage_idx]["end_time"]

            # 计算 Y 轴滚动
            # 当 stage_idx == i 时，文字正在中心激活
            y_start = CONFIG['CENTER_Y'] + (i - stage_idx) * CONFIG['LINE_SPACING']
            y_end = y_start - CONFIG['LINE_SPACING']
            
            move_tag = f"\\move({CONFIG['SCREEN_W']//2},{y_start},{CONFIG['SCREEN_W']//2},{y_end},0,{CONFIG['TRANSITION_TIME']})"
            # 只有在整个生命周期的绝对开始和绝对结束时才使用 fad
            fade_in = CONFIG['FADE_TIME'] if stage_idx == visible_indices[0] else 0
            fade_out = CONFIG['FADE_TIME'] if stage_idx == visible_indices[-1] else 0
            fad_tag = f"\\fad({fade_in},{fade_out})"
            
            # bord: 边框(光晕宽度), shad: 阴影深度, blur: 强力模糊, 3c/4c: 边框/阴影颜色
            visual_base = (f"\\bord{CONFIG['GLOW_WIDTH']}\\shad{CONFIG['SHADOW_DEPTH']}"
                          f"\\blur{CONFIG['GLOW_BLUR']}\\3c{CONFIG['SHADOW_COLOR']}\\4c{CONFIG['SHADOW_COLOR']}")

            if stage_idx == i: 
                # 【激活中】：由暗变亮
                base_style = f"\\c{CONFIG['COLOR_NORMAL']}\\1a{CONFIG['ALPHA_NORMAL']}\\3a{CONFIG['ALPHA_NORMAL']}\\4a{CONFIG['ALPHA_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']}"
                trans_tag = f"\\t(0,{CONFIG['TRANSITION_TIME']},\\c{CONFIG['COLOR_ACTIVE']}\\1a{CONFIG['ALPHA_ACTIVE']}\\3a{CONFIG['SHADOW_ALPHA']}\\4a{CONFIG['SHADOW_ALPHA']}\\fs{CONFIG['FONT_SIZE_ACTIVE']})"
            
            elif stage_idx == i + 1: 
                # 【刚结束激活】：向上移动并由亮变暗
                base_style = f"\\c{CONFIG['COLOR_ACTIVE']}\\1a{CONFIG['ALPHA_ACTIVE']}\\3a{CONFIG['SHADOW_ALPHA']}\\4a{CONFIG['SHADOW_ALPHA']}\\fs{CONFIG['FONT_SIZE_ACTIVE']}"
                trans_tag = f"\\t(0,{CONFIG['TRANSITION_TIME']},\\c{CONFIG['COLOR_NORMAL']}\\1a{CONFIG['ALPHA_NORMAL']}\\3a{CONFIG['ALPHA_NORMAL']}\\4a{CONFIG['ALPHA_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']})"
            
            else: 
                # 【准备进场】或【准备退场】
                base_style = f"\\c{CONFIG['COLOR_NORMAL']}\\1a{CONFIG['ALPHA_NORMAL']}\\3a{CONFIG['ALPHA_NORMAL']}\\4a{CONFIG['ALPHA_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']}"
                trans_tag = ""

            tags = f"{{{fad_tag}{move_tag}{visual_base}{base_style}{trans_tag}}}"
            content_lines.append(f"Dialogue: 0,{format_ass_time(start_t)},{format_ass_time(end_t)},Default,,0,0,0,,{tags}{display_text}\n")

    with open(output_file, "w", encoding="utf-8-sig") as f:
        f.write(header)
        f.writelines(content_lines)

    print(f"字幕已完成: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解析时间戳生成高质感滚动字幕")
    parser.add_argument("input", help="输入带有时间戳的文本文件")
    parser.add_argument("-o", "--output", default="output.ass", help="输出ASS文件名")
    args = parser.parse_args()
    generate_ass(args.input, args.output)