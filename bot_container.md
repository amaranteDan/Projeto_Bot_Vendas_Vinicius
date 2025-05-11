Para rodar o bot fornecido em um container Docker, você precisará criar um `Dockerfile` e configurar o ambiente adequadamente. Abaixo está um guia passo a passo para containerizar o bot:

---

### 1. **Estrutura do Projeto**
Organize os arquivos necessários no diretório do projeto. A estrutura deve ser algo assim:

```
meu-bot/
├── bot.py          # O código do bot fornecido
├── token.txt       # Arquivo com o token do bot
├── requirements.txt # Dependências do Python
├── Dockerfile      # Arquivo para construir a imagem Docker
└── clicks.db       # Banco de dados SQLite (será criado automaticamente)
```

---

### 2. **Crie o `requirements.txt`**
Liste todas as dependências do Python usadas no seu script. Com base no código fornecido, crie o arquivo `requirements.txt` com o seguinte conteúdo:

```plaintext
pyTelegramBotAPI==4.14.0
requests==2.31.0
```

Essas são as bibliotecas principais usadas no seu código (`telebot` e `requests`). Você pode ajustar as versões conforme necessário.

---

### 3. **Crie o `Dockerfile`**
Crie um arquivo chamado `Dockerfile` no diretório do projeto com o seguinte conteúdo:

```dockerfile
# Use uma imagem base do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos necessários
COPY bot.py .
COPY token.txt .
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta usada pelo servidor HTTP (8000)
EXPOSE 8000

# Comando para executar o bot
CMD ["python", "bot.py"]
```

Este `Dockerfile`:
- Usa uma imagem base leve do Python 3.9.
- Copia os arquivos `bot.py`, `token.txt` e `requirements.txt` para o container.
- Instala as dependências listadas no `requirements.txt`.
- Expõe a porta 8000, usada pelo servidor HTTP interno do bot.
- Executa o script `bot.py` quando o container é iniciado.

---

### 4. **Ajustes no Código do Bot**
O código fornecido já está bem estruturado, mas há algumas considerações para rodar em um container Docker:

#### a) **Endereço do Servidor HTTP**
No código, o servidor HTTP está configurado para rodar em `localhost` (`HOST = 'localhost'`). Em um container Docker, `localhost` refere-se ao próprio container, o que pode não ser acessível externamente. Para permitir que os links de rastreamento sejam acessíveis fora do container (por exemplo, para os usuários clicarem), você deve alterar o `HOST` para `0.0.0.0`:

```python
HOST = '0.0.0.0'
```

Isso faz com que o servidor HTTP escute em todas as interfaces de rede do container.

#### b) **Base URL**
A variável `BASE_URL` também precisa ser ajustada. Como o container será acessado por meio de um endereço externo (por exemplo, o IP do host ou um domínio), você pode configurar o `BASE_URL` para usar uma variável de ambiente ou um endereço fixo. Por exemplo:

```python
import os

HOST = '0.0.0.0'
PORT = 8000
BASE_URL = os.getenv('BASE_URL', f'http://{HOST}:{PORT}/click')
```

Depois, ao rodar o container, você pode passar o `BASE_URL` correto via variável de ambiente (veja a seção 6).

#### c) **Persistência do Banco de Dados**
O banco de dados SQLite (`clicks.db`) é criado no diretório de trabalho do container. Para evitar que os dados sejam perdidos quando o container for reiniciado, você deve montar um volume para persistir o arquivo `clicks.db`. Isso será configurado ao rodar o container (veja a seção 6).

---

### 5. **Construa a Imagem Docker**
No diretório do projeto, execute o seguinte comando para construir a imagem Docker:

```bash
docker build -t meu-bot-telegram .
```

- `-t meu-bot-telegram`: Nomeia a imagem como `meu-bot-telegram`.
- `.`: Indica que o `Dockerfile` está no diretório atual.

---

### 6. **Execute o Container**
Para rodar o container, use o comando abaixo:

```bash
docker run -d \
  --name meu-bot \
  -p 8000:8000 \
  -v $(pwd)/clicks.db:/app/clicks.db \
  -e BASE_URL=http://<SEU_IP_OU_DOMINIO>:8000/click \
  meu-bot-telegram
```

