import telebot

with open("token.txt") as arquivo:
    token = arquivo.read().strip()
bot = telebot.TeleBot(token, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hey man, how are you doing")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)   

bot.infinity_polling()     