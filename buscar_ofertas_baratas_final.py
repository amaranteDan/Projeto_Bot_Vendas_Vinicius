import telebot
import time
import threading
import requests

with open("token.txt") as arquivo:
    token = arquivo.read().strip()
bot = telebot.TeleBot(token)

chat_ids = {}


def verificar(mensagem):
    return True


@bot.message_handler(func=verificar)
def responder(mensagem):
    chat_id = mensagem.chat.id
    if chat_id not in chat_ids:
        chat_ids[chat_id] = None  # Inicializa com None, indicando que o produto ainda não foi pedido

    if mensagem.text.startswith('/opcao'):
        if mensagem.text == '/opcao1':
            bot.reply_to(mensagem, "Você escolheu a opção 1: Buscar ofertas. Qual produto você deseja procurar?")
            chat_ids[chat_id] = 'buscando_produto'
        elif mensagem.text == '/opcao2':
            bot.reply_to(mensagem, "Você escolheu a opção 2: Reclamações.")
        elif mensagem.text == '/opcao3':
            bot.reply_to(mensagem, "Você escolheu a opção 3: Enviar um elogio.")
        else:
            bot.reply_to(mensagem, "Opção inválida. Por favor, escolha uma das opções disponíveis.")
    elif chat_ids[chat_id] == 'buscando_produto':
        produto = mensagem.text.strip()
        bot.reply_to(mensagem, f"Buscando ofertas para: {produto}")
        chat_ids[chat_id] = produto
        buscar_ofertas(produto, chat_id)
    else:
        enviar_botoes(chat_id)


def buscar_ofertas(produto, chat_id):
    try:
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}')
        data = response.json()
        ofertas = data.get('results', [])

        if ofertas:
            menor_preco = float('inf')
            oferta_mais_barata = None
            outras_ofertas = []

            for oferta in ofertas[:5]:
                titulo = oferta.get('title')
                preco = oferta.get('price')
                link = oferta.get('permalink')

                if preco < menor_preco:
                    menor_preco = preco
                    oferta_mais_barata = {
                        'titulo': titulo,
                        'preco': preco,
                        'link': link
                    }
                outras_ofertas.append({
                    'titulo': titulo,
                    'preco': preco,
                    'link': link
                })

            if oferta_mais_barata:
                mensagem_oferta = (f"Encontrei a oferta mais barata para '{produto}':\n"
                                   f"{oferta_mais_barata['titulo']} - R${oferta_mais_barata['preco']}\n"
                                   f"Mais detalhes: {oferta_mais_barata['link']}")
                bot.send_message(chat_id, mensagem_oferta)

            bot.send_message(chat_id, "Aqui estão outras opções que encontrei:")
            for oferta in outras_ofertas:
                mensagem_oferta = (f"{oferta['titulo']} - R${oferta['preco']}\n"
                                   f"Mais detalhes: {oferta['link']}")
                bot.send_message(chat_id, mensagem_oferta)

            enviar_botoes_sim_nao(chat_id)
            chat_ids[chat_id] = 'esperando_resposta'
        else:
            bot.send_message(chat_id, f"Não encontrei ofertas para o produto '{produto}'. Tente outro produto!")

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao buscar ofertas: {e}")
        print(f"Erro ao buscar ofertas: {e}")


@bot.message_handler(func=lambda message: chat_ids.get(message.chat.id) == 'esperando_resposta')
def responder_busca(message):
    chat_id = message.chat.id
    if message.text.lower() == "/sim":
        bot.reply_to(message, "Por favor, informe o produto que você deseja buscar:")
        chat_ids[chat_id] = 'buscando_produto'
    elif message.text.lower() == "/nao":
        bot.reply_to(message, "Ok, se precisar de algo mais, estou à disposição! Até logo!")
        chat_ids[chat_id] = None
    else:
        bot.reply_to(message, "Comando inválido. Digite /sim para buscar outro produto ou /não para encerrar.")


def enviar_botoes(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    botao1 = telebot.types.InlineKeyboardButton('Buscar ofertas', callback_data='/opcao1')
    botao2 = telebot.types.InlineKeyboardButton('Reclamações', callback_data='/opcao2')
    botao3 = telebot.types.InlineKeyboardButton('Enviar um elogio', callback_data='/opcao3')
    markup.add(botao1, botao2, botao3)
    bot.send_message(chat_id, "Escolha uma opção:", reply_markup=markup)


def enviar_botoes_sim_nao(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    botao_sim = telebot.types.InlineKeyboardButton('Sim', callback_data='/sim')
    botao_nao = telebot.types.InlineKeyboardButton('Não', callback_data='/nao')
    markup.add(botao_sim, botao_nao)
    bot.send_message(chat_id, "Gostaria de buscar outro produto?", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(mensagem):
    chat_id = mensagem.chat.id
    texto_inicial = f"""
    Oi, {mensagem.from_user.first_name}! Como vai? Aqui é o Rab, seu assistente de compras. 
    Vou te ajudar a encontrar a melhor oferta :)
    """
    bot.send_message(chat_id, texto_inicial)
    enviar_botoes(chat_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == '/opcao1':
        bot.send_message(chat_id, "Você escolheu a opção 1: Buscar ofertas. Qual produto você deseja procurar?")
        chat_ids[chat_id] = 'buscando_produto'
    elif call.data == '/opcao2':
        bot.send_message(chat_id, "Você escolheu a opção 2: Reclamações.")
    elif call.data == '/opcao3':
        bot.send_message(chat_id, "Você escolheu a opção 3: Enviar um elogio.")
    elif call.data == '/sim':
        bot.send_message(chat_id, "Por favor, informe o produto que você deseja buscar:")
        chat_ids[chat_id] = 'buscando_produto'
    elif call.data == '/nao':
        bot.send_message(chat_id, "Ok, se precisar de algo mais, estou à disposição! Até logo!")
        chat_ids[chat_id] = None


# Inicia o bot e começa o polling
bot.polling()
