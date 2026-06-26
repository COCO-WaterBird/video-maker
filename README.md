# video-maker

图片一键生成视频，支持三种模式：横屏运镜、竖屏运镜、轮播。

---

## 环境准备

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate    # macOS / Linux
# venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt
```

---

## 快速开始

图片放进 `uploads/` 目录（支持 `.jpg .png .jpeg .gif .webp`），然后运行：

```bash
# 横屏 1920x1080（Ken Burns 从左往右平移 + 叠化转场）
python run_video.py --mode land

# 竖屏 1080x1920（Ken Burns 从左往右平移 + 叠化转场）
python run_video.py --mode shorts

# 轮播 1080x1920（等比 cover 居中裁剪，不做运镜）
python run_video.py --mode slideshow
```

生成的视频默认放在 `output/` 目录。

---

## 常用参数

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--uploads-dir` | 图片所在目录 | `uploads` |
| `--output-dir` | 输出目录 | `output` |
| `--similarity-threshold` | 相似图去重强度（6~20，越大去得越狠） | `12` |
| `--second-per-image` | slideshow 每张图停留秒数 | `2.0` |
| `--transition` | 转场方式：`fade` `dissolve` `slideleft` `slideright` | `dissolve` |
| `--transition-duration` | 转场时长（秒） | `0.45` |
| `--zoom-factor` | Ken Burns 缩放系数（1.0=不缩放，建议 1.02~1.08） | `1.05` |
| `--pan-ratio` | 平移幅度（0~1），1.0=走满整个可裁剪距离 | `1.0` |
| `--random-seed` | 随机节奏种子，改了会换节奏 | `7` |

### 示例

```bash
# 竖屏，每张图 1.5 秒
python run_video.py --mode shorts --second-per-image 1.5

# 横屏，去重更严格，不用 zoom
python run_video.py --mode land --similarity-threshold 20 --zoom-factor 1.0

# 竖屏轮播，每张 3 秒
python run_video.py --mode slideshow --second-per-image 3.0 --view-w 1080 --view-h 1920
```

---

## 三种模式对比

| 模式 | 画布 | 运镜 | 转场 | 适合场景 |
|---|---|---|---|---|
| `land` | 1920×1080 横屏 | Ken Burns 从左→右线性平移 | dissolve 叠化 | YouTube 横向视频 |
| `shorts` | 1080×1920 竖屏 | Ken Burns 从左→右线性平移 | dissolve 叠化 | TikTok / Reels / Shorts |
| `slideshow` | 1080×1920 竖屏（可改） | 无运镜，等比 cover 居中 | 无转场，直接切 | 产品图册、简单轮播 |

---

## Web 接口（可选）

如果你需要用浏览器界面：

```bash
uvicorn app.main:app --reload
```

然后访问：

| 接口 | 说明 |
|---|---|
| `GET /land/generate-video` | 生成横屏视频 |
| `GET /shorts/generate-video` | 生成竖屏视频 |
| `GET /slideshow/generate-video` | 生成轮播视频 |

可选 Query 参数同命令行参数。

---

## 依赖

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/)（需提前安装并加入 PATH）
- imagehash（感知哈希去重）
- Pillow（图片处理）
- FastAPI + Uvicorn（仅 Web 模式需要）
