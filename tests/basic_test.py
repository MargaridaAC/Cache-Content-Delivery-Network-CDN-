import time # para gerir os intervalos de tempo
import urllib.request # pedidos htttp (get, put)
import urllib.error # excepções dos pedidos http
import random # para selecionar ficheiros aleatórios

# Isto é um ficheiro de teste da aplicação que cria trafico basico
# How to run:
#   1. executar a aplicação -> ver ./zdocumentation/how-to-run.md
#   2. num terminal separado correr este ficheiro

ORIGIN_URL = "http://localhost:8000"
CDN_URL = "http://localhost:8081"

# um cabeçalho de apresentação (podemos retirar)
def print_banner():
    print("=" * 60)
    print("CDN PERFORMANCE METRICS TRAFFIC SIMULATOR")
    print("=" * 60)
    print(f"Servidor de Origem: {ORIGIN_URL}")
    print(f"Nó de Cache CDN:    {CDN_URL}")
    print("=" * 60 + "\n")


# função que faz os pedidos
def make_request(url, method="GET", data=None, headers=None):
    if headers is None: # cria um dicionario novo para cada request para não passar informações de cabeçalhos, pois modificar o dicionario dentro da funçao iria partilhar e acumular modificações anteriores (dicionários são apenas criados 1 vez em python, quando a função é carregada e não quando é chamada)
        headers = {}
    
    req = urllib.request.Request(url, method=method, headers=headers)

    # caso haja dados para enviar e estes sejam texto, converte para utf-8
    # data pode ser None como conter informações depende da madeira como se faz o pedido
    # se for um metodo get deve ir vazia, se for put vai com o texto do ficheiro
    if data:
        if isinstance(data, str):
            req.data = data.encode("utf-8")
        else:
            req.data = data
            

    start = time.perf_counter()
    try:
        # faz o pedido http com um limite de 5 segundos
        with urllib.request.urlopen(req, timeout=5) as response:
            resp_data = response.read() # lê a resposta enviada pelo servidor
            duration_ms = (time.perf_counter() - start) * 1000
            
            cache_header = response.headers.get("X-Cache", "N/A") # vai buscar ao header se foi HIT ou MISS
            time_header = response.headers.get("X-Response-Time-Ms", "N/A") # vai buscar o tempo de resposta ao header
            
            return { # alguns dados do pedido
                "status": response.status,
                "body_len": len(resp_data),
                "duration_ms": duration_ms,
                "x_cache": cache_header,
                "x_response_time": time_header,
                "error": None
            }
    # erros
    except urllib.error.HTTPError as e:
        duration_ms = (time.perf_counter() - start) * 1000
        return {
            "status": e.code,
            "body_len": 0,
            "duration_ms": duration_ms,
            "x_cache": "ERROR",
            "x_response_time": "N/A",
            "error": str(e)
        }
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        return {
            "status": 500,
            "body_len": 0,
            "duration_ms": duration_ms,
            "x_cache": "ERROR",
            "x_response_time": "N/A",
            "error": str(e)
        }

# conversor de bytes para ficar legivel
def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val/1024:.1f} KB"
    else:
        return f"{bytes_val/(1024*1024):.1f} MB"


def print_result(filename, res):
    status = "HIT " if res["x_cache"] == "HIT" else ("MISS" if res["x_cache"] == "MISS" else "ERRO") # definir o estado
    duration = f"{res['duration_ms']:.1f} ms" # vai buscar tempo
    size = format_size(res["body_len"]) # tamanho do ficheiro que foi enviado pela origem ao cliente após um GET
    print(f"      [{status}] /file/{filename} | Tempo Total: {duration} | Tam: {size}") # formato da mensagem que vai aparecer no terminal 


