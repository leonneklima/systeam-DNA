from fastapi import FastAPI, UploadFile, File
import shutil
import uuid
import os
from app.predictor import predict_species

app = FastAPI(
    title="Sistema de Análise de Fósseis",
    description="API para identificar espécies fósseis do Pleistoceno",
    version="1.0.0"
)

UPLOAD_DIR = "tmp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze_fossil(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.jpg")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = predict_species(file_path)

    os.remove(file_path)

    return {
        "status": "sucesso",
        "resultado": result
    }

@app.get("/")
def home():
    return {"mensagem": "API do Sistema de Análise de Fósseis ativa!"}
