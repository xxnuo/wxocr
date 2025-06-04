import os

import uvicorn
import wcocr
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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


class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: list[float]


class OCRResponse(BaseModel):
    results: list[OCRResult]


@app.post("/ocr", response_model=OCRResponse)
async def super_speed_ocr_service(file: UploadFile):
    if not file or file.size == 0:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # 保存上传的文件到临时目录
        file_data = await file.read()
        file_path = os.path.join(mem_fs_dir, xxh64_hexdigest(file_data))
        with open(file_path, "wb") as f:
            f.write(file_data)

        try:
            ocr_result = wcocr.ocr(file_path)
            errcode = ocr_result.get("errcode", -1)
            if errcode != 0:
                raise HTTPException(status_code=500, detail=errcode)

            # 处理OCR结果
            items = []
            for item in ocr_result.get("ocr_response", []):
                items.append(
                    OCRResult(
                        text=item["text"],
                        confidence=item["rate"],
                        bbox=[item["left"], item["top"], item["right"], item["bottom"]],
                    )
                )

            return OCRResponse(results=items)
        finally:
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    # 创建静态文件夹
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 设置模板
    templates_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "templates"
    )
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    templates = Jinja2Templates(directory=templates_dir)

    uvicorn.run(app, host="0.0.0.0", port=5000)
