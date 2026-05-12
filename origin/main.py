from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import os
import json
import paho.mqtt.publish as publish

app = FastAPI(title="Servidor Original")

# Configuração MQTT
MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL", "localhost")

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

@app.put("/update/{filename}")
async def update_file(filename: str, request: Request):
    """
    Endpoint para atualizar um ficheiro. Guarda o novo ficheiro
    no disco e envia um sinal MQTT "PURGE" para a CDN.
    """
    file_path = os.path.join(DATA_DIR, filename)
    content = await request.body()
    
    # Guarda o ficheiro no disco
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Publica a mensagem de PURGE no MQTT
    payload = json.dumps({"filename": filename})
    try:
        publish.single("cdn/purge", payload, hostname=MQTT_BROKER_URL)
        print(f"[{filename}] PURGE enviado via MQTT para o tópico cdn/purge")
    except Exception as e:
        print(f"Erro ao publicar MQTT: {e}")
        
    return {"message": f"Ficheiro {filename} atualizado com sucesso e notificação de PURGE enviada."}
