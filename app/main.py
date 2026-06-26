from fastapi import FastAPI, HTTPException

from app.services.ffmpeg_service import generate_slideshow_from_images, generate_video_from_images

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "video-maker is running"}


@app.get("/generate-video")
def generate_video(similarity_threshold: int = 12):
    """
    similarity_threshold: 相似图去重强度，6~20，越大去掉的「看起来像」的镜头越多（默认 12）。
    """
    try:
        output_path = generate_video_from_images(similarity_threshold=similarity_threshold)
        return {
            "message": "video generated successfully",
            "output": output_path,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/land/generate-video")
def generate_video_land(similarity_threshold: int = 12):
    """
    横屏 1920x1080（Land 调用）
    """
    try:
        output_path = generate_video_from_images(
            similarity_threshold=similarity_threshold,
            view_w=1920,
            view_h=1080,
            output_filename="test_video_land.mp4",
        )
        return {
            "message": "video generated successfully (land)",
            "output": output_path,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/shorts/generate-video")
def generate_video_shorts(similarity_threshold: int = 12):
    """
    竖屏 1080x1920（Shorts 调用）
    """
    try:
        output_path = generate_video_from_images(
            similarity_threshold=similarity_threshold,
            view_w=1080,
            view_h=1920,
            output_filename="test_video_shorts.mp4",
        )
        return {
            "message": "video generated successfully (shorts)",
            "output": output_path,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/slideshow/generate-video")
def generate_video_slideshow(
    similarity_threshold: int = 12,
    second_per_image: float = 2.0,
    view_w: int = 1080,
    view_h: int = 1920,
):
    """
    slideshow 模式：按顺序轮播图片（等比 cover + 居中裁剪，不做运镜）
    默认竖屏 1080x1920（Shorts 方向）。
    """
    try:
        output_path = generate_slideshow_from_images(
            similarity_threshold=similarity_threshold,
            second_per_image=second_per_image,
            view_w=view_w,
            view_h=view_h,
            output_filename="test_video_slideshow.mp4",
        )
        return {
            "message": "video generated successfully (slideshow)",
            "output": output_path,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))