# 机器人产品多媒体展示站 V9（正式素材版）

纯静态网站，无后台、无数据库。正式内容统一放在 `public/content/`，运行更新脚本后自动生成网站数据。

## V9 关键变化

- 已移除所有演示产品、白素贞示例素材和 legacy 演示数据。
- `site-config.json` 的 `categories`（机器人系列）由更新脚本根据各产品 `meta.json` 自动维护。
- `types`（对话展示 / 身体局部特写 / 全身展示）仍在 `site-config.json` 手工维护。
- 列表预览优先级：**视频 > 图片 > Cover > 占位**。
- 视频支持 **9:16 竖屏**、**16:9 横屏**及其他比例，均完整播放不裁切。
- `update-content` 会先从视频首帧自动生成 `posters/` 与 `images/`，再更新配置和数据。

## 新增正式内容

复制：

```text
public/content/_template/
```

为：

```text
public/content/<product-key>/
```

例如：

```text
public/content/bai-suzhen-fullbody/
```

`meta.json`：

```json
{
  "title": "白素贞全身展示",
  "category": "bai-suzhen",
  "description": "产品外观与动作展示",
  "tags": ["白素贞", "机器人"],
  "sort": 100,
  "enabled": true,
  "type": "fullbody"
}
```

字段说明：

- `category`：内部分类 ID / 路由键，推荐英文、数字、短横线；不会直接显示在页面上。
- `title`：默认同时作为顶部分类页签的显示名称。
- `categoryName`：可选；只有当你希望分类页签名称与 `title` 不同的时候才填写。
- `categorySort`：可选；未填写时自动使用 `sort` 作为分类排序。
- `type`：展示类型 ID，对应 `site-config.json` 的 `types`。
- `sort`：产品排序，允许重复，数值越小越靠前。

同一个分类如果包含多个内容，请让它们使用相同 `category`。默认页签名称取该分类中排序最靠前产品的 `title`；如需固定名称，可填写相同的 `categoryName`：

```text
bai-suzhen-fullbody -> category=bai-suzhen, type=fullbody
bai-suzhen-detail   -> category=bai-suzhen, type=detail
bai-suzhen-dialogue -> category=bai-suzhen, type=dialogue
```

运行 `update-content` 后，脚本会自动把 `白素贞` 加入 `site-config.json.categories`，不需要你手工维护系列分类。

## Windows（PowerShell 7 推荐）

首次使用：

```text
setup-video-tools.bat
check-environment.bat
```

以后更新：

```text
update-content.bat
```

本地预览：

```text
start-local.bat
```

## Linux / macOS

```bash
bash update-content.sh
bash start-local.sh
```

## update-content 做什么

1. 扫描 `videos/`，提取视频第一帧。
2. 自动生成同名 `posters/*.jpg`。
3. 自动生成同名 `images/*.jpg`。
4. 扫描全部 `meta.json`。
5. 自动更新 `public/data/site-config.json` 中的 `categories`。
6. 自动生成 `public/data/site-data.json`。
7. 网站刷新后自动显示新增内容、分类数量和分页。

**不要直接手改 `site-data.json`。**

## 素材规则

- 普通产品封面/图片：建议 3:4，推荐 1200×1600，最低 900×1200。
- 竖屏视频：建议 9:16，推荐 1080×1920，最低 720×1280。
- 横屏视频：建议 16:9，推荐 1920×1080，最低 1280×720。
- 视频建议 MP4 / H.264 / AAC / 30fps。
- 视频首帧生成的 `images` 会保留视频自身横竖比例，不强制裁成 3:4。

详细说明：

- `docs/素材规范与上传流程.md`
- `docs/服务器部署说明.md`
- `docs/V2数据模型说明.md`


## Windows 更新脚本 V10 修复说明
V10 修复了 PowerShell 将 Python 控制台输出误当成退出码的问题。
现在 `update-content.bat` 会：

1. 生成视频首帧；即使这一步失败，也只警告，不会阻止数据生成。
2. 执行 `build_content.py` 更新 `site-config.json` 与 `site-data.json`。
3. 生成 `public/data/content-scan-report.txt`，逐目录列出成功/失败原因。

如果 `meta.json` 中没有 `categoryName`，脚本仍能生成数据，但顶部分类名称会临时使用 `category` 的 id。建议正式素材填写：

```json
{
  "category": "xiongbu-fubu",
  "categoryName": "胸部腹部",
  "categorySort": 100
}
```


## Windows PowerShell 编码说明（V11）
V11 已将所有 `.ps1` 脚本统一为 **UTF-8 无 BOM**，`.bat` 启动器保持纯 ASCII。
这样可以避免 PowerShell 7 把 BOM 隐藏字符误识别为命令名的问题。

如果你是从旧版本升级，建议直接覆盖以下文件：

```text
windows-common.ps1
start-local.ps1
update-content.ps1
generate-stills.ps1
setup-video-tools.ps1
check-environment.ps1
以及对应的 .bat 启动器
```

推荐使用顺序：

```text
1. check-environment.bat
2. setup-video-tools.bat（仅首次需要）
3. update-content.bat
4. start-local.bat
```


## V12 分类显示规则

运行 `update-content.bat` 后，脚本会自动维护 `public/data/site-config.json -> categories`。

规则：

```text
category     = 内部 ID / 路由键
title        = 默认分类显示名称
categoryName = 可选显示名覆盖
sort         = 产品排序，同时作为默认分类排序
categorySort = 可选分类排序覆盖
```

例如：

```json
{
  "title": "胸部腹部特写",
  "category": "xiongbu-fubu",
  "description": "胸部腹部特写",
  "tags": ["胸部", "腹部"],
  "sort": 101,
  "enabled": true,
  "type": "detail"
}
```

自动生成：

```json
{
  "id": "xiongbu-fubu",
  "name": "胸部腹部特写",
  "sort": 101
}
```

因此页面显示“胸部腹部特写”，不会显示 `xiongbu-fubu`。


## V13：同一产品内横竖素材混合
视频、Poster、图片可以在同一个产品目录里同时包含 16:9 横版和 9:16 竖版。页面会为**每一个媒体文件分别计算比例**，不会再把所有视频卡片固定成 9:16。

通常无需手工配置：
- 视频：优先通过 ffprobe / imageio-ffmpeg 自动读取宽高。
- Poster、图片：通过 Pillow 自动读取宽高。
- 浏览器端还有一次图片实际尺寸兜底，会根据图片 naturalWidth / naturalHeight 修正卡片比例。

如果你希望明确强制某个文件使用横版/竖版，可在对应产品的 `meta.json` 加：

```json
{
  "title": "胸部腹部特写",
  "category": "xiongbu-fubu",
  "type": "detail",
  "sort": 101,
  "enabled": true,
  "mediaOrientation": {
    "胸部腹部特写1": 0,
    "胸部腹部特写2": 1
  }
}
```

其中：
- `0` = 横版 16:9
- `1` = 竖版 9:16
- key 使用**文件名去掉扩展名后的名称**。
- 同名的 `videos/胸部腹部特写1.mp4`、`posters/胸部腹部特写1.jpg`、`images/胸部腹部特写1.jpg` 会共用这一条方向配置，因此不用写三遍。
- `mediaOrientation` 是可选项；不写就自动识别。
