import os
import aiofiles
from datetime import datetime

METRICS_FILE = "cache_storage/metrics.csv"

# Certifica que a diretoria da cache existe
os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)


# A VEEEER -------------------------------------------------------------------
# Escreve o cabeçalho se o ficheiro de métricas ainda não existir
if not os.path.exists(METRICS_FILE):
    with open(METRICS_FILE, mode="w", newline="", encoding="utf-8") as f:
        f.write("timestamp,filename,cache_status,response_time_ms,file_size_bytes,origin_fetch_time_ms\n")
# --------------------------------------------------------------------------------

# funçao que escreve no metrics.csv
async def log_metric(
    filename: str,
    cache_status: str,
    response_time_ms: float,
    file_size_bytes: int,
    origin_fetch_time_ms: float
):
    """
    Regista assincronamente os detalhes do pedido no ficheiro metrics.csv.
    """
    timestamp = datetime.now().isoformat()
    # Limpa possíveis vírgulas no nome do ficheiro para não corromper o CSV
    safe_filename = filename.replace(",", "_")
    
    row = [
        timestamp,
        safe_filename,
        cache_status,
        f"{response_time_ms:.2f}",
        str(file_size_bytes),
        f"{origin_fetch_time_ms:.2f}"
    ]
    line = ",".join(row) + "\n"
    
    try:
        async with aiofiles.open(METRICS_FILE, mode="a", encoding="utf-8") as f:
            await f.write(line)
    except Exception as e:
        print(f"[METRIC LOGGER ERROR] Não foi possível registar a métrica: {e}")
