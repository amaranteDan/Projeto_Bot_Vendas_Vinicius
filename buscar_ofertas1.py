import telebot
import requests

# Lê o token do arquivo
with open("token.txt") as arquivo:
    token = arquivo.read().strip()

bot = telebot.TeleBot(token)

# Dicionário para armazenar o estado do chat de cada usuário
chat_ids = {}


def verificar(mensagem):
    return True


@bot.message_handler(func=verificar)
def responder(mensagem):
    chat_id = mensagem.chat.id
    if chat_id not in chat_ids:
        chat_ids[chat_id] = None  # Inicializa com None, indicando que o produto ainda não foi pedido

    # Mensagem inicial
    texto_inicial = f"""
    Oi, {mensagem.from_user.first_name}! Aqui é o Rab, te ajudo a encontrar a melhor oferta.
    /opcao1 Buscar ofertas
    """
    texto_esperando_resposta = 'Ei, esperando sua resposta;)'
    # Verificar se a mensagem é uma opção
    if mensagem.text.startswith('/opcao'):
        if mensagem.text == '/opcao1':
            # Lógica para buscar ofertas
            bot.reply_to(mensagem, "Qual produto você deseja procurar?")
            chat_ids[chat_id] = 'buscando_produto'  # Marcar que o usuário está buscando um produto
        elif mensagem.text == '/opcao2':
            # Lógica para reclamações
            bot.reply_to(mensagem, "Você escolheu a opção 2: Reclamações.")
        elif mensagem.text == '/opcao3':
            # Lógica para enviar um elogio
            bot.reply_to(mensagem, "Você escolheu a opção 3: Enviar um elogio.")
        else:
            bot.reply_to(mensagem, "Opção inválida. Por favor, escolha uma das opções disponíveis.")
    elif chat_ids[chat_id] == 'buscando_produto':
        # Caso o usuário tenha solicitado buscar ofertas, ele agora enviou um produto
        produto = mensagem.text.strip()
        bot.reply_to(mensagem, f"Buscando ofertas para: {produto}")
        chat_ids[chat_id] = produto  # Salva o nome do produto para buscar as ofertas
        buscar_ofertas(produto, chat_id)
    elif chat_ids[chat_id] is None:  # Envia a mensagem apenas se ainda não foi enviado nada
        bot.reply_to(mensagem, texto_esperando_resposta)



def processar_opcao(mensagem, chat_id):
    if mensagem.text == '/opcao1':
        bot.reply_to(mensagem, "Qual produto você deseja procurar?")
        chat_ids[chat_id] = 'aguardando_produto'  # Muda o estado para aguardando o nome do produto
    elif mensagem.text == '/opcao2':
        bot.reply_to(mensagem, "Você escolheu a opção 2: Reclamações.")
    elif mensagem.text == '/opcao3':
        bot.reply_to(mensagem, "Você escolheu a opção 3: Enviar um elogio.")
    else:
        bot.reply_to(mensagem, "Opção inválida. Por favor, escolha uma das opções disponíveis.")


def buscar_ofertas(produto, chat_id):
    try:
        # Faz a requisição ao Mercado Livre
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}')
        data = response.json()
        ofertas = data.get('results', [])

        if ofertas:
            menor_preco, oferta_mais_barata, outras_ofertas = float('inf'), None, []

            # Compara os preços das ofertas
            for oferta in ofertas[:5]:  # Limitando a 5 ofertas
                titulo = oferta.get('title')
                preco = oferta.get('price')
                link = oferta.get('permalink')

                if preco < menor_preco:
                    menor_preco = preco
                    oferta_mais_barata = {'titulo': titulo, 'preco': preco, 'link': link}

                outras_ofertas.append({'titulo': titulo, 'preco': preco, 'link': link})

            # Envia a oferta mais barata
            if oferta_mais_barata:
                mensagem_oferta = (f"Encontrei a oferta mais barata para '{produto}':\n"
                                   f"{oferta_mais_barata['titulo']} - R${oferta_mais_barata['preco']}\n"
                                   f"Mais detalhes: {oferta_mais_barata['link']}")
                bot.send_message(chat_id, mensagem_oferta)

            # Envia outras ofertas
            bot.send_message(chat_id, "Aqui estão outras opções que encontrei:")
            for oferta in outras_ofertas:
                mensagem_oferta = (f"{oferta['titulo']} - R${oferta['preco']}\n"
                                   f"Mais detalhes: {oferta['link']}")
                bot.send_message(chat_id, mensagem_oferta)

            # Pergunta se o usuário deseja buscar outro produto
            bot.reply_to(chat_id,
                         "Gostaria de buscar outro produto? Digite /sim para continuar ou /sair para encerrar.")
        else:
            bot.send_message(chat_id, f"Não encontrei ofertas para o produto '{produto}'. Tente outro produto!")

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao buscar ofertas: {e}")
        print(f"Erro ao buscar ofertas: {e}")


def tratar_resposta_busca(mensagem, chat_id):
    if mensagem.text.lower() == "/sim":
        bot.reply_to(mensagem, "Ótimo! Qual produto você deseja buscar?")
        chat_ids[chat_id] = 'aguardando_produto'
    elif mensagem.text.lower() == "/sair":
        bot.reply_to(mensagem, "Obrigado por utilizar nosso serviço! Até a próxima.")
        chat_ids[chat_id] = 'finalizado'  # Marca como finalizado
    else:
        bot.reply_to(mensagem, "Comando inválido. Digite /sim para buscar outro produto ou /sair para encerrar.")


@bot.message_handler(func=verificar)
def responder(mensagem):
    chat_id = mensagem.chat.id

    # Inicializa o estado do usuário se ainda não existir
    if chat_id not in chat_ids:
        chat_ids[chat_id] = None  # Indica que o produto ainda não foi pedido

    # Resposta inicial ou outras opções
    if chat_ids[chat_id] is None:
        responder_mensagem_inicial(mensagem)
    elif mensagem.text.startswith('/opcao'):
        processar_opcao(mensagem, chat_id)
    elif chat_ids[chat_id] == 'aguardando_produto':
        produto = mensagem.text.strip()
        bot.reply_to(mensagem, f"Buscando ofertas para: {produto}")
        chat_ids[chat_id] = 'buscando_produto'  # Muda o estado para buscar ofertas
        buscar_ofertas(produto, chat_id)


@bot.message_handler(func=lambda message: chat_ids.get(message.chat.id) == 'esperando_resposta')
def responder_busca(message):
    chat_id = message.chat.id
    tratar_resposta_busca(message, chat_id)


# Inicia o bot e começa o polling
bot.polling()
