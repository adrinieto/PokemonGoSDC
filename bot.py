# coding: utf-8
import logging
from collections import Counter
from datetime import datetime, timedelta

import telebot
from peewee import DoesNotExist

import models
from config import BOT_API_TOKEN
from models import Trainer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
logging.getLogger(__name__).setLevel(logging.DEBUG)

POKEMON = ["Missingno", "Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard", "Squirtle",
           "Wartortle", "Blastoise", "Caterpie", "Metapod", "Butterfree", "Weedle", "Kakuna", "Beedrill", "Pidgey",
           "Pidgeotto", "Pidgeot", "Rattata", "Raticate", "Spearow", "Fearow", "Ekans", "Arbok", "Pikachu", "Raichu",
           "Sandshrew", "Sandslash", "Nidoran", "Nidorina", "Nidoqueen", "Nidoran", "Nidorino", "Nidoking", "Clefairy",
           "Clefable", "Vulpix", "Ninetales", "Jigglypuff", "Wigglytuff", "Zubat", "Golbat", "Oddish", "Gloom",
           "Vileplume", "Paras", "Parasect", "Venonat", "Venomoth", "Diglett", "Dugtrio", "Meowth", "Persian",
           "Psyduck", "Golduck", "Mankey", "Primeape", "Growlithe", "Arcanine", "Poliwag", "Poliwhirl", "Poliwrath",
           "Abra", "Kadabra", "Alakazam", "Machop", "Machoke", "Machamp", "Bellsprout", "Weepinbell", "Victreebel",
           "Tentacool", "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash", "Slowpoke", "Slowbro",
           "Magnemite", "Magneton", "Farfetch'd", "Doduo", "Dodrio", "Seel", "Dewgong", "Grimer", "Muk", "Shellder",
           "Cloyster", "Gastly", "Haunter", "Gengar", "Onix", "Drowzee", "Hypno", "Krabby", "Kingler", "Voltorb",
           "Electrode", "Exeggcute", "Exeggutor", "Cubone", "Marowak", "Hitmonlee", "Hitmonchan", "Lickitung",
           "Koffing", "Weezing", "Rhyhorn", "Rhydon", "Chansey", "Tangela", "Kangaskhan", "Horsea", "Seadra", "Goldeen",
           "Seaking", "Staryu", "Starmie", "Mr. Mime", "Scyther", "Jynx", "Electabuzz", "Magmar", "Pinsir", "Tauros",
           "Magikarp", "Gyarados", "Lapras", "Ditto", "Eevee", "Vaporeon", "Jolteon", "Flareon", "Porygon", "Omanyte",
           "Omastar", "Kabuto", "Kabutops", "Aerodactyl", "Snorlax", "Articuno", "Zapdos", "Moltres", "Dratini",
           "Dragonair", "Dragonite", "Mewtwo", "Mew"]

GRAY_CIRCLE = u'\u26aa\ufe0f'
BLUE_HEART = u'\U0001f499'
RED_HEART = u'\u2764\ufe0f'
YELLOW_HEART = u'\U0001f49b'
TEAM_EMOJI = [GRAY_CIRCLE, BLUE_HEART, RED_HEART, YELLOW_HEART]

CHEATERS_FILE = "cheaters.txt"
CHEATERS = set()

bot = telebot.TeleBot(BOT_API_TOKEN)


def load_cheaters(txt_file):
    global CHEATERS
    try:
        with open(txt_file) as fp:
            CHEATERS = set([x.strip() for x in fp.readlines()])
    except IOError:
        pass


def prepare_text(text):
    return "```\n{}\n```".format(text)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hola, soy el bot de 'Pokemon Go SDC'.