Explicação dos parâmetros:
- `-d`: Executa o container em modo detached (em segundo plano).
- `--name meu-bot`: Nomeia o container como `meu-bot`.
- `-p 8000:8000`: Mapeia a porta 8000 do container para a porta 8000 do host, permitindo que o servidor HTTP seja acessível.
- `-v $(pwd)/clicks.db:/app/clicks.db`: Monta o arquivo `clicks.db` no diretório local para persistir os dados do banco SQLite.
- `-e BASE_URL=http://<SEU_IP_OU_DOMINIO>:8000/click`: Define a variável de ambiente `BASE_URL` com o endereço acessível externamente (substitua `<SEU_IP_OU_DOMINIO>` pelo IP público do host ou um domínio configurado).
- `meu-bot-telegram`: Nome da imagem Docker criada.

---

### 7. **Teste o Bot**
- Certifique-se de que o token em `token.txt` é válido e corresponde a um bot criado no Telegram.
- Acesse o Telegram e envie o comando `/start` para o bot.
- Clique nos links enviados pelo bot para verificar se o rastreamento de cliques está funcionando (os cliques devem ser registrados no `clicks.db`).
- Verifique os logs do container para depurar possíveis erros:

```bash
docker logs meu-bot
```

---

### 8. **Considerações Adicionais**
- **Segurança**: O arquivo `token.txt` contém informações sensíveis. Certifique-se de que ele não seja exposto publicamente (por exemplo, não o inclua em repositórios públicos no GitHub). Considere usar Docker Secrets ou variáveis de ambiente para gerenciar o token.
- **Escalabilidade**: O servidor HTTP embutido no código é básico. Para um ambiente de produção, considere usar um servidor mais robusto (como Gunicorn ou Uvicorn) ou configurar um proxy reverso (como Nginx).
- **Rede**: Se o container estiver rodando em uma máquina remota, certifique-se de que a porta 8000 esteja aberta no firewall e que o `BASE_URL` aponte para um endereço acessível.
- **Manutenção**: Para parar ou remover o container, use:

```bash
docker stop meu-bot
docker rm meu-bot
```

---

### 9. **Exemplo Completo**
Se você seguir todas as etapas, o bot estará rodando em um container Docker, com o banco de dados persistido e o servidor HTTP acessível. Um exemplo de como o código ajustado ficaria para o `BASE_URL`:

```python
import os

HOST = '0.0.0.0'
PORT = 8000
BASE_URL = os.getenv('BASE_URL', f'http://{HOST}:{PORT}/click')
```

E o comando para rodar o container:

```bash
docker run -d \
  --name meu-bot \
  -p 8000:8000 \
  -v $(pwd)/clicks.db:/app/clicks.db \
  -e BASE_URL=http://192.168.1.100:8000/click \
  meu-bot-telegram
```

Substitua `192.168.1.100` pelo IP ou domínio correto.

---

***********************************************************************************************************************************************

Para melhorar a segurança do bot fornecido, especialmente ao rodá-lo em um container Docker, é necessário abordar várias áreas: proteção do token, segurança do servidor HTTP, gerenciamento do banco de dados, comunicação com APIs externas e boas práticas gerais. Abaixo, apresento um guia detalhado com recomendações específicas para aumentar a segurança, mantendo as respostas concisas e organizadas:

---

### 1. **Proteger o Token do Bot**
O token do Telegram, armazenado em `token.txt`, é uma informação sensível. Se vazado, alguém pode controlar o bot. Aqui estão as melhorias recomendadas:

- **Usar Variáveis de Ambiente**:
  Em vez de armazenar o token em um arquivo, passe-o como uma variável de ambiente no Docker. Modifique o código para ler o token de uma variável de ambiente:

  ```python
  import os

  token = os.getenv('TELEGRAM_BOT_TOKEN')
  if not token:
      raise ValueError("Token do bot não fornecido na variável de ambiente TELEGRAM_BOT_TOKEN")
  bot = telebot.TeleBot(token)
  ```

  Ao rodar o container, passe o token assim:

  ```bash
  docker run -d \
    --name meu-bot \
    -p 8000:8000 \
    -v $(pwd)/clicks.db:/app/clicks.db \
    -e TELEGRAM_BOT_TOKEN=seu_token_aqui \
    -e BASE_URL=http://<SEU_IP_OU_DOMINIO>:8000/click \
    meu-bot-telegram
  ```

