import os
import httpx
import aiofiles

CACHE_DIR = "cache_storage"
ORIGIN_URL = os.getenv("ORIGIN_URL", "http://localhost:8000")

# Verifica se a pasta de cache existe
os.makedirs(CACHE_DIR, exist_ok=True)

async def get_from_cache(filename: str):
    """Verifica se o ficheiro existe localmente."""
    file_path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(file_path):
        return file_path
    return None

# Esta função pode ser melhorada usando streaming para ficheiros grandes
async def fetch_from_origin(filename: str):
    """Vai buscar à origem e guarda no disco assincronamente."""
    target_path = os.path.join(CACHE_DIR, filename)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ORIGIN_URL}/{filename}")
            if response.status_code == 200:
                # Escrita assíncrona para não bloquear o servidor
                async with aiofiles.open(target_path, mode="wb") as f:
                    await f.write(response.content)
                return target_path
            return None
        except httpx.HTTPError as e:
            print(f"Erro ao ir buscar {filename} da origem: {e}")
            return None