import telebot
import time
import threading
import requests

# Lê o token do bot a partir de um arquivo
with open("token.txt") as arquivo:
    token = arquivo.read().strip()

bot = telebot.TeleBot(token)

# Lista para armazenar os chat_ids dos contatos
chat_ids = []

# Função que verifica se a mensagem deve ser processada
def verificar(mensagem):
    return True

# Função para processar mensagens e adicionar novos contatos
@bot.message_handler(func=verificar)
def responder(mensagem):
    chat_id = mensagem.chat.id
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)

    # Mensagem inicial com opções para o usuário
    texto_inicial = f"""
    Oi, {mensagem.from_user.first_name}! Como vai? Aqui é o Rab Smile, seu assistente de compras. 
    Terei o maior prazer de te ajudar. (Clique no item)
    /opcao1 Buscar ofertas
    /opcao2 Reclamações
    /opcao3 Enviar um elogio
    Hummm. Não entendi sua mensagem. Clique em uma das opções.
    """

    # Resposta caso o usuário selecione uma opção
    if mensagem.text.startswith('/opcao'):
        if mensagem.text == '/opcao1':
            bot.reply_to(mensagem, "Você escolheu a opção 1: Buscar ofertas.")
        elif mensagem.text == '/opcao2':
            bot.reply_to(mensagem, "Você escolheu a opção 2: Reclamações.")
        elif mensagem.text == '/opcao3':
            bot.reply_to(mensagem, "Você escolheu a opção 3: Enviar um elogio.")
        else:
            bot.reply_to(mensagem, "Opção inválida. Por favor, escolha uma das opções disponíveis.")
    else:
        bot.reply_to(mensagem, texto_inicial)

# Função que busca ofertas e envia para os contatos
def buscar_ofertas():
    while True:
        try:
            # Acessa a API de ofertas
            response = requests.get('https://api.mercadolibre.com/sites/MLB/search?q=ofertas')
            data = response.json()
            ofertas = data.get('results', [])

            # Envia as 5 primeiras ofertas para os contatos
            for chat_id in chat_ids:
                for oferta in ofertas[:5]:  # Limitando a 5 ofertas
                    titulo = oferta.get('title')
                    preco = oferta.get('price')
                    link = oferta.get('permalink')
                    mensagem_oferta = f"{titulo} - R${preco}\nMais detalhes: {link}"
                    bot.send_message(chat_id, mensagem_oferta)
                    time.sleep(20)  # Intervalo de 20 segundos entre os envios

        except Exception as e:
            print(f"Erro ao buscar ofertas: {e}")

        time.sleep(60)  # Aguardar 1 minuto antes de buscar novas ofertas

# Inicia uma thread para buscar ofertas em segundo plano
threading.Thread(target=buscar_ofertas, daemon=True).start()

# Inicia o polling para ouvir mensagens do Telegram
bot.polling()
