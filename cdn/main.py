from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from services import fetch_from_origin, get_from_cache

app = FastAPI(title="Nó CDN")

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