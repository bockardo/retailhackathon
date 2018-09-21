import telebot
from telebot import types
from collections import namedtuple
from settings import TOKEN
from dwapi.datawiz import DW
import datetime

bot = telebot.TeleBot(TOKEN)
dw = DW()
info = dw.get_client_info()
client = namedtuple("Client", info.keys())
client = client(**info)


def convert_human_format(df, columns):
    format_string = '{}:  {} \n'
    results = format_string.format(*columns)
    for obj in df.to_dict('split')['data']:
        results += format_string.format(*obj)
    return results


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('ТОП 10 товарів'))
    markup.add(types.KeyboardButton('Оборот по магазинам'))
    bot.send_message(message.chat.id, "Виберіть звіт!", reply_markup=markup)


@bot.message_handler(func=lambda message: 'ТОП 10 товарів' == message.text)
def top_products(message):
    date_to = client.date_to.date()
    date_from = client.date_to.date() - datetime.timedelta(days=30)
    df = dw.get_products_sale(date_from=date_from, date_to=date_to, view_type='raw')
    df = df.groupby('name').agg({'turnover': 'sum'}).sort_values('turnover', ascending=False).head(10).reset_index()
    df['turnover'] = df['turnover'].round(2)
    bot.send_message(message.chat.id, convert_human_format(df, columns=['Назва товара', 'Оборот']))


@bot.message_handler(func=lambda message: 'Оборот по магазинам' == message.text)
def turnover_by_shops(message):
    df = dw.get_categories_sale(view_type='row', per_shop=True)
    df = df.groupby('shop_name').agg({'turnover': 'sum'}).sort_values('turnover', ascending=False).head(10).reset_index()
    df['turnover'] = df['turnover'].round(2)
    result = convert_human_format(df, ['Назва магазина', 'Оборот'])
    bot.send_message(message.chat.id, result)
    


bot.polling()
