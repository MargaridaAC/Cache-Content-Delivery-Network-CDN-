# Sistema de Logs e Métricas de Performance

DECISÕES LÓGICAS:
- **`time.perf_counter()`** - cronómetro de altíssima precisão de CPU para medir a latência exata do processamento e download.
- **Escrita Assíncrona (`aiofiles`)** - gravação concorrente de logs no disco local da CDN sem interferir na entrega de ficheiros dos clientes.
- **Ficheiro CSV Persistente** - armazenamento simples em `cache_storage/metrics.csv` para portabilidade direta e análise fácil em Excel, Pandas ou MATLAB.
- **Cabeçalhos HTTP (Headers)** - injeção de `X-Cache` e `X-Response-Time-Ms` para auditoria externa das respostas da CDN.

---

## 1. Medição de Alta Precisão: time.perf_counter()

**O que temos:**
Nas rotas da CDN, cronometramos a duração total do pedido do cliente (`response_time_ms`) e a duração específica do download na origem (`origin_fetch_time_ms`) recorrendo à biblioteca standard do Python:
```python
start_time = time.perf_counter()
# ... processo ...
response_time_ms = (time.perf_counter() - start_time) * 1000
```

**O Porquê:**
- **Precisão:** Ao contrário de `time.time()` (que tem resolução milissegundo de baixo nível, estando sujeito a atualizações NTP), o `time.perf_counter()` utiliza o contador de ticks de CPU de maior resolução do sistema. É monotonicamente crescente, ou seja, nunca regressa atrás no tempo.
- **Diferenciação:** Medir os tempos separadamente permite provar numericamente a eficácia da cache:
  - Conseguimos quantificar o tempo gasto pela CDN a processar e servir o ficheiro localmente.
  - Conseguimos medir o overhead de rede gasto no download da Origem em caso de *Cache Miss*.

---

## 2. Persistência de Métricas em CSV

**O que temos:**
Gravamos cada transação de pedido num ficheiro estruturado em `cdn/cache_storage/metrics.csv` com as seguintes colunas:
`timestamp,filename,cache_status,response_time_ms,file_size_bytes,origin_fetch_time_ms`

**O Porquê:**
- **Simplicidade e Portabilidade:** Evitamos a instalação de bases de dados relacionais complexas (PostgreSQL, SQLite) que adicionariam peso desnecessário e dependências no Docker. Um ficheiro `.csv` cumpre o papel de forma exemplar: é facilmente partilhável e pode ser imediatamente importado para tratamento estatístico.
- **I/O Não Bloqueante (`aiofiles`):** O disco rígido é o componente mais lento do sistema. Se usássemos o `open()` síncrono do Python para registar a métrica, a CDN ficaria "congelada" (bloqueada) a cada pedido enquanto escrevia no disco. O `aiofiles.open(...)` escreve os logs de forma assíncrona, permitindo que a CPU continue a responder a novos clientes em paralelo.

---

## 3. Práticas Recomendadas: Cabeçalhos HTTP

**O que temos:**
Injetamos na resposta enviada ao utilizador os cabeçalhos HTTP personalizados:
*   `X-Cache` (indica se foi `HIT` ou `MISS`).
*   `X-Response-Time-Ms` (tempo total de processamento).

**O Porquê:**
- **Transparência e Conformidade:** Este comportamento replica o funcionamento real de CDNs (como Cloudflare).
- **Facilidade de Auditoria:** Permite que qualquer cliente HTTP consiga verificar de onde veio o ficheiro e o tempo de resposta sem precisar de consultar diretamente os logs no servidor.
