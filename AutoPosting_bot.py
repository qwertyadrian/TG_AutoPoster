import requests
from time import sleep

url = 'https://api.telegram.org/bot466499924:AAFfU9g-ra-rV2a938bBQrMStmRxMIVqzpw/'

def get_updates_json(request):
	responce = requests.get(request + 'getUpdates')
	return responce.json()
	
def last_update(data):
	results = data['result']
	total_updates = len(results) - 1
	return results[total_updates]
	
def get_chat_id(update):
	chat_id = update['message']['chat']['id']
	return chat_id
	
def send_mess(chat, text):
	params = {'chat_id': chat, 'text': text}
	response = requests.post(url + 'sendMessage', data=params)
	return response
	
def main():
	update_id = last_update(get_updates_json(url))['update_id']
	while True:
		if update_id == last_update(get_updates_json(url))['update_id']:
			send_mess(get_chat_id(last_update(get_updates_json(url))), 'test')
			update_id += 1
		sleep(1)
		
if __name__ == '__main__':
	main()
