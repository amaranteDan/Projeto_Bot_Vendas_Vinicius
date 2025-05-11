import telebot
import time
import threading
import requests
from bs4 import BeautifulSoup

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
    texto = """
    Oi, como vai? Aqui é o Rab Smile, seu assistente de compras. Terei o maior prazer de te ajudar. (Clique no item)
    /opcao1 Buscar ofertas
    /opcao2 Reclamações
    /opcao3 Enviar um elogio
    Hummm. Não entendi sua mensagem. Clique em uma das opções.
    """
    bot.reply_to(mensagem, texto)

def buscar_ofertas_mercadolivre():
    response = requests.get('https://api.mercadolibre.com/sites/MLB/search?q=ofertas')
    if response.status_code != 200:
        print(f"Erro no Mercado Livre: {response.status_code} - {response.text}")
        return []
    data = response.json()
    return data.get('results', [])

def buscar_ofertas_magalu():
    url = 'https://www.magazineluiza.com.br/selecao/ofertasdodia/'
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erro no Magazine Luiza: {response.status_code} - {response.text}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    ofertas = []

    # Extrair títulos, preços, links e imagens
    for item in soup.select('.product-wrapper'):
        titulo = item.select_one('.product-title').get_text(strip=True)
        preco = item.select_one('.price').get_text(strip=True)  # Ajuste o seletor conforme a estrutura real
        link = item.find('a')['href']
        imagem = item.select_one('img')['src']  # Ajuste o seletor para a imagem

        ofertas.append({'title': titulo, 'price': preco, 'link': link, 'image': imagem})

    return ofertas

def buscar_ofertas():
    while True:
        try:
            ofertas_ml = buscar_ofertas_mercadolivre()
            ofertas_magalu = buscar_ofertas_magalu()

            todas_ofertas = ofertas_ml + ofertas_magalu

            for chat_id in chat_ids:
                for oferta in todas_ofertas[:5]:  # Limitando a 5 ofertas
                    titulo = oferta.get('title')
                    preco = oferta.get('price', 'Preço não disponível')  # Valor padrão caso não tenha
                    link = oferta.get('link', '')
                    imagem = oferta.get('image', '')  # Nova informação de imagem

                    mensagem_oferta = f"{titulo} - {preco}\nMais detalhes: {link}"
                    bot.send_photo(chat_id, imagem, caption=mensagem_oferta)
                    time.sleep(20)

        except Exception as e:
            print(f"Erro ao buscar ofertas: {e}")

        time.sleep(60)  # Aguarda 60 segundos antes de buscar novamente

# Inicia a thread para buscar ofertas
threading.Thread(target=buscar_ofertas, daemon=True).start()

bot.polling()
