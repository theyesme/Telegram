# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 08:32:32 2025

@author: savello
"""

from telethon.sync import TelegramClient
from tinydb import TinyDB, Query
import re
import json
import sys
import os

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

api_id = config['api_id']
api_hash = config['api_hash']
phone = config['phone']  
data_dir = config['data_dir']

system_version = "4.16.30-vxCUSTOM" #Important, prevents TG log outs
inf_db = TinyDB('data/influencers.json')
acc_db = TinyDB('data/infl_accounts.json')
client = TelegramClient('session_name', api_id, api_hash, system_version=system_version)


def get_our_chinf(infl_name, LAST_MESSAGES = 0):
    infl = Query()
    record = acc_db.search(infl.nickname == infl_name)
    return record[0]['tg'], int(record[0].get('last_msg') or 0) - LAST_MESSAGES


def utf_to_readable(file):
    #Decode unicode saved to json as '\uXXXX' to Russian readable format    
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        json_string = json.dumps(data, ensure_ascii=False, indent=4)
        
    with open(file.replace('.json','.rus.json'), 'w', encoding='utf-8') as f:
        f.write(json_string)


def beautify (file):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        json_string = json.dumps(data, indent=4)
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(json_string)


async def main(infl_name):
    global ch_name, msg_db
    if not(ch_name):
        ch_name, our_last_msg_id = get_our_chinf(infl_name)
        ch_name = ch_name[1:] 
        #save_directory = f'{data_dir}/{ch_name}'
        save_directory = data_dir
        #if not os.path.exists(save_directory):
        #    os.makedirs(save_directory)
        msg_db = TinyDB(f'{save_directory}/{ch_name}.json')
    
    #async with client:
    #Get last msg id from TG
    async for msg in client.iter_messages(ch_name, limit=1):
        tg_last_msg_id = msg.id
        infl = Query()
        acc_db.update({'last_msg': tg_last_msg_id}, infl.nickname == infl_name)
        break

    #Get only new messages from TG
    min_id = tg_last_msg_id if tg_last_msg_id <= our_last_msg_id else our_last_msg_id
    print (f'Last message id in channel {ch_name} is {tg_last_msg_id}')
    print (f'Last retrieved by us in channel {ch_name} is {our_last_msg_id}')
    
    async for msg in client.iter_messages(ch_name, min_id=min_id):
        if msg.text:
            links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', msg.text)
            msg_short = (msg.text)[:160] + "..."
            msg_date = str(msg.date.strftime('%Y-%m-%d %H:%M:%S'))
            print ("Inserting message ", msg.id, " ", msg_date, " ", msg_short[:20] + "...")
            msg_db.insert(({'msg_id': msg.id, 'date': msg_date, 'links': links, 'text': msg_short if msg_short else ''}))


with client:
    for record in inf_db:
        print (f'\nParsing TG channel for influencer: {record["nickname"]}')
        ch_name = None
        msg_db = None
        client.loop.run_until_complete(main(record['nickname']))
        
        chname, _ = get_our_chinf(record['nickname'])
        chname = chname[1:]
        beautify(f'{data_dir}/{chname}.json')
        utf_to_readable(f'{data_dir}/{chname}.json')

beautify('data/influencers.json')
beautify('data/infl_accounts.json')
        
    
    