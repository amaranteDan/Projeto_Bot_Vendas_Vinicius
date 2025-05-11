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

    # Mensagem inicial
    texto_inicial = f"""
    Oi, {mensagem.from_user.first_name}! Como vai? Aqui é o Rab Smile, seu assistente de compras. 
    Terei o maior prazer de te ajudar. (Clique no item)
    /opcao1 Buscar ofertas
    /opcao2 Reclamações
    /opcao3 Enviar um elogio
    Hummm. Não entendi sua mensagem. Clique em uma das opções.
    """

    # Verificar se a mensagem é uma opção
    if mensagem.text.startswith('/opcao'):
        if mensagem.text == '/opcao1':
            # Lógica para buscar ofertas
            bot.reply_to(mensagem, "Você escolheu a opção 1: Buscar ofertas. Qual produto você deseja procurar?")
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
    else:
        # Responder com a mensagem inicial se não for uma opção
        bot.reply_to(mensagem, texto_inicial)

def buscar_ofertas(produto, chat_id):
    try:
        # Fazendo a requisição para o Mercado Livre, buscando pelo produto escolhido
        response = requests.get(f'https://api.mercadolibre.com/sites/MLB/search?q={produto}')
        data = response.json()
        ofertas = data.get('results', [])

        if ofertas:
            for oferta in ofertas[:5]:  # Limitando a 5 ofertas
                titulo = oferta.get('title')
                preco = oferta.get('price')
                link = oferta.get('permalink')
                mensagem_oferta = f"{titulo} - R${preco}\nMais detalhes: {link}"
                bot.send_message(chat_id, mensagem_oferta)
                time.sleep(2)
        else:
            bot.send_message(chat_id, f"Não encontrei ofertas para o produto '{produto}'. Tente outro produto!")

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao buscar ofertas: {e}")
        print(f"Erro ao buscar ofertas: {e}")

# Inicia o bot e começa o polling
bot.polling()
