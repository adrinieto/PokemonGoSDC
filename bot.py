# coding: utf-8
import logging
from collections import Counter

import telebot

import models
from config import BOT_API_TOKEN

log = logging.getLogger(__name__)

GRAY_CIRCLE = u'\u26aa\ufe0f'
BLUE_HEART = u'\U0001f499'
RED_HEART = u'\u2764\ufe0f'
YELLOW_HEART = u'\U0001f49b'
TEAM_EMOJI = [GRAY_CIRCLE, BLUE_HEART, RED_HEART, YELLOW_HEART]

bot = telebot.TeleBot(BOT_API_TOKEN)


def prepare_text(text):
    return "```\n{}\n```".format(text)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hola, soy el bot de 'Pokemon Go SDC'.
Tengo información interesante sobre el estado de los gimnasios y los jugadores de Santiago de Compostela.
\
""")


@bot.message_handler(commands=['gimnasios'])
def gyms_by_team(message):
    gyms = models.Gym.select()
    team_counter = Counter([gym.team_id for gym in gyms])
    total_gyms = sum(team_counter.values())
    response = ""
    response += "Gimnasios por equipos\n"
    response += "-" * 30 + "\n"
    response += "Número de gimnasios: {}\n".format(models.Gym.select().count())
    teams = team_counter.items()
    teams = sorted(teams, key=lambda x: x[1], reverse=True)
    for team_id, gyms_owned in teams:
        team_emoji = TEAM_EMOJI[team_id].encode('utf-8')
        response += "{}{:10} {:5}  ({:.1f}%)\n".format(team_emoji, models.TEAMS[team_id], gyms_owned,
                                                       gyms_owned / float(total_gyms) * 100)

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['top_entrenadores'])
def top_trainers(message):
    top_trainers = models.Trainer.sorted_by_level()[:10]
    response = ""
    response += "TOP 10 trainers (by level)\n"
    response += "-" * 30 + "\n"
    response += "{:20} {:7}\n".format("TRAINER", "LEVEL")
    for trainer in top_trainers:
        team_emoji = TEAM_EMOJI[trainer.team_id].encode('utf-8')
        response += "{}{:20} {:<7}\n".format(team_emoji, trainer.name, trainer.level)

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['gimnasios_entrenadores'])
def gyms_per_trainer(message):
    top_gyms_owned = models.Trainer.top_gyms_owned()[:10]
    response = ""
    response += "Gimnasios por entrenador\n"
    response += "-" * 30 + "\n"
    response += "{:>2}  {:16} {:2}\n".format("#", "TRAINER", "LEVEL")
    for trainer in top_gyms_owned:
        team_emoji = TEAM_EMOJI[trainer.team_id].encode('utf-8')
        response += "{:2}  {}{:15} {:2}\n".format(
            len(trainer.gyms_membership), team_emoji, trainer.name, trainer.level)

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


# # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
# @bot.message_handler(func=lambda message: True)
# def echo_message(message):
#     print message
#     bot.reply_to(message, message.text)


bot.polling()
