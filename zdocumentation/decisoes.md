# Decisões de implementação: CDN

DECISÕES:
- FAST-API - framework da cdn, gere os pedidos HTTP dos clientes (usamos em IES)
- aiofiles - gestão de cache, responsavel pela persistencia de dados no dsico da CDN após um cache miss (recomendado no guiao do projeto)
- MQTT - mecanismo de purge (demos na aula)
- py - linguagem base (professor recomendou)
- httpx - cliente HTTP assíncrono usado pela cdn para solicitar ficheiros à origem (API)


## 1. Arquitetura Base e Orquestração

**O que temos:**
Temos contentores separados para o `origin` (servidor original) e para a `cdn` (nó de cache).

**O Porquê:**
- **Simulação Realista:** Uma CDN é inerentemente distribuída (rede de servidores espalhados). Utilizar contentores Docker isolados numa mesma rede virtual é a melhor forma de simular múltiplos computadores independentes.
- **Ambiente Limpo:** O uso de contentores garante que o projeto corre em qualquer máquina sem problemas de dependências, separando as portas para evitar conflitos (ex: a origem corre na porta 8000 interna, a CDN na 8080 exposta para fora).

---

## 2. Framework Web: FastAPI

**O que temos:**
Tanto a Origem (`origin/main.py`) como o nó da CDN (`cdn/main.py`) são construídos utilizando o **FastAPI** e a linguagem base é o **Python**.

**O Porquê:**
- **Concorrência Nativa (Requisito do Projeto):** O FastAPI baseia-se no `asyncio` do Python. Ao definirmos os endpoints com `async def`, a framework não bloqueia a execução. Isto significa que a CDN pode receber 100 clientes em simultâneo a pedir ficheiros e, enquanto o servidor vai buscar um ficheiro à origem, a *thread* principal fica livre para continuar a responder ou a enviar os ficheiros que já estão na cache a outros clientes.
- **Eficiência no envio de ficheiros:** O FastAPI providencia o `FileResponse`, que automaticamente lida com o *streaming* do ficheiro em "chunks" (pedaços), garantindo que a memória RAM não rebenta ao tentar enviar um ficheiro de vários Gigabytes.

---

## 3. Armazenamento Persistente

**O que temos:**
Na CDN, a lógica de *Cache Hit* (o ficheiro já está na cache) e *Cache Miss* (ir buscar à origem) está implementada. Para armazenar os ficheiros localmente após um Miss, usamos um volume Docker (`cache_storage`) e a biblioteca **`aiofiles`**.

**O Porquê:**
- **Persistência de Dados (Volume Docker):** Mapeamos a pasta `cache_storage` como um volume. Isto cumpre o requisito do enunciado ("armazenamento persistente para simular o cache de ficheiros pesados") para que os dados não se percam se o contentor for reiniciado.
- **Uso do `aiofiles`:** Escrever no disco (I/O) é tradicionalmente uma operação bloqueante. Se usássemos o `open()` normal do Python, a CDN ficaria "congelada" para todos os utilizadores enquanto guardava o ficheiro no disco. O `aiofiles` faz com que essa escrita seja feita de forma assíncrona.
- **Uso do `httpx`:** Para a CDN descarregar os dados da origem, usamos o `httpx.AsyncClient()`. Ao contrário do famoso `requests` (que é síncrono e bloquearia a aplicação), o `httpx` permite fazer o download também de forma totalmente assíncrona.

---
