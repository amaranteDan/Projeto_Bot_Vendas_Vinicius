import telebot
import time
import threading
import requests

# Lê o token do arquivo
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

    # Verificar se o chat foi finalizado
    if chat_ids[chat_id] == 'finalizado':
        return  # Não faz nada se o chat foi finalizado

    # Mensagem inicial
    texto_inicial = f"""
    Oi, {mensagem.from_user.first_name}! Aqui é o Rab, te ajudo a encontrar a melhor oferta.
    /opcao1 Buscar ofertas
    """

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
    elif chat_ids[chat_id] is None:  # Envia a mensagem inicial apenas se ainda não foi enviado nada
        bot.reply_to(mensagem, texto_inicial)

def buscar_ofertas(produto, chat_id):
    try:
        # Fazendo a requisição para o Mercado Livre, buscando pelo produto escolhido
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}')
        data = response.json()
        ofertas = data.get('results', [])

        if ofertas:
            # Inicializa uma variável para armazenar a oferta com o menor preço
            menor_preco = float('inf')
            oferta_mais_barata = None
            outras_ofertas = []

            # Comparando os preços das ofertas
            for oferta in ofertas[:5]:  # Limitando a 5 ofertas
                titulo = oferta.get('title')
                preco = oferta.get('price')
                link = oferta.get('permalink')

                if preco < menor_preco:  # Se encontramos um preço menor
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

            # Enviar a oferta mais barata
            if oferta_mais_barata:
                mensagem_oferta = (f"Encontrei a oferta mais barata para '{produto}':\n"
                                   f"{oferta_mais_barata['titulo']} - R${oferta_mais_barata['preco']}\n"
                                   f"Mais detalhes: {oferta_mais_barata['link']}")
                bot.send_message(chat_id, mensagem_oferta)

            # Enviar as outras ofertas
            bot.send_message(chat_id, "Aqui estão outras opções que encontrei:")
            for oferta in outras_ofertas:
                mensagem_oferta = (f"{oferta['titulo']} - R${oferta['preco']}\n"
                                   f"Mais detalhes: {oferta['link']}")
                bot.send_message(chat_id, mensagem_oferta)

            # Perguntar se o usuário deseja buscar outro produto
            bot.send_message(chat_id,
                             "Gostaria de buscar outro produto? Digite sim para continuar ou sair para encerrar.")
            chat_ids[chat_id] = 'esperando_resposta'
        else:
            bot.send_message(chat_id, f"Não encontrei ofertas para o produto '{produto}'. Tente outro produto!")

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao buscar ofertas: {e}")
        print(f"Erro ao buscar ofertas: {e}")

# Função para lidar com a resposta do usuário sobre buscar outro produto
def responder_usuario(chat_id, resposta):
    if resposta.lower() == "sim":
        bot.send_message(chat_id, "Ótimo! Qual produto você deseja buscar?")
        chat_ids[chat_id] = 'aguardando_produto'
    elif resposta.lower() == "sair":
        bot.send_message(chat_id, "Obrigado por utilizar nosso serviço! Até a próxima.")
        chat_ids[chat_id] = 'finalizado'  # Marca como finalizado, impedindo respostas posteriores
    else:
        bot.send_message(chat_id, "Desculpe, não entendi sua resposta. Digite sim para buscar outro produto ou sair para encerrar.")

@bot.message_handler(func=lambda message: chat_ids.get(message.chat.id) == 'esperando_resposta')
def responder_busca(message):
    chat_id = message.chat.id
    if message.text.lower() == "/sim":
        # Volta para a fase de buscar um produto
        bot.reply_to(message, "Por favor, informe o produto que você deseja buscar:")
        chat_ids[chat_id] = 'buscando_produto'
    elif message.text.lower() == "/sair":
        # Encerra a busca
        bot.reply_to(message, "Ok, se precisar de algo mais, estou à disposição! Até logo!")
        chat_ids[chat_id] = 'finalizado'  # Marca como finalizado, impedindo respostas posteriores
    # else:
    #     bot.reply_to(message, "Comando inválido. Digite /sim para buscar outro produto ou /sair para encerrar.")

# Inicia o bot e começa o polling
while True:
    time.sleep(20)
    bot.polling()