# PURGE via MQTT

Introduzimos um servidor intermédio **MQTT** (*Message Broker*), utilizando o Eclipse Mosquitto.
- O Servidor de **Origem** atua como *Publisher*.
- O nó da **CDN** atua como *Subscriber*.

### Porquê o MQTT?
1. **Desacoplamento e Escalonamento:** A origem não precisa de saber quantas CDNs existem no mundo, nem os seus IPs. Simplesmente publica uma notificação de mudança num tópico (ex: `cdn/purge`). Qualquer nó de CDN subscrito vai ouvir a mensagem.
2. **Baixa Latência (Imediatismo):** O MQTT é um protocolo incrivelmente leve (usado em IoT), garantindo que o sinal de "PURGE" chegue na ordem dos milissegundos.

---

### Orquestração com Docker Compose
- Adicionámos o serviço `mqtt-broker` utilizando a imagem `eclipse-mosquitto:latest`.
- Mapeámos um ficheiro de configuração `mosquitto.conf` de forma a autorizar conexões anónimas para simplificar.
- Foram introduzidas variáveis de ambiente `MQTT_BROKER_URL` na Origem e na CDN para que as mesmas saibam onde encontrar o broker.

### Servidor Original (Publisher)
- O módulo `paho-mqtt` foi listado no `requirements.txt`.
- Em `origin/main.py`, desenvolvemos um novo endpoint `PUT /update/{filename}`.
Quando um ficheiro atualizado é enviado, a Origem guarda a nova versão na pasta local e, imediatamente a seguir, **publica uma mensagem JSON com o nome do ficheiro** no tópico MQTT `cdn/purge`.

### Nó da CDN (Subscriber)
- Incluímos o módulo `aiomqtt` no respetivo `requirements.txt` porque o FastAPI trabalha com funções assíncronas.
- Em `cdn/services.py`, foi programada a rotina lógica `delete_from_cache(filename)`, que executa fisicamente a remoção de um ficheiro dos ficheiros locais da CDN.
- Em `cdn/main.py`, ligámos uma tarefa em *background* permanente que arranca juntamente com o FastAPI (através do mecanismo `lifespan`). O seu único propósito é ligar-se ao Mosquitto, subscrever-se no tópico `cdn/purge` e aguardar que mensagens cheguem para ativar a função de remoção da cache.