- **Usar Docker Secrets**:
  Para maior segurança, especialmente em ambientes de produção, use Docker Secrets para gerenciar o token. Crie um arquivo com o token (por exemplo, `bot_token.txt`) e configure o Docker Compose para usá-lo:

  ```yaml
  version: '3.8'
  services:
    bot:
      image: meu-bot-telegram
      ports:
        - "8000:8000"
      volumes:
        - ./clicks.db:/app/clicks.db
      environment:
        - BASE_URL=http://<SEU_IP_OU_DOMINIO>:8000/click
      secrets:
        - bot_token
  secrets:
    bot_token:
      file: ./bot_token.txt
  ```

  No código, leia o segredo de `/run/secrets/bot_token`:

  ```python
  with open('/run/secrets/bot_token') as f:
      token = f.read().strip()
  ```

- **Restringir Permissões do Arquivo**:
  Se mantiver o `token.txt`, garanta que ele tenha permissões restritas no host:

  ```bash
  chmod 600 token.txt
  ```

---

### 2. **Proteger o Servidor HTTP**
O servidor HTTP embutido (`BaseHTTPRequestHandler`) é básico e vulnerável a ataques. Aqui estão as melhorias:

- **Adicionar Validação de Entrada**:
  Valide os parâmetros da URL (`chat_id`, `produto`, `link`) para evitar injeções maliciosas. Por exemplo:

  ```python
  from urllib.parse import urlparse, parse_qs
  import re

  def do_GET(self):
      parsed_url = urlparse(self.path)
      query = parse_qs(parsed_url.query)
      
      chat_id = query.get('chat_id', [None])[0]
      produto = query.get('produto', [None])[0]
      link = query.get('link', [None])[0]

      # Validação
      if not chat_id or not chat_id.isdigit():
          self.send_response(400)
          self.end_headers()
          self.wfile.write(b'chat_id inválido')
          return
      if not produto or not re.match(r'^[\w\s-]+$', produto):
          self.send_response(400)
          self.end_headers()
          self.wfile.write(b'produto inválido')
          return
      if not link or not link.startswith('https://'):
          self.send_response(400)
          self.end_headers()
          self.wfile.write(b'link inválido')
          return

      log_click(int(chat_id), produto, link)
      self.send_response(302)
      self.send_header('Location', link)
      self.end_headers()
  ```

- **Usar HTTPS**:
  O servidor HTTP atual usa HTTP, o que expõe dados a interceptações. Configure HTTPS usando um servidor mais robusto, como o Gunicorn com um proxy reverso (Nginx) ou um certificado SSL. Um exemplo simples com Nginx:

  1. Instale o Nginx no host ou em outro container.
  2. Obtenha um certificado SSL gratuito com o Certbot (Let’s Encrypt).
  3. Configure o Nginx para redirecionar o tráfego HTTPS para o container.

  Alternativamente, substitua o servidor HTTP embutido por uma biblioteca como `FastAPI` com suporte a HTTPS.

- **Limitar Acesso à Porta**:
  Restrinja o acesso à porta 8000 usando um firewall (como `ufw` ou regras de segurança na nuvem). Por exemplo:

  ```bash
  ufw allow from <IP_PERMITIDO> to any port 8000
  ```

- **Rate Limiting**:
  Para evitar abusos (como ataques DDoS), configure um rate limiting no Nginx ou use bibliotecas como `ratelimit` no Python.

---

### 3. **Proteger o Banco de Dados SQLite**
O banco de dados `clicks.db` armazena informações sensíveis, como `chat_id` e links. Melhore sua segurança:

- **Sanitizar Entradas**:
  O código já usa consultas parametrizadas (`?`) no SQLite, o que previne injeções SQL. Continue assim e valide todas as entradas antes de inseri-las no banco.

- **Restringir Permissões do Arquivo**:
  No container, defina permissões restritas para o `clicks.db`:

  ```dockerfile
  RUN touch clicks.db && chmod 600 clicks.db
  ```

  No host, após montar o volume, ajuste as permissões:

  ```bash
  chmod 600 clicks.db
  ```

