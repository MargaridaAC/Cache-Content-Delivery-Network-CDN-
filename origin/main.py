from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Servidor Original")

# Diretório onde os ficheiros originais estão guardados
DATA_DIR = "data"

@app.get("/")
def read_root():
    return {"message": "Servidor Original está ativo."}

@app.get("/{filename}")
def get_file(filename: str):
    """
    Endpoint que serve um ficheiro específico.
    Se o ficheiro não existir, devolve um erro 404.
    """
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Ficheiro não encontrado no Servidor Original")
    
    # FileResponse lida automaticamente com ficheiros grandes, 
    # enviando em chunks apropriados.
    return FileResponse(file_path)
