# coding: utf-8
import logging

from peewee import Model, SqliteDatabase, CharField, IntegerField, BooleanField, DoubleField, DateTimeField, \
    ForeignKeyField, fn

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


class BaseModel(Model):
    class Meta:
        database = init_database()


class Trainer(BaseModel):
    name = CharField(primary_key=True, max_length=50)
    level = IntegerField()
    last_checked = DateTimeField()

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
    TEAMS = ['Uncontested', 'Mystic', 'Valor', 'Instint']
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
        return Gym.TEAMS[self.team_id]

    @property
    def level(self):
        points_per_level = [2000, 4000, 8000, 12000, 16000, 20000, 30000, 40000, 50000]
        level = 1
        while self.gym_points >= points_per_level[level - 1]:
            level += 1
        return level

    @classmethod
    def get_by_teams(cls):
        gyms = Gym.select()

    def __repr__(self):
        return "Gym(id={}, name={}, team_id={}, gym_points={}, last_modified={}, members_count={}))".format(
            self.id, self.name.encode('utf-8'), self.team_id, self.gym_points, self.last_modified, len(self.members))


class GymMember(BaseModel):
    trainer = ForeignKeyField(Trainer, related_name='gyms_membership')
    gym = ForeignKeyField(Gym, related_name='members')
    pokemon = ForeignKeyField(Pokemon)

    def __repr__(self):
        return str(self.__dict__)
        # return "GymMember(trainer={}, gym={}, pokemon={}))".format(self.trainer, self.gym, self.pokemon)
