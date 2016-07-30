# coding: utf-8
import csv
import json
import logging
from collections import Counter
from datetime import datetime
from time import sleep

from peewee import InsertQuery

import models
from models import create_tables
from utils import setup_logging, setup_api

log = logging.getLogger(__name__)

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
    gym_members = {}

    for gym_detail in gym_details:
        if 'gym_state' not in gym_detail:  # Sometimes the request fail and no data is returned. status code = 2
            log.error("Error requesting gym details. Response: {}".format(gym_detail))
            continue

        gym_data = gym_detail['gym_state']['fort_data']
        gym_id = gym_data['id']
        team_id = gym_data.get('owned_by_team', models.Gym.UNCONTESTED)
        gyms[gym_id] = {
            'id': gym_id,
            'name': gym_detail['name'],
            'description': gym_detail.get('description', ''),
            'team_id': team_id,
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

        members = []
        for member in memberships:
            pokemon_data = member['pokemon_data']
            trainer_data = member['trainer_public_profile']

            trainer_name = trainer_data['name']
            trainers[trainer_name] = {
                'name': trainer_name,
                'level': trainer_data['level'],
                'team_id': team_id,
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

            members.append({
                'trainer': trainer_name,
                'gym': gym_id,
                'pokemon': pokemon_id,
                'added_date': now
            })

        gym_members[gym_id] = members

    models.update_gyms(gyms, gym_members)

    InsertQuery(models.Trainer, rows=trainers.values()).upsert().execute()
    log.info("Upserted {} trainers".format(len(trainers)))
    InsertQuery(models.Pokemon, rows=pokemons.values()).upsert().execute()
    log.info("Upserted {} pokemons".format(len(pokemons)))


def print_gyms_by_team():
    gyms = models.Gym.select()
    team_counter = Counter([gym.team for gym in gyms])
    total_gyms = sum(team_counter.values())
    print
    print "Gimnasios por equipos"
    print "-" * 30
    print "Número de gimnasios: {}".format(models.Gym.select().count())
    for team, gyms_owned in team_counter.iteritems():
        print "{:10} {:5}  ({:.1f}%)".format(team, gyms_owned, gyms_owned / float(total_gyms) * 100)


def print_top_trainers():
    top_trainers = models.Trainer.sorted_by_level()[:10]
    print
    print "TOP 10 trainers (by level)"
    print "-" * 30
    print "{:20} {:7} {:7}".format("TRAINER", "LEVEL", "TEAM")
    for trainer in top_trainers:
        print "{:20} {:<7} {:7}".format(trainer.name, trainer.level, trainer.team)


def print_top_gyms_owned():
    top_gyms_owned = models.Trainer.top_gyms_owned()[:10]
    print
    print "Gimnasios por entrenador"
    print "-" * 30
    print "{:20} {:7} {:7} {:5}".format("TRAINER", "LEVEL", "TEAM", "GYMS OWNED")
    for trainer in top_gyms_owned:
        print "{:20} {:<7} {:7} {:5}".format(
            trainer.name, trainer.level, trainer.team, len(trainer.gyms_membership))


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

    gym_details = read_data_from_json('gym_details.json')

    parse_and_insert_to_database(gym_details)

    print_gyms_details()
    print_gyms_by_team()
    print_top_trainers()
    print_top_gyms_owned()


if __name__ == '__main__':
    main()
