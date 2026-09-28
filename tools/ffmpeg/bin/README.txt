可选：如果你不想使用 Python 的 imageio-ffmpeg，可以把便携版 FFmpeg 的 ffmpeg.exe 放在此目录：

  tools/ffmpeg/bin/ffmpeg.exe

脚本会自动优先识别，不需要修改 Windows PATH。
如果同时放入 ffprobe.exe，build_content.py 还能自动检测视频分辨率和横/竖屏方向。
