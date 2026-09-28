#!/usr/bin/env python3
"""从 public/content 下的视频提取首帧，自动生成 posters 和 images。"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / 'public' / 'content'
VIDEO_EXT = {'.mp4', '.webm', '.mov', '.m4v'}
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp'}
def find_ffmpeg():
    # 1) System PATH
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    # 2) Project-local portable ffmpeg
    candidates = [
        ROOT / 'tools' / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
        ROOT / 'tools' / 'ffmpeg' / 'ffmpeg.exe',
        ROOT / 'tools' / 'ffmpeg' / 'bin' / 'ffmpeg',
        ROOT / 'tools' / 'ffmpeg' / 'ffmpeg',
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    # 3) Python package imageio-ffmpeg (bundles its own ffmpeg binary)
    try:
        import imageio_ffmpeg  # type: ignore
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    return None

FFMPEG = find_ffmpeg()
FFPROBE = shutil.which('ffprobe')


def natural_key(s: str):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', s)]


def media_files(folder: Path, exts):
    if not folder.is_dir():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts and not p.name.startswith('.')], key=lambda p: natural_key(p.name))


def probe_video(path: Path):
    if not FFPROBE:
        return None
    try:
        r = subprocess.run([
            FFPROBE, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', str(path)
        ], capture_output=True, text=True, timeout=30)
        line = (r.stdout or '').strip()
        if not line or 'x' not in line:
            return None
        w, h = [int(x) for x in line.split('x', 1)]
        if not w or not h:
            return None
        return {'width': w, 'height': h, 'orientation': 'landscape' if w >= h else 'portrait'}
    except Exception:
        return None


def extract_frame(video: Path, out: Path, orientation: str | None):
    out.parent.mkdir(parents=True, exist_ok=True)
    vf = None
    if orientation == 'portrait':
        vf = "scale=-2:'if(gt(ih,1920),1920,ih)'"
    elif orientation == 'landscape':
        vf = "scale='if(gt(iw,1920),1920,iw)':-2"
    cmd = [FFMPEG, '-y', '-i', str(video), '-frames:v', '1']
    if vf:
        cmd += ['-vf', vf]
    cmd += ['-q:v', '2', str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0


def image_exists_with_same_stem(folder: Path, stem: str):
    if not folder.is_dir():
        return False
    for ext in IMAGE_EXT:
        if (folder / f'{stem}{ext}').exists():
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description='从视频提取首帧到 posters 与 images')
    ap.add_argument('--overwrite', action='store_true', help='覆盖已存在的同名 jpg')
    ap.add_argument('--only', choices=['posters', 'images', 'both'], default='both', help='只生成哪一类图片')
    args = ap.parse_args()

    if not FFMPEG:
        print('[错误] 未找到可用的 FFmpeg，无法提取视频首帧。')
        print('Windows 推荐：双击项目根目录 setup-video-tools.bat，然后重新运行 update-content.bat。')
        print('也可以手动执行：py -m pip install imageio-ffmpeg')
        print('或者把便携版 ffmpeg.exe 放到 tools/ffmpeg/bin/ffmpeg.exe。')
        return 1
    print(f'[视频工具] 使用 FFmpeg：{FFMPEG}')

    scanned = generated_posters = generated_images = skipped = failed = 0
    folders = sorted([d for d in CONTENT.iterdir() if d.is_dir() and not d.name.startswith(('_', '.'))], key=lambda d: natural_key(d.name)) if CONTENT.exists() else []
    for product in folders:
        videos_dir = product / 'videos'
        posters_dir = product / 'posters'
        images_dir = product / 'images'
        videos = media_files(videos_dir, VIDEO_EXT)
        if not videos:
            continue
        print(f'处理产品：{product.name}')
        for video in videos:
            scanned += 1
            stem = video.stem
            info = probe_video(video) or {}
            orientation = info.get('orientation')
            if orientation:
                print(f'  视频：{video.name} ({info.get("width")}×{info.get("height")}, {orientation})')
            else:
                print(f'  视频：{video.name}')

            if args.only in ('posters', 'both'):
                poster_out = posters_dir / f'{stem}.jpg'
                if (not args.overwrite) and image_exists_with_same_stem(posters_dir, stem):
                    print(f'    [跳过] poster 已存在：{stem}')
                    skipped += 1
                else:
                    ok = extract_frame(video, poster_out, orientation)
                    if ok:
                        print(f'    [生成] poster -> {poster_out.relative_to(ROOT)}')
                        generated_posters += 1
                    else:
                        print(f'    [失败] poster 生成失败：{video.name}')
                        failed += 1

            if args.only in ('images', 'both'):
                image_out = images_dir / f'{stem}.jpg'
                if (not args.overwrite) and image_exists_with_same_stem(images_dir, stem):
                    print(f'    [跳过] image 已存在：{stem}')
                    skipped += 1
                else:
                    ok = extract_frame(video, image_out, orientation)
                    if ok:
                        print(f'    [生成] image  -> {image_out.relative_to(ROOT)}')
                        generated_images += 1
                    else:
                        print(f'    [失败] image 生成失败：{video.name}')
                        failed += 1

    print('\n========== 提取完成 ==========')
    print('视频总数：', scanned)
    print('新增 poster：', generated_posters)
    print('新增 image：', generated_images)
    print('跳过：', skipped)
    print('失败：', failed)
    print('说明：默认不覆盖已存在文件；如需重建，请加 --overwrite')
    return 0 if failed == 0 else 2

if __name__ == '__main__':
    sys.exit(main())
