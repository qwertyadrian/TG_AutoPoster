import telepot
import requests
form time import sleep
from config import *

bot = telepot.Bot(TOKEN)

def main():
	updates = bot.getUpdates()
	update_id = int(updates['update_id'])
	if len(updates) == 0:
		pass
	else:
		for item in updates:
			if item['message']['text'] == '/start':
				text = 'Привет. Я бот для автопостинга из групп ВК в телеграмм'
				bot.sendMessage(item['message']['chat']['id'], text)
			elif item['message']['text'] == '/add':
				text = 'Приступим к настройке автопостинга.'
				bot.sendMessage(item['message']['chat']['id'], text)
                      bot.sendMessage(item['message']['chat']['id'], 'Пришли мне токен бота, от имени которого ты хочешь отправлять посты.')
				sleep(60)
				try:
					token = bot.getUpdates(update_id+1)[0]['text']
					bot.sendMessage(item['message']['chat']['id'], 'Токен бота был упешно сохранен.')
				except KeyError:
					bot.sendMessage(item['message']['chat']['id'], 'Я не получил токен бота. Попробуй еще раз')
				bot.sendMessage(item['message']['chat']['id'], 'Пришли мне кратку ссылку на группу вк. Поимер: test_public_page123')
				sleep(60)
				try:
					group = bot.getUpdates(update_id+2)[0]['text']
					bot.sendMessage(item['message']['chat']['id'], 'Ссылка была сохранена.')
				except KeyError:
					bot.sendMessage(item['message']['chat']['id'], 'Я не получил ссылку. Попробуй еще раз.')
				bot.sendMessage(item['message']['chat']['id'], 'Пришли мне свой токен ВК для просмотра и обработки постов.')
				sleep(120)
				try:
					token_vk = bot.getUpdates(update_id+3)[0]['text']
					bot.sendMessage(item['message']['chat']['id'], 'Токен сохранен.')
				except KeyError:
					bot.sendMessage(item['message']['chat']['id'], 'Я не получил токен ВК. Попробуй еще раз.')
				bot.sendMessage(item['message']['chat']['id'], 'Для отправки сообщений вам в ЛС, ничего не отвечайте. Для отправки сообщений в чат/канал отправьте ссылку на чат. : @hotelab')
				sleep(60)
				try:
					chat_id = bot.getUpdates(update_id+4)[0]['text']
					bot.sendMessage(item['message']['chat']['id'], 'Отправка сообщений будет осуществлятся в чат/канал.')
				except KeyError:
					chat_id = item['message']['chat']['id']
					bot.sendMessage(item['message']['chat']['id'], 'Отправка сообщениий будет осуществлятся в ЛС.')
				bot.sendMessage(item['message']['chat']['id'], 'Настройка завершена')
				