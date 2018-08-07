











import sys
from re import sub

from async import Async
from requests import get, post

class CallBackQuery:
	def __init__(self, json,  bot):
		self.id = json['id']
		self.From = json['from']
		
		try:
			self.chat = json['message']['chat']
		except KeyError:
			self.chat = None
		self.chat_instance = json['chat_instance']
		self.data = json['data']
		self.bot = bot
		self.any = json
	
	def showAlert(self, message):
		return	(self.bot.method("answerCallbackQuery", {'callback_query_id':self.id, 'text':message, 'show_alert':'true'}))
	
	def editMsg(self, text, markup="{}"):
		return self.bot.method("editMessageText",{'message_id':self.mid, 'chat_id':self.chat['id'],'text':text,'reply_markup':markup})
	def showNotification(self, message):
		return self.bot.method("answerCallbackQuery", {'callback_query_id':self.id, 'text':message, 'show_alert':'false'})


class Message:
	def __init__(self, json, bot):
		self.json = json
		if 'text' in json:	self.text = json['text']
		if not 'message' in json:	return None
		json = json['message']
		if 'reply_to_message' in json:
			self.replied = True
			self.reply_to_message = json['reply_to_message']
		else:
			self.replied = False
		self.chat_id = json['chat']['id']
		self.chat_type = 'group' if str(self.chat_id).startswith('-') else 'user'
		self.message_id = json['message_id']
		self.user = json['from']
		self.any = json
		try:	self.text = json['text']
		except KeyError:	self.text = ""
		self.bot = bot
	def nextMessageHandler(self, handler,params={}):
		self.bot.nextMessages[str(self.chat_id)+"_"+str(self.user['id'])] = {'count':0,"handler":handler,"params":params}
	def send(self, msg, any={}, markup=""):
		formula = {'chat_id':self.chat_id, 'text':msg, 'reply_markup':markup}
		formula.update(any)
		return self.bot.method("sendMessage", formula)
	def delete(self):
		self.bot.method("deleteMessage", {'chat_id':self.chat_id, 'message_id':self.message_id})
	def sendPhoto(self, photo, comment="", markup=""):
		file = {'photo':open(photo, 'rb')}
		data = {'chat_id':self.chat_id, 'caption':comment, 'reply_markup':markup}
		post(self.bot.uri+"sendPhoto", data, files=file)


class InlineQuery:
	def __init__(self,json,bot):
		self.json = json
		self.From = self.json['from']
		self.query = self.json['query']
		self.bot = bot
		self.id = self.json['id']
		self.text = json['query']
	def builder(self):
		return InlineQueryBuilder(self.id, self.bot)
	
	def responde(self, mark):
		return self.bot.method("answerInlineQuery",{"inline_query_id":self.id, "results":mark})

class InlineQueryBuilder:
	def __init__(self,qid,bot):
		self.markup = '['
		self.id = qid
		self.rid = 1
	
	def addArticle(self, title, message_text, description="", reply_markup="{}"):
		self.markup += '{"reply_markup":'+reply_markup+',"type":"article","description":"'+description+'","id":'+str(self.rid)+', "title":"'+title+'", "message_text":"'+message_text+'"},'
		self.rid += 1
	#def addPhoto(self, photoUrl, title="", description="",caption=""):
		#self.markup +=  '{"photo_file_id":1,"type":"photo","description":"'+description+'","id":'+str(self.rid)+', "title":"'+title+'", "caption":"'+caption+'"},'
	def get(self):
		return sub(r'\,$','',self.markup)+"]"

class Bot:
	def __init__(self, token):
		self.token = token
		self.handler = lambda: 'ok'
		self.nextMessages = {}
		self.uri = "https://api.telegram.org/bot"+token+"/"
		self.proxies = {}
	def proxy(self, ip, port):
		self.proxies = {
		'https':"https://"+ip+":"+port,
		"http":"http://"+ip+":"+port
		}
	def CallbackQueryHandler(self, handler):
		self.callbackHandler = handler
	def message_handler(self, AsyncHandler):
		self.handler  = AsyncHandler
	
	def method(self, method, params={}):
		return get(self.uri+method, params, proxies=self.proxies).json()
	
	def InlineQueryHandler(self, handler):
		self.inlineHandler = handler
	
	def polling(self):
		try:
			new_offset = None
			while True:
				req = self.method("getUpdates", {'offset':new_offset, 'timeout':30, 'limit':40})
				if not 'result' in req:	continue
				if len(req['result']) == 0:	continue
				#print(req)
				new_offset = int(req["result"][-1]['update_id'])+1
				loop = Async()
				for event in req['result']:
					if 'callback_query' in event:
						if 'inline_query' in event['callback_query']:
							event = InlineQuery(event['callback_query']['inline_query'],self)
							loop.addTask(event)
							continue
						event = CallBackQuery(event['callback_query'], self)
						loop.addTask(self.callbackHandler(event))
						continue
					elif 'inline_query' in event:
						event = InlineQuery(event['inline_query'], self)
						loop.addTask(self.inlineHandler(event))
						continue
					event = Message(event, self)
					textString = str(event.chat_id)+"_"+str(event.user['id'])
					if textString in self.nextMessages:
						print("in")
						if self.nextMessages[textString]['count']==0:
							event.params = self.nextMessages[textString]['params']
							loop.addTask(self.nextMessages[textString]['handler'](event))
							self.nextMessages[textString]['count']=1
							del self.nextMessages[textString]
							continue
					if event == None:	continue
					loop.addTask(self.handler(event))
				loop.run()
		except KeyboardInterrupt:
			sys.exit(0)
			
			
class InlineButtons:
	def __init__(self,InlineMarkup=True):
		if InlineMarkup:
			self.markup = '{"inline_keyboard":['
		else:
			self.markup = ''
		self.te = InlineMarkup
	def add(self, text, callback_data, resizeable=False):
		resizeable = str(resizeable).lower()
		self.markup += '[{"text":"'+text+'", "callback_data":"'+callback_data+'", "resize_keyboard":"'+resizeable+'"}],'
			
	def Markup(self):
		data=sub(r"\,$", "", self.markup)+("]}" if self.te else ']')
		if self.te:
			self.markup = '{"inline_keyboard":['
		else:
			self.markup = ''
		return data

class Buttons:
	def __init__(self, resizeable=True):
		self.markup = '{"resize_keyboard":'+str(resizeable).lower()+',"keyboard":['
	def remove(self):
		return '{"remove_keyboard":true}'
	def add(self,text):
		self.markup += '[{"text":"'+text.replace('"','\\"')+'"}],'
	def Markup(self):
		return sub(r'\,$', '', self.markup)+']}'