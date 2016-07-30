import json
from collections import Counter, namedtuple
from datetime import datetime
from pprint import pprint
from time import sleep

import csv

from utils import setup_logging, setup_api, timestamp_to_strftime

TEAMS = {
    0: 'neutral',
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


def gyms_by_team(gym_details):
    teams = []
    for gym_detail in gym_details:
        if 'owned_by_team' not in gym_detail['gym_state']['fort_data']:
            teams.append(0)
            continue
        team = int(gym_detail['gym_state']['fort_data']['owned_by_team'])
        teams.append(team)

    team_counter = Counter(teams)
    total_gyms = sum(team_counter.values())
    print "Total gyms: %s" % total_gyms
    for team, gyms_owned in team_counter.iteritems():
        print "{:10} {:2}  ({:.1f}%)".format(TEAMS[team], gyms_owned, gyms_owned / float(total_gyms) * 100)


def main():
    gyms = read_gyms_from_csv('gyms_santiago.csv')
    gym_details = get_data_from_server(gyms)
    save_to_json(gym_details)

    # gym_details = read_data_from_json('gym_details.json')

    gyms_by_team(gym_details)

    gym_members_counter = Counter()

    trainers_level = {}
    for gym_detail in gym_details:
        gym_data = gym_detail['gym_state']['fort_data']
        owned_by_team = int(gym_data['owned_by_team']) if 'owned_by_team' in gym_data else 0
        gym_members = gym_detail['gym_state']['memberships'] if 'owned_by_team' in gym_data else []
        is_in_battle = gym_data['is_in_battle'] if 'is_in_battle' in gym_data else False
        last_modified = timestamp_to_strftime(gym_data['last_modified_timestamp_ms']) if 'last_modified_timestamp_ms' in gym_data else 0
        gym_points = gym_data['gym_points'] if 'gym_points' in gym_data else 0
        print u"{name}: level {level} ({points} points) team {team} (last interaction at {last_modified} {in_battle}".format(
            name=gym_detail['name'],
            level=len(gym_members),
            points=gym_points,
            team=TEAMS[owned_by_team],
            last_modified=last_modified,
            in_battle='' if not is_in_battle else 'IN BATTLE!!'
        )
        member_names = []
        for member in gym_members:
            pokemon_data = member['pokemon_data']
            trainer_data = member['trainer_public_profile']
            trainer_name = trainer_data['name']
            trainer_level = trainer_data['level']

            trainers_level[trainer_name] = trainer_level

            member_names.append(trainer_name)
            print "\t{owner_name:15}  {level:2}{cp:8} CP ".format(
                owner_name=trainer_name,
                level=trainer_level,
                cp=pokemon_data['cp'],
            )
        gym_members_counter.update(member_names)

    for trainer_name, count in gym_members_counter.most_common(15):
        print "{:15} (level {:2}): {:2} gyms".format(trainer_name, trainers_level[trainer_name], count)

    trainers = sorted(trainers_level.items(), key=lambda x: x[1], reverse=True)
    pprint(trainers[:10])


if __name__ == '__main__':
    main()
