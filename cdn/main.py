from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import os
import json
import aiomqtt
from services import fetch_from_origin, get_from_cache, delete_from_cache

MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL", "localhost")

async def mqtt_listener():
    """Background task para ouvir mensagens de PURGE via MQTT"""
    while True:
        try:
            async with aiomqtt.Client(MQTT_BROKER_URL) as client:
                await client.subscribe("cdn/purge")
                print(f"[MQTT] Subscrito no tópico cdn/purge em {MQTT_BROKER_URL}")
                async for message in client.messages:
                    payload = message.payload.decode()
                    try:
                        data = json.loads(payload)
                        filename = data.get("filename")
                        if filename:
                            print(f"[MQTT] Recebido pedido de PURGE para: {filename}")
                            delete_from_cache(filename)
                    except json.JSONDecodeError:
                        print(f"[MQTT] Erro ao descodificar mensagem: {payload}")
        except aiomqtt.MqttError as e:
            print(f"[MQTT] Erro de conexão MQTT: {e}. A tentar de novo em 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[MQTT] Erro inesperado: {e}")
            break

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia a tarefa background no arranque
    task = asyncio.create_task(mqtt_listener())
    yield
    # Cancela a tarefa no encerramento
    task.cancel()

app = FastAPI(title="Nó CDN", lifespan=lifespan)
@app.get("/file/{filename}")
async def cdn_file_controller(filename: str):
    # Tenta a Cache
    path = await get_from_cache(filename)
    
    if path:
        print(f"[HIT] A entregar {filename} da cache.")
        return FileResponse(path)

    # Se falhar, tenta a Origem
    print(f"[MISS] A descarregar {filename} da origem...")
    path = await fetch_from_origin(filename)
    
    if path:
        print(f"[HIT] A entregar {filename} da origem.")
        return FileResponse(path)
    
    # Se falhar em ambos, devolve erro
    raise HTTPException(status_code=404, detail="Ficheiro não encontrado em lado nenhum.")