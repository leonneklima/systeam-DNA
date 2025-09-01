from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Minha API Rápida")

# Modelo de dados
class Item(BaseModel):
    id: int
    nome: str
    preco: float

# Banco de dados em memória (simples)
db = []

# Rota inicial
@app.get("/")
def home():
    return {"mensagem": "Bem-vindo à API!"}

# Listar todos os itens
@app.get("/itens")
def listar_itens():
    return db

# Buscar um item por ID
@app.get("/itens/{item_id}")
def buscar_item(item_id: int):
    for item in db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item não encontrado")

# Adicionar um novo item
@app.post("/itens")
def adicionar_item(item: Item):
    for existente in db:
        if existente.id == item.id:
            raise HTTPException(status_code=400, detail="ID já existe")
    db.append(item)
    return {"mensagem": "Item adicionado com sucesso", "item": item}
