# ffmpegBus

无

黑色背景，无音轨生成

ffmpeg -f lavfi -i color=c=black:s=1920x1080:r=30 -vf "subtitles=output.ass" -t 30 -c:v libx264 -pix_fmt yuv420p output.mp4


一句命令

python3 genass.py test.txt ;  ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=30 -vf "subtitles=output.ass" -t 30 -c:v libx264 -pix_fmt yuv420p output.mp4