# função da simulação
def run_simulation():
    print_banner()
    
    # dicionario com ficheiros de varios tamanhos
    sample_files = {
        "relatorio_anual.txt": "Linha de dados de teste para simular um relatorio. " * 300,  # ~15KB
        "imagem_background.png": "Simulando dados binarios de uma imagem leve. " * 1500,   # ~60KB
        "base_dados.bin": "Simulando dados binarios estruturados pesados. " * 6000,          # ~250KB
    }
    
    print("1. A preparar e enviar ficheiros de teste para o Servidor Original...")
    for filename, content in sample_files.items(): # itera entre cada par titulo e conteúdo de cada ficheiro no dicionário
        res = make_request(f"{ORIGIN_URL}/update/{filename}", method="PUT", data=content) #put para cada ficheiro ser enviado para a origem (usa o purge, como fez um "update" de um ficheiro o origin é atualizado e caso exista uma versão na cache é apagada)
        if res["status"] == 200: # dar feedback no terminal 
            print(f"   Ficheiro '{filename}' guardado na Origem ({format_size(len(content))})")
        else:
            print(f"   Falha ao enviar '{filename}': {res['error']}\n")
    
    filenames = list(sample_files.keys())
    
    print("2. A iniciar simulação dinâmica de pedidos ao Nó de Cache CDN...")
    print("-" * 80)
    
    try:
        for cycle in range(1, 5):
            print(f"\n --- Ciclo de Simulação #{cycle} ---")
            
            temp_name = f"pedido_dinamico_{cycle}.txt"
            temp_content = f"Ficheiro unico criado dinamicamente para o ciclo {cycle}. " * 250
            
            # cria um ficheiro novo com a informação acima
            make_request(f"{ORIGIN_URL}/update/{temp_name}", method="PUT", data=temp_content)
            time.sleep(0.3)
            
            print(f"\n   [MISS Esperado] Pedindo '{temp_name}' pela primeira vez:")
            res = make_request(f"{CDN_URL}/file/{temp_name}")
            print_result(temp_name, res)
            
            # Cenário B: Cache HIT (Pedir o mesmo ficheiro de novo)
            time.sleep(0.5)
            print(f"\n   [HIT Esperado] Pedindo '{temp_name}' pela segunda vez:")
            res = make_request(f"{CDN_URL}/file/{temp_name}")
            print_result(temp_name, res)
            
            # Cenário C: HITs consecutivos em ficheiros na origem mas ainda não presentes na cache
            print(f"\n   [1 HIT esperado] Pedindo ficheiros existentes unicamente na origin:")
            for _ in range(4):
                fn = random.choice(filenames)
                res = make_request(f"{CDN_URL}/file/{fn}")
                print_result(fn, res)
                time.sleep(0.4)
            
            # Cenário D: Atualização na Origem -> MQTT PURGE -> Cache MISS
            fn_to_modify = random.choice(filenames)
            print(f"\n   [PURGE + MISS Esperado] Atualizando '{fn_to_modify}' na origem (MQTT PURGE)...")
            new_content = sample_files[fn_to_modify] + f" [Atualização dinâmica do ciclo {cycle}]" # incluir ao conteudo existente no ficheiro escolhido aleatoriamente e juntar "Atualização dinâmica do ciclo ..."
            make_request(f"{ORIGIN_URL}/update/{fn_to_modify}", method="PUT", data=new_content) # fazer o purge e alterar o ficheiro
            print(f"     Ficheiro alterado na origem. Notificação PURGE disparada.")
            
            # Delay para o canal MQTT processar o PURGE
            time.sleep(0.8)
            
            print(f"      Pedindo '{fn_to_modify}' atualizado ao CDN:")
            res = make_request(f"{CDN_URL}/file/{fn_to_modify}") # pedido do ficheiro recentemente alterado
            print_result(fn_to_modify, res)
            
            # Cenário E: Pedido com Erro (Ficheiro não existente)
            if cycle % 2 == 0: # só executa nos ciclos pares
                print(f"\n   [ERRO Esperado] Pedindo ficheiro inexistente:")
                res = make_request(f"{CDN_URL}/file/ficheiro_inexistente.bin")
                print_result("ficheiro_inexistente.bin", res)
                
            time.sleep(2.0)
            
    except KeyboardInterrupt:
        print("\nSimulação terminada pelo utilizador.") # mensagem de finalização pelo user
        
    print("\n" + "=" * 60)
    print("Simulação concluída com sucesso!") # mensagem de teste terminado 
    print("As métricas foram registadas com sucesso em cdn/cache_storage/metrics.csv!")
    print("=" * 60)

if __name__ == "__main__": # executa o teste
    run_simulation()
