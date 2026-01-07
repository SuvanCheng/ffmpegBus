import datetime
import argparse
import sys
import os

# --- 默认配置 ---
CONFIG = {
    "SCREEN_W": 1920,
    "SCREEN_H": 1080,
    "CENTER_Y": 700,
    "LINE_SPACING": 180,       # 行间距
    "LINE_DURATION": 1.0,      # 每行文字高亮的持续时间 小提示：这里应该是根据字幕时间来的，先默认设置为1s间隔
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

    base_name = os.path.splitext(input_file)[0]
    secondary_output = f"{base_name}.ass"

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    # 在样式表中预设基础阴影颜色
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
    for i in range(len(lines)):
        display_text = lines[i].replace(" | ", "\\N")
        
        visible_range = range(max(0, i-2), min(len(lines), i+3)) #小提示： 如果你发现文字向上飞得太远超出了屏幕，可以微调 visible_range 里的 i+5 为 i+3 或 i+4
        
        for stage in visible_range:
            start_t = stage * CONFIG['LINE_DURATION']
            end_t = (stage + 1) * CONFIG['LINE_DURATION']

            # 计算当前阶段的滚动路径
            y_start = CONFIG['CENTER_Y'] + (i - stage) * CONFIG['LINE_SPACING']
            y_end = y_start - CONFIG['LINE_SPACING']
            
            move_tag = f"\\move({CONFIG['SCREEN_W']//2},{y_start},{CONFIG['SCREEN_W']//2},{y_end},0,{CONFIG['TRANSITION_TIME']})"
            # 只有在整个生命周期的绝对开始和绝对结束时才使用 fad
            fade_in = CONFIG['FADE_TIME'] if stage == visible_range[0] else 0
            fade_out = CONFIG['FADE_TIME'] if stage == visible_range[-1] else 0
            fad_tag = f"\\fad({fade_in},{fade_out})"
            
            # bord: 边框(光晕宽度), shad: 阴影深度, blur: 强力模糊, 3c/4c: 边框/阴影颜色
            visual_base = (f"\\bord{CONFIG['GLOW_WIDTH']}\\shad{CONFIG['SHADOW_DEPTH']}"
                          f"\\blur{CONFIG['GLOW_BLUR']}\\3c{CONFIG['SHADOW_COLOR']}\\4c{CONFIG['SHADOW_COLOR']}")

            # --- 状态逻辑控制 ---
            if stage == i: 
                # 【激活中】：处于中心，由暗变亮，由小变大
                base_style = f"\\c{CONFIG['COLOR_NORMAL']}\\1a{CONFIG['ALPHA_NORMAL']}\\3a{CONFIG['ALPHA_NORMAL']}\\4a{CONFIG['ALPHA_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']}"
                trans_tag = f"\\t(0,{CONFIG['TRANSITION_TIME']},\\c{CONFIG['COLOR_ACTIVE']}\\1a{CONFIG['ALPHA_ACTIVE']}\\3a{CONFIG['SHADOW_ALPHA']}\\4a{CONFIG['SHADOW_ALPHA']}\\fs{CONFIG['FONT_SIZE_ACTIVE']})"
            
            elif stage == i + 1: 
                # 【刚结束激活】：从中心向上滚动，由亮变暗，由大变小
                base_style = f"\\c{CONFIG['COLOR_ACTIVE']}\\1a{CONFIG['ALPHA_ACTIVE']}\\3a{CONFIG['SHADOW_ALPHA']}\\4a{CONFIG['SHADOW_ALPHA']}\\fs{CONFIG['FONT_SIZE_ACTIVE']}"
                trans_tag = f"\\t(0,{CONFIG['TRANSITION_TIME']},\\c{CONFIG['COLOR_NORMAL']}\\1a{CONFIG['ALPHA_NORMAL']}\\3a{CONFIG['ALPHA_NORMAL']}\\4a{CONFIG['ALPHA_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']})"
            
            else: 
                # 【进场中】或【退出漂移中】：保持暗淡小字，持续滚动
                base_style = f"\\c{CONFIG['COLOR_NORMAL']}\\1a{CONFIG['ALPHA_NORMAL']}\\3a{CONFIG['ALPHA_NORMAL']}\\4a{CONFIG['ALPHA_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']}"
                trans_tag = ""

            tags = f"{{{fad_tag}{move_tag}{visual_base}{base_style}{trans_tag}}}"
            content_lines.append(f"Dialogue: 0,{format_ass_time(start_t)},{format_ass_time(end_t)},Default,,0,0,0,,{tags}{display_text}\n")

    for target_file in [output_file, secondary_output]:
        with open(target_file, "w", encoding="utf-8-sig") as f:
            f.write(header)
            f.writelines(content_lines)

    print(f"字幕已完成:\n1. {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成高质感持续滚动字幕")
    parser.add_argument("input", help="输入文本文件路径")
    parser.add_argument("-o", "--output", default="output.ass", help="输出ASS文件名")
    args = parser.parse_args()
    generate_ass(args.input, args.output)