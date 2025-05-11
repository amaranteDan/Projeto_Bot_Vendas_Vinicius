import telebot
import requests
import time
from uuid import uuid4

# Lê o token do arquivo
with open("token.txt") as arquivo:
    token = arquivo.read().strip()

bot = telebot.TeleBot(token)
chat_ids = {}  # Armazena o estado de cada chat


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
    """Busca ofertas no Mercado Livre e envia os resultados."""
    try:
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}', timeout=10)
        response.raise_for_status()  # Levanta exceção para erros HTTP
        data = response.json()
        ofertas = data.get('results', [])

        if not ofertas:
            bot.send_message(chat_id, f"😕 Não encontrei ofertas para '{produto}'. Tente outro produto!")
            enviar_botoes_iniciais(chat_id)
            return

        menor_preco = float('inf')
        oferta_mais_barata = None
        outras_ofertas = []

        for oferta in ofertas[:5]:  # Limita a 5 ofertas
            titulo = oferta.get('title', 'Sem título')
            preco = oferta.get('price', 0)
            link = oferta.get('permalink', '#')

            if preco < menor_preco:
                menor_preco = preco
                oferta_mais_barata = {'titulo': titulo, 'preco': preco, 'link': link}
            outras_ofertas.append({'titulo': titulo, 'preco': preco, 'link': link})

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
                if oferta != oferta_mais_barata:  # Evita duplicar a oferta mais barata
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
    bot.answer_callback_query(call.id)  # Confirma o clique no botão

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
            time.sleep(5)  # Aguarda antes de tentar novamente