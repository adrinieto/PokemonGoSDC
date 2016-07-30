# coding: utf-8
import logging

from peewee import Model, SqliteDatabase, CharField, IntegerField, BooleanField, DoubleField, DateTimeField, \
    ForeignKeyField, fn, DeleteQuery, InsertQuery, DoesNotExist

from config import DATABASE

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
    tables = [Trainer, Pokemon, Gym, GymMember]
    # db.drop_tables(tables)
    db.create_tables(tables, safe=True)
    db.close()


TEAMS = ['Uncontested', 'Mystic', 'Valor', 'Instint']


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


@db.transaction()
def update_gym_members(gym_id, gym_members):
    deleted_gym_members = DeleteQuery(GymMember).where(GymMember.gym == gym_id).execute()
    if gym_members:  # Not insert if empty list
        InsertQuery(GymMember, rows=gym_members).upsert().execute()
    log.debug("Updated gym members from gym {} (deleted {})".format(gym_id, deleted_gym_members))


def update_gyms(gyms, gym_members_dict):
    gym_members_to_update = []
    for gym_id in gyms:
        try:
            gym = Gym.get(Gym.id == gym_id)
            if gym.last_modified != gyms[gym.id]['last_modified']:
                gym_members_to_update.append(gym_id)
        except DoesNotExist:
            gym_members_to_update.append(gym_id)

    InsertQuery(Gym, rows=gyms.values()).upsert().execute()
    log.info("Upserted {} gyms".format(len(gyms)))

    for gym_id in gym_members_to_update:
        update_gym_members(gym_id, gym_members_dict[gym_id])
    log.info("{} gyms modified".format(len(gym_members_to_update)))
