#!/usr/bin/env python3
"""扫描 public/content，自动维护分类并生成 public/data/site-data.json。"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'docs'
CONTENT = PUBLIC / 'content'
DATA = PUBLIC / 'data'
CONFIG = DATA / 'site-config.json'
OUT = DATA / 'site-data.json'
REPORT = DATA / 'content-scan-report.txt'
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp'}
VIDEO_EXT = {'.mp4', '.webm', '.mov', '.m4v'}
COVERS = ('cover.jpg', 'cover.jpeg', 'cover.png', 'cover.webp')

try:
    from PIL import Image
except Exception:
    Image = None
try:
    import qrcode
except Exception:
    qrcode = None
try:
    import imageio_ffmpeg  # type: ignore
except Exception:
    imageio_ffmpeg = None

FFPROBE = shutil.which('ffprobe')
WARN = 0


def natural_key(s):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', str(s))]


def web_path(p):
    return './' + p.relative_to(PUBLIC).as_posix()


def media_files(folder, exts):
    if not folder.is_dir():
        return []
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts and not p.name.startswith('.')],
        key=lambda p: natural_key(p.name),
    )


def warn(msg):
    global WARN
    WARN += 1
    print('  [警告]', msg)


def ratio_close(w, h, a, b, tol=0.035):
    return bool(w and h) and abs(w / h - a / b) <= tol


def check_image_ratio(label, w, h, target, minimum, recommended):
    if not w or not h:
        return
    if not ratio_close(w, h, *target):
        warn(f'{label} 为 {w}×{h}，建议比例 {target[0]}:{target[1]}')
    if w < minimum[0] or h < minimum[1]:
        warn(f'{label} 为 {w}×{h}，低于最低建议 {minimum[0]}×{minimum[1]}（推荐 {recommended[0]}×{recommended[1]}）')


def image_size(path):
    if Image is None:
        return None
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def check_image(path, label, video_orientation=None):
    size = image_size(path)
    if size is None:
        if Image is not None:
            warn(f'{label} 无法读取图片尺寸')
        return
    w, h = size
    if video_orientation == 'landscape':
        check_image_ratio(label, w, h, (16, 9), (1280, 720), (1920, 1080))
    elif video_orientation == 'portrait':
        check_image_ratio(label, w, h, (9, 16), (720, 1280), (1080, 1920))
    else:
        check_image_ratio(label, w, h, (3, 4), (900, 1200), (1200, 1600))


def parse_orientation_value(value):
    """meta 中 0=横版，1=竖版；也兼容英文字符串。"""
    if value in (0, '0', False, 'landscape', 'horizontal', 'h'):
        return 'landscape'
    if value in (1, '1', True, 'portrait', 'vertical', 'v'):
        return 'portrait'
    return None


def orientation_override(meta, path_or_stem):
    mapping = meta.get('mediaOrientation')
    if not isinstance(mapping, dict):
        return None
    key = Path(str(path_or_stem)).stem
    value = mapping.get(key)
    if value is None:
        value = mapping.get(str(path_or_stem))
    return parse_orientation_value(value)


def canonical_aspect(orientation):
    if orientation == 'landscape':
        return round(16 / 9, 6)
    if orientation == 'portrait':
        return round(9 / 16, 6)
    return None


def image_media_info(path, forced_orientation=None):
    size = image_size(path)
    if not size:
        if forced_orientation:
            return {'aspectRatio': canonical_aspect(forced_orientation), 'orientation': forced_orientation}
        return None
    w, h = size
    orientation = forced_orientation or ('landscape' if w >= h else 'portrait')
    aspect = canonical_aspect(forced_orientation) if forced_orientation else round(w / h, 6)
    return {'width': int(w), 'height': int(h), 'aspectRatio': aspect, 'orientation': orientation}


def probe_video(path, label, forced_orientation=None):
    w = h = None
    # 1) 优先使用 ffprobe
    if FFPROBE:
        try:
            r = subprocess.run(
                [FFPROBE, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', str(path)],
                capture_output=True, text=True, timeout=30,
            )
            st = (json.loads(r.stdout or '{}').get('streams') or [{}])[0]
            w, h = st.get('width'), st.get('height')
        except Exception:
            w = h = None

    # 2) Windows 常见场景没有 ffprobe：用 imageio-ffmpeg 读取元信息
    if (not w or not h) and imageio_ffmpeg is not None:
        try:
            gen = imageio_ffmpeg.read_frames(str(path), pix_fmt='rgb24')
            meta = next(gen)
            size = meta.get('size') or meta.get('source_size')
            try:
                gen.close()
            except Exception:
                pass
            if size and len(size) >= 2:
                w, h = int(size[0]), int(size[1])
        except Exception:
            w = h = None

    if not w or not h:
        if forced_orientation:
            return {'aspectRatio': canonical_aspect(forced_orientation), 'orientation': forced_orientation}
        return None

    detected = 'landscape' if w >= h else 'portrait'
    orientation = forced_orientation or detected
    aspect = canonical_aspect(forced_orientation) if forced_orientation else round(w / h, 6)

    if forced_orientation is None:
        if not (ratio_close(w, h, 9, 16) or ratio_close(w, h, 16, 9)):
            warn(f'{label} 为 {w}×{h}，推荐 9:16 竖屏或 16:9 横屏；网站仍会按原比例完整播放')
        if detected == 'portrait' and (w < 720 or h < 1280):
            warn(f'{label} 为 {w}×{h}，竖屏最低建议 720×1280（推荐 1080×1920）')
        if detected == 'landscape' and (w < 1280 or h < 720):
            warn(f'{label} 为 {w}×{h}，横屏最低建议 1280×720（推荐 1920×1080）')

    return {'width': int(w), 'height': int(h), 'aspectRatio': aspect, 'orientation': orientation}


def ensure_qr(site):
    target = DATA / 'contact-qr.jpg'
    value = site.get('qrCode') or (f"tel:{site.get('phone', '')}" if site.get('phone') else '')
    if not value:
        site.pop('qrImage', None)
        return
    if qrcode is None:
        if target.exists():
            print('[提示] 未安装 qrcode，保留现有 contact-qr.jpg')
            site['qrImage'] = './data/contact-qr.jpg'
        else:
            warn('未安装 qrcode，且 contact-qr.jpg 不存在，页脚将没有二维码')
            site.pop('qrImage', None)
        return
    qrcode.make(value).save(target)
    site['qrImage'] = './data/contact-qr.jpg'


def read_meta(folder):
    meta_file = folder / 'meta.json'
    if not meta_file.is_file():
        raise ValueError('缺少 meta.json')
    try:
        meta = json.loads(meta_file.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError as e:
        raise ValueError(f'meta.json 格式错误：第 {e.lineno} 行 {e.msg}')
    if not isinstance(meta, dict):
        raise ValueError('meta.json 必须是 JSON 对象')
    return meta


def collect_categories(folders, existing_categories):
    """根据 meta.json 自动维护 site-config.json 的 categories。"""
    existing = {c.get('id'): c for c in existing_categories if c.get('id')}
    found = {}
    invalid_folders = set()

    for folder in folders:
        try:
            meta = read_meta(folder)
        except Exception as e:
            print(f'  [错误] {folder.name} 分类扫描失败：{e}')
            invalid_folders.add(folder.name)
            continue
        cat_id = str(meta.get('category') or '').strip()
        if not cat_id:
            print(f'  [错误] {folder.name} 缺少 category，已跳过')
            invalid_folders.add(folder.name)
            continue
        old = existing.get(cat_id, {})
        # 分类页签显示名：优先 categoryName（可选显式覆盖），否则使用当前产品 title。
        # category 仅作为内部 ID / 路由键，不直接作为页面显示文字。
        cat_name = str(meta.get('categoryName') or meta.get('title') or old.get('name') or cat_id).strip()
        cat_sort = meta.get('categorySort', meta.get('sort', old.get('sort', 100)))
        if not isinstance(cat_sort, (int, float)):
            cat_sort = 100
        if cat_id in found:
            prev = found[cat_id]
            if cat_name != prev['name']:
                warn(f'系列 {cat_id} 出现不同显示名：“{prev["name"]}” / “{cat_name}”，保留排序更靠前产品的名称')
                if cat_sort < prev['sort']:
                    prev['name'] = cat_name
            prev['sort'] = min(prev['sort'], cat_sort)
        else:
            found[cat_id] = {'id': cat_id, 'name': cat_name, 'sort': cat_sort}

    categories = sorted(found.values(), key=lambda c: (c.get('sort', 100), natural_key(c['id'])))
    return categories, invalid_folders


def product_from(folder, category_ids, type_ids):
    meta = read_meta(folder)
    if not meta.get('title'):
        raise ValueError('缺少 title')
    cat = str(meta.get('category') or '').strip()
    typ = str(meta.get('type') or '').strip()
    if cat not in category_ids:
        raise ValueError(f'category “{cat}” 未被识别')
    if typ not in type_ids:
        raise ValueError(f'type “{typ}” 不存在，可用展示类型：{", ".join(sorted(type_ids))}')

    cover = next((folder / n for n in COVERS if (folder / n).is_file()), None)
    if cover:
        check_image(cover, f'{folder.name}/{cover.name}')
    else:
        warn(f'{folder.name} 没有 cover，将使用视频/图片预览或占位')
    cover_url = web_path(cover) if cover else ''

    video_files = media_files(folder / 'videos', VIDEO_EXT)
    video_info_map = {}
    for f in video_files:
        forced = orientation_override(meta, f.stem)
        video_info_map[f.stem] = probe_video(f, f'{folder.name}/videos/{f.name}', forced)

    images = []
    for f in media_files(folder / 'images', IMAGE_EXT):
        forced = orientation_override(meta, f.stem)
        # 自动截帧图片与同名视频共用方向；普通图片则读取自身尺寸。
        inherited = (video_info_map.get(f.stem) or {}).get('orientation')
        display_orientation = forced or inherited
        check_image(f, f'{folder.name}/images/{f.name}', display_orientation)
        info = image_media_info(f, display_orientation)
        item = {'title': f.stem, 'url': web_path(f)}
        if info:
            item.update(info)
        images.append(item)

    posters = {f.stem: f for f in media_files(folder / 'posters', IMAGE_EXT)}
    videos = []
    for f in video_files:
        info = video_info_map.get(f.stem)
        poster = posters.get(f.stem)
        forced = orientation_override(meta, f.stem)
        if poster:
            poster_info = image_media_info(poster, forced or (info or {}).get('orientation'))
            # 如果视频无法读取宽高，则用同名 poster 的实际比例兜底。
            if not info and poster_info:
                info = poster_info
            check_image(poster, f'{folder.name}/posters/{poster.name}', (info or {}).get('orientation'))
        item = {'title': f.stem, 'url': web_path(f), 'poster': web_path(poster) if poster else cover_url}
        if info:
            item.update(info)
        videos.append(item)

    tags = meta.get('tags') if isinstance(meta.get('tags'), list) else []
    return {
        'id': folder.name,
        'category': cat,
        'type': typ,
        'title': str(meta['title']),
        'description': str(meta.get('description', '')),
        'tags': [str(x) for x in tags],
        'cover': cover_url,
        'images': images,
        'videos': videos,
        'sort': meta.get('sort', 100) if isinstance(meta.get('sort', 100), (int, float)) else 100,
        'enabled': meta.get('enabled', True) is not False,
    }


def sync_runtime(dest):
    dest = Path(dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    for item in ['index.html', 'assets']:
        src, dst = ROOT / item, dest / item
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.exists():
            shutil.copy2(src, dst)
    (dest / 'data').mkdir(exist_ok=True)
    shutil.copy2(OUT, dest / 'data/site-data.json')
    qr = DATA / 'contact-qr.jpg'
    if qr.exists():
        shutil.copy2(qr, dest / 'data/contact-qr.jpg')
    if CONTENT.is_dir():
        shutil.copytree(CONTENT, dest / 'content', dirs_exist_ok=True, ignore=shutil.ignore_patterns('_template'))
    print('已同步运行文件到：', dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dist', help='同步运行文件到部署目录，例如 dist 或 /var/www/robot-showcase')
    args = ap.parse_args()

    try:
        cfg = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    except Exception as e:
        print('[错误] 读取 site-config.json 失败：', e)
        return 1

    site = cfg.get('site', {})
    site.setdefault('pageSize', 12)
    types = cfg.get('types', [])
    type_ids = {t.get('id') for t in types if t.get('id')}
    if not type_ids:
        print('[错误] site-config.json 缺少 types')
        return 1

    folders = sorted(
        [d for d in CONTENT.iterdir() if d.is_dir() and not d.name.startswith(('_', '.'))],
        key=lambda d: natural_key(d.name),
    ) if CONTENT.exists() else []

    categories, category_invalid = collect_categories(folders, cfg.get('categories', []))
    cfg['categories'] = categories
    cfg['site'] = site
    cfg['types'] = types
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[配置] site-config.json 已自动同步系列分类：{len(categories)} 个')

    category_ids = {c['id'] for c in categories}
    ensure_qr(site)
    if Image is None:
        print('[提示] 未安装 Pillow，跳过图片尺寸检查')
    if not FFPROBE:
        print('[提示] 未找到 ffprobe，跳过视频尺寸检查')

    products = []
    scanned = skipped = 0
    report_lines = []
    for folder in folders:
        scanned += 1
        print('扫描：', folder.name)
        report_lines.append(f'[{folder.name}]')
        if folder.name in category_invalid:
            skipped += 1
            print('  [错误] 已跳过：meta.json 无法用于生成分类')
            report_lines.append('状态：失败 - meta.json 无法用于生成分类')
            report_lines.append('')
            continue
        try:
            product = product_from(folder, category_ids, type_ids)
            products.append(product)
            report_lines.append(f"状态：成功 | category={product.get('category')} | type={product.get('type')} | images={len(product.get('images', []))} | videos={len(product.get('videos', []))}")
            report_lines.append('')
        except Exception as e:
            skipped += 1
            print('  [错误] 已跳过：', e)
            report_lines.append(f'状态：失败 - {e}')
            report_lines.append('')

    products.sort(key=lambda p: (p.get('sort', 100), natural_key(p.get('id', ''))))
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({'site': site, 'categories': categories, 'types': types, 'products': products}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    REPORT.write_text('\n'.join(report_lines), encoding='utf-8')

    print('\n========== 生成完成 ==========')
    print('扫描产品数：', scanned)
    print('成功产品数：', scanned - skipped)
    print('跳过产品数：', skipped)
    print('系列分类数：', len(categories))
    print('图片总数：', sum(len(p.get('images', [])) for p in products))
    print('视频总数：', sum(len(p.get('videos', [])) for p in products))
    print('尺寸警告数：', WARN)
    print('已更新：', CONFIG)
    print('输出：', OUT)
    print('扫描报告：', REPORT)

    if args.dist:
        sync_runtime(args.dist)
    return 0


if __name__ == '__main__':
    sys.exit(main())
