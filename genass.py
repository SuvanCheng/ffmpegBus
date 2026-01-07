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
    "LINE_DURATION": 4.0,      # 每行文字高亮的持续时间
    "TRANSITION_TIME": 800,    # 动画过渡时间(毫秒)
    "FONT_SIZE_ACTIVE": 60,    # 激活行字号
    "FONT_SIZE_NORMAL": 40,    # 普通行字号
    "COLOR_ACTIVE": "&H00FFFF&", # 亮黄色
    "COLOR_NORMAL": "&H666666&", # 暗灰色
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

    # 获取输入文件的基础名称 (例如 test.txt -> test)
    base_name = os.path.splitext(input_file)[0]
    secondary_output = f"{base_name}.ass"

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CONFIG['SCREEN_W']}
PlayResY: {CONFIG['SCREEN_H']}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{CONFIG['FONT_SIZE_NORMAL']},&HFFFFFF,&H000000,&H000000,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # 生成字幕内容
    content_lines = []
    # 遍历每一行，计算它在不同时间点的表现
    for i in range(len(lines)):
        display_text = lines[i].replace(" | ", "\\N")
        # 这一行文字“出生”到“消失”的总生命周期
        # 我们让它在轮到它前 2 行就开始出现，轮到它后 2 行再消失
        for stage in range(max(0, i-2), min(len(lines), i+3)):
            start_t = stage * CONFIG['LINE_DURATION']
            end_t = (stage + 1) * CONFIG['LINE_DURATION']
            # 计算当前阶段这行字的起始位置和终点位置
            # i 是这行字的索引，stage 是当前的播放头进度
            y_start = CONFIG['CENTER_Y'] + (i - stage) * CONFIG['LINE_SPACING']
            y_end = y_start - CONFIG['LINE_SPACING']
            
            # 构建标签
            # 1. 位移动画
            move_tag = f"\\move({CONFIG['SCREEN_W']//2},{y_start},{CONFIG['SCREEN_W']//2},{y_end},0,{CONFIG['TRANSITION_TIME']})"
            
            # 2. 初始样式
            if stage == i: # 轮到这一行了，刚开始是普通，然后变大
                base_style = f"\\c{CONFIG['COLOR_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']}"
                # \t(时间, 属性) 实现丝滑放大和变色
                trans_tag = f"\\t(0,{CONFIG['TRANSITION_TIME']},\\c{CONFIG['COLOR_ACTIVE']}\\fs{CONFIG['FONT_SIZE_ACTIVE']})"
            elif stage == i + 1: # 这一行唱完了，从大变小
                base_style = f"\\c{CONFIG['COLOR_ACTIVE']}\\fs{CONFIG['FONT_SIZE_ACTIVE']}"
                trans_tag = f"\\t(0,{CONFIG['TRANSITION_TIME']},\\c{CONFIG['COLOR_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']})"
            else: # 其他静止状态
                base_style = f"\\c{CONFIG['COLOR_NORMAL']}\\fs{CONFIG['FONT_SIZE_NORMAL']}"
                trans_tag = ""

            content_lines.append(f"Dialogue: 0,{format_ass_time(start_t)},{format_ass_time(end_t)},Default,,0,0,0,,{{{move_tag}{base_style}{trans_tag}}}{display_text}\n")

    # 同时写入两个文件
    for target_file in [output_file, secondary_output]:
        with open(target_file, "w", encoding="utf-8-sig") as f:
            f.write(header)
            f.writelines(content_lines)

    print(f"字幕已生成:\n1. {output_file}\n2. {secondary_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成丝滑滚动的电子书式字幕")
    parser.add_argument("input", help="输入文本文件路径 (每行一句，支持 'EN | CN' 格式)")
    parser.add_argument("-o", "--output", default="output.ass", help="输出ASS文件名 (默认: output.ass)")
    
    args = parser.parse_args()
    generate_ass(args.input, args.output)