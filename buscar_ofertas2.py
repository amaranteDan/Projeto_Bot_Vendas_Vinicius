import telebot
import requests
import sqlite3
import threading
import logging
from flask import Flask, redirect

# Configuração de logging
logging.basicConfig(filename='bot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Banco de dados SQLite
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, state TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS clicks (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, link TEXT, clicks INTEGER, UNIQUE(chat_id, link))''')
conn.commit()

# Funções de gerenciamento de estado
def set_state(chat_id, state):
    cursor.execute('INSERT OR REPLACE INTO users (chat_id, state) VALUES (?, ?)', (chat_id, state))
    conn.commit()

def get_state(chat_id):
    cursor.execute('SELECT state FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# Inicialização do bot
with open("token.txt") as arquivo:
    token = arquivo.read().strip()
bot = telebot.TeleBot(token)

# Função genérica para enviar botões
def enviar_botoes(chat_id, texto, opcoes):
    markup = telebot.types.InlineKeyboardMarkup()
    for texto_botao, callback in opcoes:
        markup.add(telebot.types.InlineKeyboardButton(texto_botao, callback_data=callback))
    bot.send_message(chat_id, texto, reply_markup=markup)

# Handler para qualquer mensagem
def verificar(mensagem):
    return True

@bot.message_handler(func=verificar)
def responder(mensagem):
    chat_id = mensagem.chat.id
    estado = get_state(chat_id)
    
    if estado is None:
        set_state(chat_id, None)
    
    if mensagem.text.startswith('/opcao'):
        if mensagem.text == '/opcao1':
            bot.reply_to(mensagem, "Você escolheu a opção 1: Buscar ofertas. Qual produto você deseja procurar?")
            set_state(chat_id, 'buscando_produto')
        elif mensagem.text == '/opcao2':
            bot.reply_to(mensagem, "Você escolheu a opção 2: Reclamações.")
        elif mensagem.text == '/opcao3':
            bot.reply_to(mensagem, "Você escolheu a opção 3: Enviar um elogio.")
        else:
            bot.reply_to(mensagem, "Opção inválida. Por favor, escolha uma das opções disponíveis.")
    elif estado == 'buscando_produto':
        produto = mensagem.text.strip()
        if not produto or len(produto) < 3:
            bot.reply_to(mensagem, "Por favor, informe um produto válido com pelo menos 3 caracteres.")
            return
        bot.reply_to(mensagem, f"Buscando ofertas para: {produto}")
        set_state(chat_id, produto)
        buscar_ofertas(produto, chat_id)
    elif estado and estado.startswith('aguardando_comentario_'):
        produto = estado.split('_')[1]
        comentario = mensagem.text
        with open(f"comentarios_{produto}.txt", "a") as f:
            f.write(f"Chat ID {chat_id}: {comentario}\n")
        bot.reply_to(mensagem, "Obrigado pelo seu comentário!")
        set_state(chat_id, None)
        enviar_botoes(chat_id, "Escolha uma opção:", [
            ("Buscar ofertas", "/opcao1"),
            ("Reclamações", "/opcao2"),
            ("Enviar um elogio", "/opcao3")
        ])
    else:
        enviar_botoes(chat_id, "Escolha uma opção:", [
            ("Buscar ofertas", "/opcao1"),
            ("Reclamações", "/opcao2"),
            ("Enviar um elogio", "/opcao3")
        ])

# Função para buscar ofertas
def buscar_ofertas(produto, chat_id):
    try:
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}')
        response.raise_for_status()
        data = response.json()
        ofertas = data.get('results', [])[:5]

        if ofertas:
            for oferta in ofertas:
                link_personalizado = f"http://localhost:5000/redirect/{chat_id}/{oferta['permalink']}"
                mensagem_oferta = (f"{oferta['title']} - R${oferta['price']}\n"
                                   f"Mais detalhes: {link_personalizado}")
                bot.send_message(chat_id, mensagem_oferta)
            
            # Botão para comentário
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Deixar um comentário", callback_data=f"comentar_{produto}"))
            bot.send_message(chat_id, "O que achou da oferta? Deixe um comentário!", reply_markup=markup)
            
            # Botões sim/não
            enviar_botoes(chat_id, "Gostaria de buscar outro produto?", [
                ("Sim", "/sim"),
                ("Não", "/nao")
            ])
            set_state(chat_id, 'esperando_resposta')
        else:
            bot.send_message(chat_id, f"Não encontrei ofertas para o produto '{produto}'. Tente outro produto!")
            set_state(chat_id, None)

    except requests.RequestException as e:
        logging.error(f"Erro na API do Mercado Livre: {e}")
        bot.send_message(chat_id, "Erro ao buscar ofertas. Tente novamente mais tarde.")
        set_state(chat_id, None)

# Handler para respostas após busca
@bot.message_handler(func=lambda message: get_state(message.chat.id) == 'esperando_resposta')
def responder_busca(message):
    chat_id = message.chat.id
    if message.text.lower() == "/sim":
        bot.reply_to(message, "Por favor, informe o produto que você deseja buscar:")
        set_state(chat_id, 'buscando_produto')
    elif message.text.lower() == "/nao":
        bot.reply_to(message, "Ok, se precisar de algo mais, estou à disposição! Até logo!")
        set_state(chat_id, None)
    else:
        bot.reply_to(message, "Comando inválido. Digite /sim para buscar outro produto ou /não para encerrar.")

# Comando /start
@bot.message_handler(commands=['start'])
def start(mensagem):
    chat_id = mensagem.chat.id
    texto_inicial = f"""
    Oi, {mensagem.from_user.first_name}! Como vai? Aqui é o Rab, seu assistente de compras. 
    Vou te ajudar a encontrar a melhor oferta :)
    """
    bot.send_message(chat_id, texto_inicial)
    enviar_botoes(chat_id, "Escolha uma opção:", [
        ("Buscar ofertas", "/opcao1"),
        ("Reclamações", "/opcao2"),
        ("Enviar um elogio", "/opcao3")
    ])

# Comando /cliques
@bot.message_handler(commands=['cliques'])
def mostrar_cliques(mensagem):
    chat_id = mensagem.chat.id
    cursor.execute('SELECT link, clicks FROM clicks WHERE chat_id = ?', (chat_id,))
    resultados = cursor.fetchall()
    if resultados:
        resposta = "\n".join([f"Link: {r[0]} - Cliques: {r[1]}" for r in resultados])
        bot.send_message(chat_id, resposta)
    else:
        bot.send_message(chat_id, "Nenhum clique registrado ainda.")

# Handler para callback de botões
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == '/opcao1':
        bot.send_message(chat_id, "Você escolheu a opção 1: Buscar ofertas. Qual produto você deseja procurar?")
        set_state(chat_id, 'buscando_produto')
    elif call.data == '/opcao2':
        bot.send_message(chat_id, "Você escolheu a opção 2: Reclamações.")
    elif call.data == '/opcao3':
        bot.send_message(chat_id, "Você escolheu a opção 3: Enviar um elogio.")
    elif call.data == '/sim':
        bot.send_message(chat_id, "Por favor, informe o produto que você deseja buscar:")
        set_state(chat_id, 'buscando_produto')
    elif call.data == '/nao':
        bot.send_message(chat_id, "Ok, se precisar de algo mais, estou à disposição! Até logo!")
        set_state(chat_id, None)
    elif call.data.startswith('comentar_'):
        produto = call.data.split('_')[1]
        bot.send_message(chat_id, f"Digite seu comentário sobre as ofertas de '{produto}':")
        set_state(chat_id, f"aguardando_comentario_{produto}")

# Configuração do Flask para rastrear cliques
app = Flask(__name__)

@app.route('/redirect/<int:chat_id>/<path:link>')
def redirect_link(chat_id, link):
    cursor.execute('INSERT INTO clicks (chat_id, link, clicks) VALUES (?, ?, 1) '
                   'ON CONFLICT(chat_id, link) DO UPDATE SET clicks = clicks + 1', (chat_id, link))
    conn.commit()
    return redirect(link)

# Iniciar Flask e Bot em threads separadas
if __name__ == "__main__":
    flask_thread = threading.Thread(target=app.run, args=('0.0.0.0', 5000))
    flask_thread.daemon = True
    flask_thread.start()
    bot.polling()