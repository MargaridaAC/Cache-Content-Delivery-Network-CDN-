# Cache-Content-Delivery-Network-CDN-

Tema 4 – Cache Content Delivery Network (CDN)
Implementar um sistema de entrega de conteúdos que minimize a latência e a carga no servidor de
origem.
• CDN: rede de servidores espalhados geograficamente com cópias dos ficheiros existentes num
servidor original, centralizado. Quando os utilizadores pedem um ficheiro, o pedido é enviado sempre
primeiro ao nó de cache da CDN.
• O cliente pede um ficheiro ao nó da CDN. Se o nó tiver o ficheiro (Cache Hit), entrega-o. Se não tiver
(Cache Miss), deve descarregá-lo do servidor original, guardá-lo localmente (usando, e.g., aiofiles)
e só então entregar ao cliente.
• A CDN deve correr num contentor com armazenamento persistente para simular o cache de ficheiros
pesados.
• Mais dificil: Quando um ficheiro é alterado no servidor original, este publica uma mensagem "PURGE"
num tópico MQTT. O nó da CDN, que está subscrito para receber essas mensagens, recebe o aviso e
apaga a sua cópia local imediatamente para evitar servir dados obsoletos.
• Concorrência: O nó da CDN deve ser capaz de servir múltiplos clientes em simultâneo enquanto
descarrega novos ficheiros da origem.

CLIENTE <--> CACHE <--> SERVIDOR ORIGINAL



DECISÕES:
- FAST-API - cdn (usamos em IES)
- aiofiles (recomendado no guiao do projeto)
- MQTT (demos na aula)
- py (professor tinha ordenado)

ARQUITETURA REPOSITÓRIO:

├── docker-compose.yml       # Orquestração de toda a rede (Origem, CDN, Cliente) 
├── origin/ 
│   ├── Dockerfile           # Imagem para o servidor de origem 
│   ├── main.py              # Servidor HTTP com os ficheiros originais 
│   └── data/                # Ficheiros que a CDN vai buscar 
├── cdn/ 
│   ├── Dockerfile           # Imagem para o nó de cache 
│   ├── main.py              # Lógica da CDN (Cache Hit/Miss + MQTT) 
│   └── cache_storage/       # Volume persistente para os ficheiros guardados 
├── common/ 
│   └── protocol.py          # Definição de mensagens/formatos (Opcional)
└── tests/                   # Scripts de teste (baseados no guião 08) 
