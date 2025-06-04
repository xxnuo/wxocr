import base64
import os
from typing import Optional

import uvicorn
import wcocr
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from xxhash import xxh64_hexdigest

app = FastAPI()
arch = "aarch64"
wcocr.init(f"./bin/{arch}/wxocr", f"./bin/{arch}")

mem_fs_dir = "/dev/shm/wxocr"
os.makedirs(mem_fs_dir, exist_ok=True)


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建静态文件夹
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 设置模板
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)


class ImageRequest(BaseModel):
    image: str


def extract_image_type(base64_data):
    # Check if the base64 data has the expected prefix
    if base64_data.startswith("data:image/"):
        # Extract the image type from the prefix
        prefix_end = base64_data.find(";base64,")
        if prefix_end != -1:
            return (
                base64_data[len("data:image/") : prefix_end],
                base64_data.split(";base64,")[-1],
            )
    return "png", base64_data


@app.post("/ocr")
async def ocr(image_request: ImageRequest):
    try:
        # Get base64 image from request
        image_data = image_request.image
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")

        # Extract image type from base64 data
        image_type, base64_data = extract_image_type(image_data)
        if not image_type:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Generate unique filename and save image
        filename = os.path.join(mem_fs_dir, f"{xxh64_hexdigest(base64_data)}.{image_type}")
        try:
            image_bytes = base64.b64decode(base64_data)
            with open(filename, "wb") as f:
                f.write(image_bytes)

            # Process image with OCR
            result = wcocr.ocr(filename)
            return {"result": result}

        finally:
            pass
        #     # Clean up temp file
        #     if os.path.exists(filename):
        #         os.remove(filename)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"},
    )


@app.exception_handler(405)
async def method_not_allowed_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=405,
        content={"error": "Method not allowed"},
    )


if __name__ == "__main__":
    # 确保templates目录存在
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    uvicorn.run(app, host="0.0.0.0", port=5000)
