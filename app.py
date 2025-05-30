import telebot
import time
import threading
import requests

with open("token.txt") as arquivo:
    token = arquivo.read().strip()
bot = telebot.TeleBot(token)

chat_ids = []


def verificar(mensagem):
    return True


@bot.message_handler(func=verificar)
def responder(mensagem):
    chat_id = mensagem.chat.id
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)

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
            bot.reply_to(mensagem, "Você escolheu a opção 1: Buscar ofertas.")
        elif mensagem.text == '/opcao2':
            # Lógica para reclamações
            bot.reply_to(mensagem, "Você escolheu a opção 2: Reclamações.")
        elif mensagem.text == '/opcao3':
            # Lógica para enviar um elogio
            bot.reply_to(mensagem, "Você escolheu a opção 3: Enviar um elogio.")
        else:
            bot.reply_to(mensagem, "Opção inválida. Por favor, escolha uma das opções disponíveis.")
    else:
        # Responder com a mensagem inicial se não for uma opção
        bot.reply_to(mensagem, texto_inicial)


def buscar_ofertas():
    while True:
        try:
            response = requests.get('https://api.mercadolibre.com/sites/MLB/search?q=ofertas')
            #response = requests.get('https://pt.aliexpress.com/item/1005004992965519.html?aff_fcid=7fa8566fc305463b9ec9bd004abc5419-1726962345682-09716-_mKL4ftE&tt=CPS_NORMAL&aff_fsk=_mKL4ftE&aff_platform=influencer-program-register-campaign&sk=_mKL4ftE&aff_trace_key=7fa8566fc305463b9ec9bd004abc5419-1726962345682-09716-_mKL4ftE&terminal_id=3182188e460c4887af8df4e9d337ec62&afSmartRedirect=y&gatewayAdapt=glo2bra')
            data = response.json()
            ofertas = data.get('results', [])

            for chat_id in chat_ids:
                for oferta in ofertas[:5]:  # Limitando a 5 ofertas
                    titulo = oferta.get('title')
                    preco = oferta.get('price')
                    link = oferta.get('permalink')
                    mensagem_oferta = f"{titulo} - R${preco}\nMais detalhes: {link}"
                    bot.send_message(chat_id, mensagem_oferta)
                    time.sleep(20)

        except Exception as e:
            print(f"Erro ao buscar ofertas: {e}")

        time.sleep(60)  # Aguarda 60 segundos antes de buscar novamente


# Inicia a thread para buscar ofertas
threading.Thread(target=buscar_ofertas, daemon=True).start()

bot.polling()
