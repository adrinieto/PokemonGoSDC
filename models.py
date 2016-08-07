# coding: utf-8
import logging
from datetime import datetime

from peewee import Model, SqliteDatabase, CharField, IntegerField, BooleanField, DoubleField, DateTimeField, \
    ForeignKeyField, fn, DeleteQuery, InsertQuery, DoesNotExist

from config import DATABASE

TEAMS = ['Neutral', 'Mystic', 'Valor', 'Instinct']
log = logging.getLogger(__name__)

db = None


def init_database():
    global db
    if db is not None:
        return db

    db = SqliteDatabase(DATABASE)
    log.info('Connecting to local SQLite database.')

    return db


def create_tables():
    init_database()
    db.connect()
    tables = [Trainer, Pokemon, Gym, GymMember, GymLog]
    # db.drop_tables(tables)
    db.create_tables(tables, safe=True)
    db.close()


class BaseModel(Model):
    class Meta:
        database = init_database()


class Trainer(BaseModel):
    name = CharField(primary_key=True, max_length=50)
    level = IntegerField()
    team_id = IntegerField()
    last_checked = DateTimeField()

    @property
    def team(self):
        return TEAMS[self.team_id]

    @classmethod
    def sorted_by_level(cls):
        return list(Trainer.select()
                    .order_by(Trainer.level.desc()))

    @classmethod
    def top_gyms_owned(cls):
        return Trainer.select(Trainer, GymMember).join(GymMember).group_by(GymMember.trainer).order_by(
            fn.COUNT(GymMember.trainer).desc())

    def __repr__(self):
        return "Trainer(name={}, level={}))".format(self.name, self.level)


class Pokemon(BaseModel):
    id = CharField(primary_key=True, max_length=50)
    owner = ForeignKeyField(Trainer, related_name='pokemons')
    pokemon_id = IntegerField()
    cp = IntegerField()
    last_checked = DateTimeField()

    def __repr__(self):
        return "Pokemon(id={}, owner={}))".format(self.id, self.owner)


class Gym(BaseModel):
    UNCONTESTED = 0
    TEAM_MYSTIC = 1
    TEAM_VALOR = 2
    TEAM_INSTINCT = 3

    id = CharField(primary_key=True, max_length=50)
    name = CharField(max_length=50)
    description = CharField(max_length=400)
    team_id = IntegerField()
    guard_pokemon_id = IntegerField()
    gym_points = IntegerField()
    is_in_battle = BooleanField()
    enabled = BooleanField()
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField()
    last_checked = DateTimeField()

    @property
    def team(self):
        return TEAMS[self.team_id]

    @property
    def level(self):
        points_per_level = [2000, 4000, 8000, 12000, 16000, 20000, 30000, 40000, 50000]
        level = 1
        while self.gym_points >= points_per_level[level - 1]:
            level += 1
        return level

    def __repr__(self):
        return "Gym(id={}, name={}, team_id={}, gym_points={}, last_modified={}, members_count={}))".format(
            self.id, self.name.encode('utf-8'), self.team_id, self.gym_points, self.last_modified, len(self.members))


class GymMember(BaseModel):
    trainer = ForeignKeyField(Trainer, related_name='gyms_membership')
    gym = ForeignKeyField(Gym, related_name='members')
    pokemon = ForeignKeyField(Pokemon)
    added_date = DateTimeField()

    def __repr__(self):
        return str(self.__dict__)
        # return "GymMember(trainer={}, gym={}, pokemon={}))".format(self.trainer, self.gym, self.pokemon)


class GymLog(BaseModel):
    IN_BATTLE = 'in_battle'
    STOP_BATTLE = 'stop_battle'
    GYM_TRAINED = 'gym_trained'
    GYM_ATTACKED = 'gym_attacked'
    GYM_CONQUESTED = 'gym_conquested'
    NEW_GYM_MEMBER = 'new_gym_member'
    LOST_GYM_MEMBER = 'lost_gym_member'
    UNKNOWN = 'unknown'

    timestamp = DateTimeField()
    gym = ForeignKeyField(Gym, related_name='actions')
    action = CharField(max_length=50)
    trainer = ForeignKeyField(Trainer, related_name='actions', null=True)
    points_change = IntegerField(null=True)
    gym_points = IntegerField(null=True)
    old_team_id = IntegerField(null=True)
    team_id = IntegerField(null=True)


@db.transaction()
def update_gym_members(gym_id, gym_members):
    deleted_gym_members = DeleteQuery(GymMember).where(GymMember.gym == gym_id).execute()
    if gym_members:  # Not insert if empty list
        InsertQuery(GymMember, rows=gym_members).upsert().execute()
    log.debug("Updated gym members from gym {} (deleted {})".format(gym_id, deleted_gym_members))


