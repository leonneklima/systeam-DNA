from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import tempfile
import os
from datetime import datetime
from app.predictor import predict_species

app = FastAPI(
    title="Sistema de Análise de Fósseis",
    description="API para identificar espécies fósseis do Pleistoceno",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_fossil(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie apenas imagens.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = predict_species(tmp_path)
    finally:
        os.remove(tmp_path)

    return {
        "status": "sucesso",
        "arquivo": file.filename,
        "analisado_em": datetime.utcnow().isoformat(),
        "resultado": result
    }

@app.get("/")
def home():
    return {"mensagem": "API do Sistema de Análise de Fósseis ativa!"}