- **Criptografar Dados Sensíveis**:
  Se o `chat_id` ou outros dados forem considerados sensíveis, criptografe-os antes de armazenar no banco. Use uma biblioteca como `cryptography`:

  ```python
  from cryptography.fernet import Fernet

  key = Fernet.generate_key()  # Armazene a chave em um local seguro
  cipher = Fernet(key)

  def log_click(chat_id, produto, link):
      encrypted_chat_id = cipher.encrypt(str(chat_id).encode()).decode()
      conn = sqlite3.connect('clicks.db')
      cursor = conn.cursor()
      cursor.execute('INSERT INTO clicks (chat_id, produto, link) VALUES (?, ?, ?)', 
                     (encrypted_chat_id, produto, link))
      conn.commit()
      conn.close()
  ```

- **Usar um Banco Gerenciado**:
  Para maior escalabilidade e segurança, considere migrar para um banco de dados gerenciado (como PostgreSQL ou MySQL) com autenticação e backups automáticos.

---

### 4. **Proteger a Comunicação com APIs Externas**
O bot faz chamadas à API do Mercado Livre. Proteja essas interações:

- **Validar Respostas da API**:
  Verifique se as respostas da API são válidas e não contêm dados maliciosos:

  ```python
  def buscar_ofertas(produto, chat_id):
      try:
          response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}', timeout=10)
          response.raise_for_status()
          data = response.json()
          if not isinstance(data, dict) or 'results' not in data:
              raise ValueError("Resposta inválida da API")
          ofertas = data.get('results', [])
          ...
      except (requests.exceptions.RequestException, ValueError) as e:
          bot.send_message(chat_id, f"⚠️ Erro ao buscar ofertas: {str(e)}")
          enviar_botoes_iniciais(chat_id)
  ```

- **Usar Cabeçalhos de Segurança**:
  Adicione cabeçalhos como `User-Agent` para evitar bloqueios e identificar o bot:

  ```python
  headers = {'User-Agent': 'MeuBot/1.0 (+http://meu_dominio.com)'}
  response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}', headers=headers, timeout=10)
  ```

- **Timeout e Tentativas**:
  O código já define um timeout de 10 segundos. Para maior robustez, implemente retentativas com `tenacity`:

  ```python
  from tenacity import retry, stop_after_attempt, wait_fixed

  @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
  def buscar_ofertas(produto, chat_id):
      response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}', timeout=10)
      response.raise_for_status()
      return response.json()
  ```

---

### 5. **Proteger o Container Docker**
A execução do container também precisa de cuidados de segurança:

- **Usar Usuário Não-Root**:
  Modifique o `Dockerfile` para rodar o container como um usuário não-root:

  ```dockerfile
  FROM python:3.9-slim

  WORKDIR /app
  COPY bot.py .
  COPY requirements.txt .

  RUN pip install --no-cache-dir -r requirements.txt && \
      useradd -m appuser && \
      chown -R appuser:appuser /app

  USER appuser

  EXPOSE 8000
  CMD ["python", "bot.py"]
  ```

- **Minimizar a Imagem**:
  Use uma imagem base ainda mais leve, como `python:3.9-alpine`, se possível, e remova pacotes desnecessários:

  ```dockerfile
  FROM python:3.9-alpine
  WORKDIR /app
  COPY bot.py .
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  EXPOSE 8000
  CMD ["python", "bot.py"]
  ```

- **Escaneamento de Vulnerabilidades**:
  Use ferramentas como `docker scan` ou `trivy` para verificar vulnerabilidades na imagem:

  ```bash
  docker scan meu-bot-telegram
  ```

- **Isolar o Container**:
  Use redes Docker para isolar o container e limite os recursos com `--memory` e `--cpus`:

  ```bash
  docker run -d \
    --name meu-bot \
    --network minha-rede \
    --memory="512m" \
    --cpus="1" \
    -p 8000:8000 \
    -v $(pwd)/clicks.db:/app/clicks.db \
    -e TELEGRAM_BOT_TOKEN=seu_token_aqui \
    -e BASE_URL=http://<SEU_IP_OU_DOMINIO>:8000/click \
    meu-bot-telegram
  ```

---

### 6. **Monitoramento e Logging**
- **Centralizar Logs**:
  Configure um sistema de logging centralizado (como ELK Stack ou Fluentd) para monitorar atividades suspeitas.
