# Como correr

1. `docker compose up --build`
se der erros, tenta `docker compose down --remove-orphans`

2. no browser, acede ao nó CDN para pedir o ficheiro:
   `http://localhost:8081/file/teste.txt`
   - **No browser**: vai aparecer o texto que está no ficheiro original
   - **No terminal**:  `[MISS] A descarregar teste.txt da origem...`

3. dá refresh no browser:
   - **No terminal**: `[HIT] A entregar teste.txt da cache.`

4. para testar o purge:
   `curl -X PUT http://localhost:8000/update/teste.txt -d "novo texto"`

   - **No terminal**: 
     `[MQTT] Recebido pedido de PURGE para: teste.txt`
     `[PURGE] Ficheiro teste.txt removido da cache com sucesso.`

5. volta ao browser e dá refresh:
   - **No browser**: vais ver o novo texto
   - **No terminal**: `[MISS]...`