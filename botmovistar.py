

import telebot
import time
import sys
import logging
import json
import requests
import pymysql.cursors
import socket
import time
import random
import urllib.request
import json
import os
import optparse
import sys

from telebot import types
from datetime import datetime
from download_movistar import download_movistar

API_TOKEN = ''
DOWNLOAD_PATH= ''
USERID=

bot = telebot.TeleBot(API_TOKEN)
telebot.logger.setLevel(logging.DEBUG)

def getrecordings(cid,actual): 
  try:    
    url = 'http://www-60.svc.imagenio.telefonica.net:2001/appserver/mvtv.do?action=recordingList&mode=0&state=2&firstItem='+str(actual)+'&numItems=10&intervalFromLastUpdate=0'
    jsondata = requests.get(url).json()
    recordings = jsondata['resultData']['result']
    listofdata= []
    markup = types.InlineKeyboardMarkup()
    inicio = 0
    if actual != inicio:
       markup.add(types.InlineKeyboardButton("Anteriores 10",callback_data=str(0)+","+str(int(actual)-10)))
    for recording in recordings:
      length=int((recording["endTime"]-recording["beginTime"])/1000)	
      markup.add(types.InlineKeyboardButton(recording['name'],callback_data=str(recording["serviceUID"])+","+str(recording["productID"])+","+str(length)+","))
    markup.add(types.InlineKeyboardButton("Siguientes 10",callback_data=str(0)+","+str(int(actual)+10)))
    bot.send_message(cid, "Elige grabacion a sincronizar", reply_markup=markup, disable_notification="true")
  
  except Exception as e:
    print(e)  


@bot.message_handler(commands=['descarga'])
def handdescarga(m): 
  if( m.chat.id == USERID):
    getrecordings(m.chat.id,0)

@bot.callback_query_handler(func=lambda call: True)      
def process_descarga_final(call):
  cid = call.from_user.id
  recordingdata= call.data.split(",")
  if recordingdata[0]== "0":
    getrecordings(cid,recordingdata[1])
  else :
    starthour=int(time.time())
    length=int(recordingdata[2])
    endhour=starthour+length
    endtext= datetime.fromtimestamp(endhour).strftime('%H:%M')
    url="http://www-60.svc.imagenio.telefonica.net:2001/appserver/mvtv.do?action=getRecordingData&extInfoID="+recordingdata[1]+"&channelID="+recordingdata[0]+"&mode=1&adType=1"
    with urllib.request.urlopen(url) as pagina:
      s = pagina.read()
      decoded =json.loads(s.decode('utf-8'))
      name=decoded['resultData']['name']
    pid = os.fork()
    if pid == 0:
      download_movistar(recordingdata[1],recordingdata[0],DOWNLOAD_PATH)
    else :
      acciones = types.ReplyKeyboardMarkup()
      acciones.one_time_keyboard=True
      acciones.resize_keyboard=True
      accion1 = types.KeyboardButton(text="/descarga")
      acciones.add(accion1)
      bot.send_message(cid, "Sincronización de "+name+" en marcha, acabará a las "+str(endtext), reply_markup=acciones)
def main_loop():
	try:
		bot.polling(True)
		while 1:
	       		time.sleep(3)
	except:
		pass
if __name__ == '__main__':
  try:
    main_loop()
  except KeyboardInterrupt:
    print >> sys.stderr, '\nExiting by user request.\n'
    sys.exit(0)
