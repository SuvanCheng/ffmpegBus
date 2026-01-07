# ffmpegBus

1. 制作字幕
目前
 - 无时间戳，后续添加
执行
python3 genass.py test.txt

2. 根据字幕文件制作视频
目前
 - 无背景图片，暂时采用黑色背景

无音轨 执行
ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=24 -vf "subtitles=output.ass" -t 15 -c:v libx264 -pix_fmt yuv420p output.mp4
有音轨+硬件加速 执行
ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=24 -i test.m4a -vf "subtitles=output.ass" -c:v h264_videotoolbox -pix_fmt yuv420p -c:a copy -shortest output.mp4

3. 一句命令
python3 genass.py test.txt && ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=24 -i test.m4a -vf "subtitles=output.ass" -c:v h264_videotoolbox -pix_fmt yuv420p -c:a copy -shortest output.mp4