- **Monitorar Cliques**:
  Adicione verificações para detectar cliques anormais (por exemplo, muitos cliques de um mesmo `chat_id` em pouco tempo):

  ```python
  def log_click(chat_id, produto, link):
      conn = sqlite3.connect('clicks.db')
      cursor = conn.cursor()
      cursor.execute('SELECT COUNT(*) FROM clicks WHERE chat_id = ? AND timestamp > datetime("now", "-1 hour")', (chat_id,))
      click_count = cursor.fetchone()[0]
      if click_count > 100:  # Limite arbitrário
          print(f"Possível abuso detectado: {chat_id}")
          conn.close()
          return
      cursor.execute('INSERT INTO clicks (chat_id, produto, link) VALUES (?, ?, ?)', 
                     (chat_id, produto, link))
      conn.commit()
      conn.close()
  ```

---

### 7. **Boas Práticas Gerais**
- **Atualizar Dependências**:
  Regularmente, atualize as dependências no `requirements.txt` para corrigir vulnerabilidades:

  ```bash
  pip install --upgrade pip
  pip install --upgrade -r requirements.txt
  ```

  Use ferramentas como `pip-audit` para verificar vulnerabilidades:

  ```bash
  pip install pip-audit
  pip-audit -r requirements.txt
  ```

- **Autenticação no Bot**:
  Considere restringir o acesso ao bot a usuários autorizados. Por exemplo, verifique o `chat_id` contra uma lista de IDs permitidos antes de processar comandos:

  ```python
  ALLOWED_CHAT_IDS = {123456789, 987654321}  # Substitua pelos chat_ids permitidos

  @bot.message_handler(commands=['start'])
  def start(mensagem):
      chat_id = mensagem.chat.id
      if chat_id not in ALLOWED_CHAT_IDS:
          bot.send_message(chat_id, "🚫 Acesso não autorizado.")
          return
      ...
  ```

- **Backup do Banco de Dados**:
  Configure backups regulares do `clicks.db` para evitar perda de dados:

  ```bash
  cp clicks.db clicks_backup_$(date +%F).db
  ```

---

### 8. **Resumo das Principais Ações**
1. Substitua `token.txt` por variáveis de ambiente ou Dockersecrets.
2. Valide entradas no servidor HTTP e migre para HTTPS.
3. Criptografe dados sensíveis no banco de dados e restrinja permissões.
4. Adicione cabeçalhos e retentativas nas chamadas à API do Mercado Livre.
5. Rode o container como usuário não-root e limite recursos.
6. Monitore logs e cliques para detectar abusos.

---

Ótimo! Vamos seguir com **conceitos essenciais e avançados do Docker**, focando em como trabalhar com **containers, redes e Dockerfiles**. Abaixo está um guia prático dividido por temas com exemplos.

---

## 🧱 1. Containers na prática

### 🔹 Criar e rodar um container

```bash
docker run --name meu-nginx -d -p 8080:80 nginx
```

* `--name`: nome do container
* `-d`: modo daemon (background)
* `-p`: mapeamento de portas (`host:container`)

### 🔹 Acessar o container

```bash
docker exec -it meu-nginx bash
```

### 🔹 Ver logs do container

```bash
docker logs meu-nginx
```

### 🔹 Parar e remover

```bash
docker stop meu-nginx
docker rm meu-nginx
```

---

## 🌐 2. Redes Docker

### 🔹 Listar redes disponíveis

```bash
docker network ls
```

### 🔹 Criar rede customizada (bridge)

```bash
docker network create minha-rede
```

### 🔹 Usar essa rede em dois containers:

```bash
docker run -d --name app --network minha-rede nginx
docker run -it --name debug --network minha-rede alpine sh
```

Agora dentro de `debug`, você pode fazer:

```bash
wget app
```

➡ Comunicação direta via nome DNS (`app`)

---

## 📦 3. Dockerfile avançado

### Exemplo:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

### Build e execução:

```bash
docker build -t minha-app .
docker run -p 8000:8000 minha-app
```

---

## 💡 Dicas avançadas

* Use `multi-stage builds` para imagens menores.
* Use `HEALTHCHECK` para monitorar containers.
* Use `docker-compose` para orquestrar múltiplos serviços.
* Use `volumes` para persistência de dados (`-v`).

---

## ⚙️ Quer ir além?

Posso mostrar:

* Como criar um `docker-compose.yml`
* Como usar `bind mounts` para desenvolvimento local
* Como integrar Docker com um app Python Flask ou FastAPI
* Como escanear imagens com ferramentas como `trivy` ou `dockle`

Excelente decisão! Vamos transformar isso em um guia **prático e profissional com Docker**, cobrindo as técnicas **mais avançadas e usadas na prática por desenvolvedores e DevOps**.

