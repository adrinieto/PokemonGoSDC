# coding: utf-8
import json
from collections import Counter, namedtuple
from datetime import datetime
from pprint import pprint
from time import sleep

import csv

from peewee import InsertQuery

import models
from models import create_tables, init_database
from utils import setup_logging, setup_api, timestamp_to_strftime

TEAMS = {
    0: 'Neutral',
    1: 'Mystic',
    2: 'Valor',
    3: 'Instint'
}


def read_gyms_from_csv(csv_file):
    gyms = []

    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)

        for row in reader:
            gym = {}
            for idx, field in enumerate(row):
                gym[header[idx]] = field
            gyms.append(gym)
    return gyms


def save_to_json(data):
    with open('gym_details.json', 'w') as output_file:
        json.dump(data, output_file, indent=2)


def read_data_from_json(path):
    with open(path) as data_file:
        return json.load(data_file)


def get_data_from_server(gyms):
    setup_logging()
    position = (42.878529, -8.544476, 0)  # Catedral
    api = setup_api(position)

    gym_details = []

    for gym in gyms:
        gym_lat = float(gym['latitude'])
        gym_lng = float(gym['longitude'])
        gym_id = gym['gym_id']

        api.set_position(gym_lat, gym_lng, 0)
        response_dict = api.get_gym_details(gym_id=gym_id)
        gym_detail = response_dict["responses"]["GET_GYM_DETAILS"]
        gym_details.append(gym_detail)

        sleep(0.2)
    return gym_details


def parse_and_insert_to_database(gym_details):
    create_tables()
    now = datetime.now()

    gyms = {}
    trainers = {}
    pokemons = {}
    gym_members = []

    for gym_detail in gym_details:
        gym_data = gym_detail['gym_state']['fort_data']
        gym_id = gym_data['id']
        gyms[gym_id] = {
            'id': gym_id,
            'name': gym_detail['name'],
            'description': gym_detail.get('description', ''),
            'team_id': gym_data.get('owned_by_team', models.Gym.UNCONTESTED),
            'guard_pokemon_id': gym_data.get('guard_pokemon_id', 0),
            'gym_points': gym_data.get('gym_points', 0),
            'is_in_battle': gym_data.get('is_in_battle', False),
            'enabled': gym_data['enabled'],
            'latitude': gym_data['latitude'],
            'longitude': gym_data['longitude'],
            'last_modified': datetime.utcfromtimestamp(
                gym_data['last_modified_timestamp_ms'] / 1000.0),
            'last_checked': now,
        }

        memberships = gym_detail['gym_state'].get('memberships', [])

        for member in memberships:
            pokemon_data = member['pokemon_data']
            trainer_data = member['trainer_public_profile']

            trainer_name = trainer_data['name']
            trainers[trainer_name] = {
                'name': trainer_name,
                'level': trainer_data['level'],
                'last_checked': now
            }

            pokemon_id = pokemon_data['id']
            pokemons[pokemon_id] = {
                'id': pokemon_id,
                'owner': pokemon_data['owner_name'],
                'pokemon_id': pokemon_data['pokemon_id'],
                'cp': pokemon_data['cp'],
                'last_checked': now
            }

            gym_members.append({
                'trainer': trainer_name,
                'gym': gym_id,
                'pokemon': pokemon_id
            })

    InsertQuery(models.Gym, rows=gyms.values()).upsert().execute()
    InsertQuery(models.Trainer, rows=trainers.values()).upsert().execute()
    InsertQuery(models.Pokemon, rows=pokemons.values()).upsert().execute()
    InsertQuery(models.GymMember, rows=gym_members).upsert().execute()


def print_gyms_by_team():
    gyms = models.Gym.select()
    team_counter = Counter([gym.team_id for gym in gyms])
    total_gyms = sum(team_counter.values())
    print
    print "Gimnasios por equipos"
    print "-" * 30
    print "Número de gimnasios: {}".format(total_gyms)
    for team, gyms_owned in team_counter.iteritems():
        print "{:10} {:5}  ({:.1f}%)".format(TEAMS[team], gyms_owned, gyms_owned / float(total_gyms) * 100)


def print_top_trainers():
    top_trainers = models.Trainer.sorted_by_level()[:10]
    print
    print "TOP 10 trainers (by level)"
    print "-" * 30
    print "{:20} {:7}".format("TRAINER", "LEVEL")
    for trainer in top_trainers:
        print "{:20} {:<7}".format(trainer.name, trainer.level)


def print_top_gyms_owned():
    top_gyms_owned = models.Trainer.top_gyms_owned()[:10]
    print
    print "Gimnasios por entrenador"
    print "-" * 30
    print "{:20} {:7} {:5}".format("TRAINER", "LEVEL", "GYMS OWNED")
    for trainer in top_gyms_owned:
        print "{:20} {:<7} {:5}".format(
            trainer.name, trainer.level, len(trainer.gyms_membership))


def print_gyms_details():
    print
    for gym in models.Gym.select():
        print "-", gym.name
        print "  Controlled by: {}".format(gym.team)
        print "  {} points (level {})".format(gym.gym_points, gym.level)
        print "  {} trainers:".format(len(gym.members))
        for member in gym.members:
            print "    - {:4} CP ({:15} level {:2})".format(
                member.pokemon.cp, member.trainer.name, member.trainer.level)


def main():
    gyms_dict = read_gyms_from_csv('gyms_santiago.csv')
    gym_details = get_data_from_server(gyms_dict)
    save_to_json(gym_details)

    # gym_details = read_data_from_json('gym_details.json')

    parse_and_insert_to_database(gym_details)

    print_gyms_details()
    print_gyms_by_team()
    print_top_trainers()
    print_top_gyms_owned()


if __name__ == '__main__':
    main()
