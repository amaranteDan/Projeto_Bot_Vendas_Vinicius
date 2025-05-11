import telebot
import requests
import time
import sqlite3
import threading
from uuid import uuid4
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import webbrowser

# Lê o token do arquivo
with open("token.txt") as arquivo:
    token = arquivo.read().strip()

bot = telebot.TeleBot(token)
chat_ids = {}  # Armazena o estado de cada chat
HOST = 'localhost'
PORT = 8000
BASE_URL = f'http://{HOST}:{PORT}/click'

# Configuração do banco de dados SQLite
def setup_database():
    """Configura o banco de dados SQLite para armazenar cliques."""
    conn = sqlite3.connect('clicks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            produto TEXT,
            link TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_click(chat_id, produto, link):
    """Registra um clique no banco de dados."""
    conn = sqlite3.connect('clicks.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO clicks (chat_id, produto, link) VALUES (?, ?, ?)', 
                   (chat_id, produto, link))
    conn.commit()
    conn.close()

# Servidor HTTP para rastrear cliques
class ClickHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        
        chat_id = query.get('chat_id', [None])[0]
        produto = query.get('produto', [None])[0]
        link = query.get('link', [None])[0]

        if chat_id and produto and link:
            log_click(int(chat_id), produto, link)
            self.send_response(302)
            self.send_header('Location', link)
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Parâmetros inválidos')

def run_server():
    """Inicia o servidor HTTP em uma thread separada."""
    server = HTTPServer((HOST, PORT), ClickHandler)
    print(f"Servidor de cliques rodando em {BASE_URL}")
    server.serve_forever()

# Inicia o servidor em uma thread separada
setup_database()
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

def enviar_botoes_iniciais(chat_id):
    """Envia os botões iniciais para o usuário escolher uma opção."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    botoes = [
        telebot.types.InlineKeyboardButton('🔍 Buscar ofertas', callback_data='/opcao1'),
        telebot.types.InlineKeyboardButton('📩 Reclamações', callback_data='/opcao2'),
        telebot.types.InlineKeyboardButton('🌟 Enviar um elogio', callback_data='/opcao3')
    ]
    markup.add(*botoes)
    bot.send_message(chat_id, "Escolha uma opção:", reply_markup=markup)

def enviar_botoes_sim_nao(chat_id):
    """Envia botões de Sim/Não para continuar ou encerrar a busca."""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton('✅ Sim', callback_data='/sim'),
        telebot.types.InlineKeyboardButton('❌ Não', callback_data='/nao')
    )
    bot.send_message(chat_id, "Gostaria de buscar outro produto?", reply_markup=markup)

def buscar_ofertas(produto, chat_id):
    """Busca ofertas no Mercado Livre e envia os resultados com links rastreados."""
    try:
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}', timeout=10)
        response.raise_for_status()
        data = response.json()
        ofertas = data.get('results', [])

        if not ofertas:
            bot.send_message(chat_id, f"😕 Não encontrei ofertas para '{produto}'. Tente outro produto!")
            enviar_botoes_iniciais(chat_id)
            return

        menor_preco = float('inf')
        oferta_mais_barata = None
        outras_ofertas = []

        for oferta in ofertas[:5]:
            titulo = oferta.get('title', 'Sem título')
            preco = oferta.get('price', 0)
            link = oferta.get('permalink', '#')
            # Gera um link rastreado
            tracked_link = f"{BASE_URL}?chat_id={chat_id}&produto={produto}&link={link}"

            if preco < menor_preco:
                menor_preco = preco
                oferta_mais_barata = {'titulo': titulo, 'preco': preco, 'link': tracked_link}
            outras_ofertas.append({'titulo': titulo, 'preco': preco, 'link': tracked_link})

        # Envia a oferta mais barata
        mensagem_oferta = (
            f"🎉 Oferta mais barata para '{produto}':\n"
            f"📌 {oferta_mais_barata['titulo']}\n"
            f"💸 R${oferta_mais_barata['preco']:.2f}\n"
            f"🔗 {oferta_mais_barata['link']}"
        )
        bot.send_message(chat_id, mensagem_oferta)

        # Envia outras ofertas
        if len(outras_ofertas) > 1:
            bot.send_message(chat_id, "📋 Outras opções encontradas:")
            for oferta in outras_ofertas:
                if oferta != oferta_mais_barata:
                    mensagem_oferta = (
                        f"📌 {oferta['titulo']}\n"
                        f"💸 R${oferta['preco']:.2f}\n"
                        f"🔗 {oferta['link']}"
                    )
                    bot.send_message(chat_id, mensagem_oferta)

        # Pergunta se o usuário quer buscar novamente
        chat_ids[chat_id] = 'esperando_resposta'
        enviar_botoes_sim_nao(chat_id)

    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"⚠️ Erro ao buscar ofertas: {str(e)}")
        print(f"Erro ao buscar ofertas: {e}")
        enviar_botoes_iniciais(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Erro inesperado: {str(e)}")
        print(f"Erro inesperado: {e}")
        enviar_botoes_iniciais(chat_id)

@bot.message_handler(commands=['start'])
def start(mensagem):
    """Handler para o comando /start."""
    chat_id = mensagem.chat.id
    chat_ids[chat_id] = None
    texto_inicial = (
        f"👋 Oi, {mensagem.from_user.first_name}! Sou o Rab, seu assistente de compras.\n"
        "Estou aqui para te ajudar a encontrar as melhores ofertas! 😊"
    )
    bot.send_message(chat_id, texto_inicial)
    enviar_botoes_iniciais(chat_id)

@bot.message_handler(commands=['clicks'])
def show_clicks(mensagem):
    """Mostra a quantidade de cliques registrados."""
    chat_id = mensagem.chat.id
    conn = sqlite3.connect('clicks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT produto, link, COUNT(*) as count FROM clicks WHERE chat_id = ? GROUP BY produto, link', (chat_id,))
    clicks = cursor.fetchall()
    conn.close()

    if not clicks:
        bot.send_message(chat_id, "📊 Ainda não há cliques registrados para você.")
        return

    mensagem = "📊 Relatório de cliques:\n"
    for produto, link, count in clicks:
        mensagem += f"🔍 Produto: {produto}\n🔗 Link: {link}\n👆 Cliques: {count}\n\n"
    bot.send_message(chat_id, mensagem)

@bot.message_handler(func=lambda mensagem: True)
def responder(mensagem):
    """Handler para mensagens de texto."""
    chat_id = mensagem.chat.id
    if chat_id not in chat_ids:
        chat_ids[chat_id] = None

    if chat_ids[chat_id] == 'buscando_produto':
        produto = mensagem.text.strip()
        if not produto:
            bot.reply_to(mensagem, "⚠️ Por favor, informe o nome de um produto válido.")
            return
        bot.reply_to(mensagem, f"🔎 Buscando ofertas para: {produto}")
        chat_ids[chat_id] = produto
        buscar_ofertas(produto, chat_id)
    elif chat_ids[chat_id] == 'esperando_resposta':
        bot.reply_to(mensagem, "Por favor, use os botões abaixo para continuar ou encerrar.")
    else:
        enviar_botoes_iniciais(chat_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handler para callbacks dos botões inline."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if call.data == '/opcao1':
        bot.send_message(chat_id, "🔍 Qual produto você deseja procurar?")
        chat_ids[chat_id] = 'buscando_produto'
    elif call.data == '/opcao2':
        bot.send_message(chat_id, "📩 Envie sua reclamação e entraremos em contato!")
        chat_ids[chat_id] = None
    elif call.data == '/opcao3':
        bot.send_message(chat_id, "🌟 Ficamos felizes com seu elogio! Envie sua mensagem!")
        chat_ids[chat_id] = None
    elif call.data == '/sim':
        bot.send_message(chat_id, "🔍 Qual produto você deseja buscar agora?")
        chat_ids[chat_id] = 'buscando_produto'
    elif call.data == '/nao':
        bot.send_message(chat_id, "👋 Ok, estou aqui se precisar! Até logo!")
        chat_ids[chat_id] = None
        enviar_botoes_iniciais(chat_id)

if __name__ == "__main__":
    print("Bot iniciado...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"Erro no polling: {e}")
            time.sleep(5)