---

# 🚀 Projeto Avançado com Docker – Guia Completo

## 📁 Estrutura do projeto exemplo:

Vamos criar um projeto realista com:

* Backend em **Python (FastAPI)**
* Banco de dados **PostgreSQL**
* Painel de monitoramento
* Testes automatizados
* Dockerfile otimizado
* `docker-compose` com rede, volumes e variáveis de ambiente

```bash
meu_projeto/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── Dockerfile
├── docker-compose.yml
├── .env
├── scripts/
│   └── init.sql
└── tests/
    └── test_api.py
```

---

## 🧰 1. Dockerfile avançado (com multi-stage)

```dockerfile
# Etapa de build
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Etapa final
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🧱 2. Docker Compose com PostgreSQL e FastAPI

```yaml
version: "3.9"

services:
  api:
    build: .
    container_name: fastapi_app
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - db
    networks:
      - backend

  db:
    image: postgres:15
    container_name: postgres_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - backend

networks:
  backend:

volumes:
  pgdata:
```

---

## 🔐 3. `.env` – Variáveis sensíveis

```
POSTGRES_USER=admin
POSTGRES_PASSWORD=senhaforte123
POSTGRES_DB=meuprojeto
```

---

## 🧪 4. Testes automatizados (pytest + requests)

Arquivo: `tests/test_api.py`

```python
import requests

def test_root():
    response = requests.get("http://localhost:8000")
    assert response.status_code == 200
```

Rodar com:

```bash
docker-compose up -d
pytest tests/
```

---

## 🩺 5. Healthcheck nos containers

Adicione ao `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 🛡️ 6. Segurança e verificação

### 📦 Escaneamento de imagem:

```bash
docker scan minha-app
```

### 🔍 Usar Trivy:

```bash
brew install aquasecurity/trivy/trivy  # macOS
trivy image minha-app
```

---

## 🔄 7. Hot reload para dev (opcional)

Use o `volume` e o `--reload` do Uvicorn:

```yaml
volumes:
  - ./app:/app
command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 8. Monitoramento com Grafana + Prometheus (opcional extra)

Podemos integrar:

* Exportador de métricas FastAPI
* Prometheus para coleta
* Grafana para visualização

---

## ⚙️ 9. Práticas profissionais adicionais

* ✅ Use tags de imagem (ex: `v1.0`) ao invés de `latest`
* ✅ Bloqueie permissões com `USER` no Dockerfile
* ✅ Use `.dockerignore` para acelerar builds
* ✅ Use `alpine` quando possível para imagens mínimas
* ✅ Automatize builds com GitHub Actions ou GitLab CI

---

## 🚀 Quer que eu te entregue esse projeto completo para rodar local?

Posso gerar agora todos os arquivos prontos para você testar e adaptar.

Você quer que eu crie o projeto base completo para começarmos a iterar?

Tudo atualizado! Agora o projeto está usando **MySQL** e inclui:

✅ CRUD completo com SQLAlchemy
✅ Arquitetura profissional com separação de camadas (`models`, `schemas`, `crud`)
✅ Testes automatizados
✅ Healthcheck
✅ Variáveis de ambiente
✅ Inicialização com script SQL

Posso agora incluir:

* 🔐 Autenticação JWT
* 📈 Integração com Prometheus + Grafana
* 🚀 Workflow de deploy automatizado (GitHub Actions)

Deseja seguir com alguma dessas etapas agora?

✅ Pronto! Agora o projeto possui **autenticação JWT** integrada, incluindo:

* Rota de login (`/token`) com `OAuth2PasswordRequestForm`
* Proteção de rotas com token JWT
* Armazenamento de senha com hash seguro (`bcrypt`)
* Middleware CORS habilitado para testes com frontend

Você pode testar assim:

```bash
# 1. Criar usuário
curl -X POST http://localhost:8000/usuarios/ -H "Content-Type: application/json" -d '{"nome": "Joao", "senha": "123456"}'

# 2. Obter token
curl -X POST http://localhost:8000/token -d "username=Joao&password=123456"

# 3. Listar usuários autenticado
curl -H "Authorization: Bearer <SEU_TOKEN_AQUI>" http://localhost:8000/usuarios/
```

Deseja que eu siga com a próxima etapa: **Prometheus + Grafana para monitoramento**?

