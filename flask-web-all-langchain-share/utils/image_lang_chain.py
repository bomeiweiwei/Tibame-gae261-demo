import base64
from pathlib import Path


def image4LangChain(image_url):
    image_url = str(image_url)

    if image_url.startswith("http"):
        return {"url": image_url}

    image_path = Path(image_url)

    if not image_path.exists():
        raise FileNotFoundError(f"找不到圖片：{image_path.resolve()}")

    # 副檔名對應 MIME Type
    image_mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }

    suffix = image_path.suffix.lower()

    mime_type = image_mime_types.get(suffix)

    if mime_type is None:
        raise ValueError(f"不支援的圖片格式：{suffix}")

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    return {
        "url": f"data:{mime_type};base64,{image_data}"
    }