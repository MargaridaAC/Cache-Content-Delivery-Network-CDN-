from datetime import datetime
import os
import sys
import csv

def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val/1024:.2f} KB"
    else:
        return f"{bytes_val/(1024*1024):.2f} MB" # same as in basic_test.py

def find_metrics_file():
    # Se o utilizador fornecer o caminho como argumento
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            return arg_path
        print(f"Caminho fornecido não existe: '{arg_path}'. A procurar fallbacks...")

    possible_paths = [
        "cdn/cache_storage/metrics.csv", # Executado a partir da raiz do projeto
        "../cdn/cache_storage/metrics.csv", # Executado de dentro da pasta data_processing
        "cache_storage/metrics.csv", # Executado de dentro da pasta cdn
        "metrics.csv" # Copiado para a pasta local
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    return None

def generate_report_text(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f) #lê cada linha do csv como dicionario e as chaves vẽem do cabeçalho
        rows = list(reader) # lista de dicionarios
        
    # verificar se o ficheiro está vazio
    if not rows:
        return "O ficheiro metrics.csv está vazio."

    # Cálculos gerais
    total_requests = len(rows)
    hits = [r for r in rows if r["cache_status"] == "HIT"]
    misses = [r for r in rows if r["cache_status"] == "MISS"]
    errors = [r for r in rows if r["cache_status"] == "ERROR"]
    
    hits_count = len(hits)
    misses_count = len(misses)
    errors_count = len(errors)
    
    # percentagem de hits, mas se a soma der 0 dá 0.0
    hit_rate = (hits_count / (hits_count + misses_count) * 100) if (hits_count + misses_count) > 0 else 0.0
    
    # Latências (Tempos de resposta)
    hit_latencies = [float(r["response_time_ms"]) for r in hits]
    miss_latencies = [float(r["response_time_ms"]) for r in misses]
    error_latencies = [float(r["response_time_ms"]) for r in errors]
    origin_latencies = [float(r["origin_fetch_time_ms"]) for r in misses if r["origin_fetch_time_ms"]]
    
    avg_hit = sum(hit_latencies) / hits_count if hits_count > 0 else 0.0
    avg_miss = sum(miss_latencies) / misses_count if misses_count > 0 else 0.0
    avg_error = sum(error_latencies) / errors_count if errors_count > 0 else 0.0
    avg_origin = sum(origin_latencies) / len(origin_latencies) if origin_latencies else 0.0
    
    min_hit = min(hit_latencies) if hit_latencies else 0.0
    max_hit = max(hit_latencies) if hit_latencies else 0.0
    
    min_miss = min(miss_latencies) if miss_latencies else 0.0
    max_miss = max(miss_latencies) if miss_latencies else 0.0
    
    # calcular o quão mais rápido é a cache em comparação à origem
    speedup = (avg_miss / avg_hit) if avg_hit > 0 and avg_miss > 0 else 0.0
    
    # Dados transferidos
    file_sizes = [int(r["file_size_bytes"]) for r in rows if r["file_size_bytes"] and int(r["file_size_bytes"]) != -1]
    total_data_bytes = sum(file_sizes)
    avg_file_size = total_data_bytes / len(file_sizes) if file_sizes else 0.0
    
    # Popularidade de Ficheiros
    file_stats = {}
    for r in rows:
        filename = r["filename"]
        status = r["cache_status"]
        if filename not in file_stats:
            file_stats[filename] = {"requests": 0, "hits": 0, "misses": 0, "errors": 0}
        file_stats[filename]["requests"] += 1
        if status == "HIT":
            file_stats[filename]["hits"] += 1
        elif status == "MISS":
            file_stats[filename]["misses"] += 1
        else:
            file_stats[filename]["errors"] += 1
            
    sorted_popularity = sorted(file_stats.items(), key=lambda x: x[1]["requests"], reverse=True)

    # Construção do Relatório em Texto
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # tempo quando foi criado
    report = []
    report.append("RELATÓRIO DE PERFORMANCE E MÉTRICAS CDN\n")
    report.append(f"Criado em: {now_str}")
    report.append("--------------------------------------------------------------")
    report.append("\nESTATÍSTICAS GERAIS DE TRÁFEGO")
    report.append(f"    - Total de Pedidos Processados: {total_requests}")
    report.append(f"    - Total de Cache HITs: {hits_count} ({(hits_count/total_requests*100):.1f}%)")
    report.append(f"    - Total de Cache MISSes: {misses_count} ({(misses_count/total_requests*100):.1f}%)")
    report.append(f"    - Total de Erros: {errors_count} ({(errors_count/total_requests*100):.1f}%)")
    report.append(f"    - Taxa de Hit Global (HIT/MISS): {hit_rate:.2f}%")
    
    report.append("\nANÁLISE DE LATÊNCIA (tempos de resposta)")
    report.append(f"    - Latência Média de Cache HIT: {avg_hit:.3f} ms")
    report.append(f"    [Mínimo: {min_hit:.3f} ms | Máximo: {max_hit:.3f} ms]")
    report.append(f"    - Latência Média de Cache MISS: {avg_miss:.3f} ms")
    report.append(f"    [Mínimo: {min_miss:.3f} ms | Máximo: {max_miss:.3f} ms]")
    if errors_count > 0:
        report.append(f"    - Latência Média em Erros: {avg_error:.3f} ms")
    report.append(f"    - Latência Média de Download (Origem): {avg_origin:.3f} ms")
    report.append("--------------------------------------------------------------")
    if speedup > 0:
        report.append(f"FATOR DE ACELERAÇÃO: {speedup:.1f}x MAIS RÁPIDO EM HIT!")
    else:
        report.append("FATOR DE ACELERAÇÃO (SPEEDUP): N/A (Sem dados de HIT/MISS suficientes)")
        
    report.append("\nVOLUME E DADOS INTEGRADOS")
    report.append(f"    - Total de Dados Servidos: {format_size(total_data_bytes)}")
    report.append(f"    - Tamanho Médio dos Ficheiros: {format_size(avg_file_size)}")

    report.append("\nRANKING DE POPULARIDADE DE FICHEIROS")
    report.append(f"{'Ficheiro':<30} | {'Pedidos':<8} | {'HITs':<6} | {'MISSes':<6} | {'Hit Rate':<8}")
    report.append("   " + "-" * 70)
    for name, stats in sorted_popularity[:10]: # Top 10
        total_valid = stats["hits"] + stats["misses"]
        f_hit_rate = (stats["hits"] / total_valid * 100) if total_valid > 0 else 0.0
        report.append(f"{name:<30} | {stats['requests']:<8} | {stats['hits']:<6} | {stats['misses']:<6} | {f_hit_rate:.1f}%")
            
    return "\n".join(report)

def main():
    print("=" * 60)
    print("PROCESSAMENTO E TRATAMENTO DE MÉTRICAS CDN")
    print("=" * 60)
    
    csv_path = find_metrics_file()
    if not csv_path:
        print("Erro: Não foi possível localizar o ficheiro 'metrics.csv'.")
        print("Certifica-te que correste a simulação primeiro para gerar os dados!")
        sys.exit(1)
        
    print(f"Ficheiro metrics.csv localizado em: '{csv_path}'\n")
    
    report_text = generate_report_text(csv_path)
    
    # mostra resultado no terminal
    print(report_text)
    
    # gravar resultado num ficheiro (para não termos de repetir a execução)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_file_path = os.path.join(script_dir, "metrics_report.txt")
    try:
        with open(report_file_path, mode="w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"\n[SUCESSO] Relatório de métricas gravado em: '{os.path.abspath(report_file_path)}'")
    except Exception as e:
        print(f"\nErro ao gravar o ficheiro de relatório: {e}")

if __name__ == "__main__":
    main()