def update_gyms(gyms, gym_members_dict):
    actions = []
    gym_members_to_update = []
    for gym_id in gyms:
        try:
            gym = Gym.get(Gym.id == gym_id)
            # if gym.last_modified != gyms[gym_id]['last_modified']:
            gym_actions = check_gym_changes(gym, gyms[gym_id], gym_members_dict[gym_id])
            actions.extend(gym_actions)
            gym_members_to_update.append(gym_id)
        except DoesNotExist:
            log.debug("Adding new gym: {}".format(gyms[gym_id]['name']))
            gym_members_to_update.append(gym_id)

    if gyms:
        InsertQuery(Gym, rows=gyms.values()).upsert().execute()
    if actions:
        print(len(actions))
        InsertQuery(GymLog, rows=actions).upsert().execute()

    log.info("Upserted {} gyms".format(len(gyms)))

    for gym_id in gym_members_to_update:
        update_gym_members(gym_id, gym_members_dict[gym_id])
    log.info("{} gyms modified".format(len(gym_members_to_update)))


def check_gym_changes(gym, new_gym_dict, new_gym_members):
    now = datetime.now()  # TODO mover a otro sitio
    new_last_modified = new_gym_dict['last_modified']
    new_team_id = new_gym_dict['team_id']
    new_is_in_battle = new_gym_dict['is_in_battle']
    new_gym_points = new_gym_dict['gym_points']
    points_change = new_gym_points - gym.gym_points

    print "-"*30
    print gym.name
    print "Last modified:", gym.last_modified, new_last_modified
    print "Team: ", gym.team_id, new_team_id
    print "Is in battle:", gym.is_in_battle, new_is_in_battle
    print "Gym_points:", gym.gym_points, new_gym_points
    print "Members:", len(gym.members), len(new_gym_members)

    actions = []

    if new_is_in_battle:
        print "GYM IS BEEN ATTACKED NOW!"
        actions.append({
            'timestamp': now,
            'gym': gym.id,
            'action': GymLog.IN_BATTLE,
            'trainer': None,
            'points_change': None,
            'gym_points': None,
            'old_team_id': None,
            'team_id': None
        })

    if gym.is_in_battle is True and new_is_in_battle is False:
        print "STOPPED ATTACK..."
        actions.append({
            'timestamp': now,
            'gym': gym.id,
            'action': GymLog.STOP_BATTLE,
            'trainer': None,
            'points_change': None,
            'gym_points': None,
            'old_team_id': None,
            'team_id': None
        })

    if gym.team_id == new_team_id and points_change > 0:
        print "GYM TRAINED ({:+d} points)".format(points_change)
        actions.append({
            'timestamp': now,
            'gym': gym.id,
            'action': GymLog.GYM_TRAINED,
            'trainer': None,
            'points_change': points_change,
            'gym_points': new_gym_points,
            'old_team_id': None,
            'team_id': None
        })

    if gym.team_id == new_team_id and points_change < 0:
        print "GYM ATTACKED ({} points)".format(points_change)
        actions.append({
            'timestamp': now,
            'gym': gym.id,
            'action': GymLog.GYM_ATTACKED,
            'trainer': None,
            'points_change': points_change,
            'gym_points': new_gym_points,
            'old_team_id': None,
            'team_id': None
        })

    if gym.team_id != new_team_id:
        if new_team_id == 0:
            print "GYM IS NEUTRAL NOW"
        else:
            print "GYM CONQUESTED BY TEAM {}".format(TEAMS[new_team_id])
        actions.append({
            'timestamp': now,
            'gym': gym.id,
            'action': GymLog.GYM_CONQUESTED,
            'trainer': None,
            'points_change': None,
            'gym_points': new_gym_points,
            'old_team_id': gym.team_id,
            'team_id': new_team_id
        })

    if gym.team_id != new_team_id or len(gym.members) != len(new_gym_members):
        old_members = set([gym_member.trainer.name for gym_member in list(gym.members)])
        new_members = set([member['trainer'] for member in new_gym_members])
        new_members_in_gym = list(new_members - old_members)
        lost_members_in_gym = list(old_members - new_members)
        if new_members_in_gym:
            print "NEW GYM MEMBERS:", new_members_in_gym
            for member in new_members_in_gym:
                actions.append({
                    'timestamp': now,
                    'gym': gym.id,
                    'action': GymLog.NEW_GYM_MEMBER,
                    'trainer': member,
                    'points_change': None,
                    'gym_points': new_gym_points,
                    'old_team_id': None,
                    'team_id': None
                })
        if lost_members_in_gym:
            print "LOST GYM MEMBERS:", lost_members_in_gym
            for member in lost_members_in_gym:
                actions.append({
                    'timestamp': now,
                    'gym': gym.id,
                    'action': GymLog.LOST_GYM_MEMBER,
                    'trainer': member,
                    'points_change': None,
                    'gym_points': None,
                    'old_team_id': None,
                    'team_id': None
                })

        # print "Old members:"
        # pprint(list(gym.members))
        # print "New members:"
        # pprint(new_gym_members)

    if not actions:
        actions.append({
            'timestamp': now,
            'gym': gym.id,
            'action': GymLog.UNKNOWN,
            'trainer': None,
            'points_change': None,
            'gym_points': None,
            'old_team_id': None,
            'team_id': None
        })
    return actions