# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import os
import json
# pyrefly: ignore [missing-import]
import aiomqtt
import time
from services import fetch_from_origin, get_from_cache, delete_from_cache
from metrics import log_metric

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
    # inicia o contador de tempo (marca o inicio da operação total)
    start_time = time.perf_counter()
    origin_fetch_time_ms = 0.0 # pois não chega a ir buscar à origem

    # Tenta a Cache
    path = await get_from_cache(filename)
    
    if path: # caso encontre na cache
        # tempo em milissegundos caso der HIT, ou seja, vá buscar o ficheiro à cache (tempo atual - tempo inicial)
        response_time_ms = (time.perf_counter() - start_time) * 1000
        file_size = os.path.getsize(path)
        print(f"[HIT] A entregar {filename} da cache ({response_time_ms:.2f}ms).")
        
        # envia as informações da operação para o ficheiro metrics.csv (ver função em metrics.py)
        await log_metric(
            filename=filename,
            cache_status="HIT",
            response_time_ms=response_time_ms,
            file_size_bytes=file_size,
            origin_fetch_time_ms=0.0
        )
        
        headers = {
            "X-Cache": "HIT",
            "X-Response-Time-Ms": f"{response_time_ms:.2f}"
        }
        return FileResponse(path, headers=headers)

    # Se falhar, tenta a Origem
    print(f"[MISS] A descarregar {filename} da origem...")

    # contador de tempo na origem
    origin_start = time.perf_counter()

    # vai pesquisar à origem ver função em services.py
    path = await fetch_from_origin(filename)

    # tempo que demorou a ir buscar o ficheiro à origem
    origin_fetch_time_ms = (time.perf_counter() - origin_start) * 1000
    
    if path: # caso encontre na origem 
        response_time_ms = (time.perf_counter() - start_time) * 1000
        file_size = os.path.getsize(path)
        print(f"[HIT] A entregar {filename} da origem ({response_time_ms:.2f}ms, origem: {origin_fetch_time_ms:.2f}ms).")
        
        await log_metric(
            filename=filename,
            cache_status="MISS",
            response_time_ms=response_time_ms,
            file_size_bytes=file_size,
            origin_fetch_time_ms=origin_fetch_time_ms
        )
        
        headers = {
            "X-Cache": "MISS",
            "X-Response-Time-Ms": f"{response_time_ms:.2f}"
        }
        return FileResponse(path, headers=headers)
    
    # Se falhar em ambos, devolve erro
    response_time_ms = (time.perf_counter() - start_time) * 1000 # tempo de erro
    await log_metric(
        filename=filename,
        cache_status="ERROR",
        response_time_ms=response_time_ms,
        file_size_bytes=-1,
        origin_fetch_time_ms=origin_fetch_time_ms
    )
    raise HTTPException(status_code=404, detail="Ficheiro não encontrado em lado nenhum.")