Tengo información interesante sobre el estado de los gimnasios y los entrenadores de Santiago de Compostela.
\
""")


@bot.message_handler(commands=['equipos'])
def gyms_by_team(message):
    log.debug("/equipos " + str(message.chat.__dict__))
    updated_time = list(models.Gym.select().order_by(models.Gym.last_checked.desc()).limit(1))[0].last_checked
    gyms = models.Gym.select()
    team_counter = Counter([gym.team_id for gym in gyms])
    total_gyms = sum(team_counter.values())
    response = ""
    response += "Gimnasios por equipos\n"
    response += "-" * 25 + "\n"
    response += "Total de gimnasios: {}\n".format(models.Gym.select().count())
    teams = team_counter.items()
    teams = sorted(teams, key=lambda x: x[1], reverse=True)
    for team_id, gyms_owned in teams:
        team_emoji = TEAM_EMOJI[team_id].encode('utf-8')
        response += "{}{:8} {:5}  ({:.1f}%)\n".format(team_emoji, models.TEAMS[team_id], gyms_owned,
                                                      gyms_owned / float(total_gyms) * 100)
    response += "Fecha: {}".format(updated_time.strftime('%H:%M %d/%m/%Y'))

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['top_entrenadores'])
def top_trainers(message):
    log.debug("/top_entrenadores " + str(message.chat.__dict__))
    updated_time = list(models.Trainer.select().order_by(models.Trainer.last_checked.desc()).limit(1))[0].last_checked
    top_trainers = models.Trainer.sorted_by_level()
    top_trainers_withouth_cheaters = [trainer for trainer in top_trainers if trainer.name not in CHEATERS
                                      if trainer.last_checked > datetime.now() + timedelta(days=-15)]

    response = ""
    response += "TOP 15 entrenadores de los últimos 15 días\n"
    response += "-" * 25 + "\n"
    response += "{:5} {:15}\n".format("NIVEL", "ENTRENADOR")
    for trainer in top_trainers_withouth_cheaters[:15]:
        team_emoji = TEAM_EMOJI[trainer.team_id].encode('utf-8')
        response += "{:^5} {}{:16} \n".format(trainer.level, team_emoji, trainer.name)
    response += "Fecha: {}".format(updated_time.strftime('%H:%M %d/%m/%Y'))

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['lista_chetos', 'top_chetos'])
def top_trainers(message):
    log.debug("/lista_chetos " + str(message.chat.__dict__))
    updated_time = list(models.Trainer.select().order_by(models.Trainer.last_checked.desc()).limit(1))[0].last_checked
    top_trainers = models.Trainer.sorted_by_level()
    top_cheaters = [trainer for trainer in top_trainers if trainer.name in CHEATERS
                    if trainer.last_checked > datetime.now() + timedelta(days=-15)]

    response = ""
    response += "TOP 10 chetos de los últimos 15 días\n"
    response += "-" * 25 + "\n"
    if len(top_cheaters) > 0:
        response += "{:5} {:15}\n".format("NIVEL", "ENTRENADOR")
        for trainer in top_cheaters[:10]:
            team_emoji = TEAM_EMOJI[trainer.team_id].encode('utf-8')
            response += "{:^5} {}{:16} \n".format(trainer.level, team_emoji, trainer.name)
    else:
        response += "No hay chetos registrados en los últimos días :)\n"
    response += "Fecha: {}".format(updated_time.strftime('%H:%M %d/%m/%Y'))

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['top_gimnasios'])
def gyms_per_trainer(message):
    log.debug("/top_gimnasios " + str(message.chat.__dict__))
    updated_time = list(models.Gym.select().order_by(models.Gym.last_checked.desc()).limit(1))[0].last_checked
    top_gyms_owned = models.Trainer.top_gyms_owned()[:10]
    response = ""
    response += "TOP 10 gimnasios por entrenador\n"
    response += "-" * 25 + "\n"
    response += "{:>2} {:16} {:2}\n".format("#", "ENTRENADOR", "NIVEL")
    for trainer in top_gyms_owned:
        cheater_flag = "*" if trainer.name in CHEATERS else ""
        team_emoji = TEAM_EMOJI[trainer.team_id].encode('utf-8')
        response += "{:2} {}{:15} {:2}\n".format(
            len(trainer.gyms_membership), team_emoji, cheater_flag + trainer.name, trainer.level)
    response += "Fecha: {}".format(updated_time.strftime('%H:%M %d/%m/%Y'))

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['entrenador'])
def entrenador(message):
    log.debug(message.text + str(message.chat.__dict__))
    try:
        trainer_name = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "Indica el nombre del entrenador: /entrenador NOMBRE")
        return
    try:
        trainer = Trainer.get(Trainer.name == trainer_name)
    except DoesNotExist:
        bot.reply_to(message, "No hay datos para ese entrenador")
        return

    team_emoji = TEAM_EMOJI[trainer.team_id].encode('utf-8')
    response = "{} {} (level {})\n".format(trainer.name, team_emoji, trainer.level)
    response += "-" * 25 + "\n"
    gyms = trainer.gyms_membership

    for gym in gyms:
        pokemon = gym.pokemon
        gym_name = gym.gym.name.encode('utf-8')
        response += "{:10} {:4}CP - {}\n".format(POKEMON[pokemon.pokemon_id], pokemon.cp, gym_name)

    if not gyms:
        response += "No controla ningún gimnasio"

    bot.reply_to(message, prepare_text(response), parse_mode="Markdown")


@bot.message_handler(commands=['about'])
def about(message):
    response = "Los datos utilizados por el Bot son extraídos de los gimnasios de Santiago y alrededores, " \
               "incluyendo Milladoiro y Los Tilos.\n" \
               "Si quieres contactar con el creador mándame un mensaje a @Nieto."
    bot.reply_to(message, response)


@bot.message_handler(func=lambda message: True)
def other_message(message):
    log.debug("Incorrect command: " + message.text + " " + str(message.chat.__dict__))

if __name__ == "__main__":
    load_cheaters(CHEATERS_FILE)
    print CHEATERS
    try:
        bot.polling(none_stop=True)
    except Exception as ex:
        log.error(ex)
