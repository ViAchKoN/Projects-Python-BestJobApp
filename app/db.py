import asyncpg

from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, BigInteger, String, Boolean, Date
)

__all__ = ['user_group', 'user', 'job_offers', 'job_candidates']

meta = MetaData()


async def init_pg(app):
    config = app['config']['postgres']
    app['pool'] = await asyncpg.create_pool(
        database=config['database'],
        user=config['user'],
        password=config['password'],
        host=config['host'],
        port=config['port'],
        min_size=config['minsize'],
        max_size=config['maxsize'],
    )

user_groups = Table(
    'user_groups', meta,

    Column('id', Integer, primary_key=True),
    Column('name', String(200), nullable=False)
)

users = Table(
    'users', meta,

    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey(
        'user_groups.id', ondelete='CASCADE')),
    Column('name', String(50), nullable=False),
    Column('phone', String(50))
)

job_offers = Table(
    'job_offers', meta,

    Column('id', Integer, primary_key=True),
    Column('employer_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('department', String(200), nullable=False),
    Column('manager', String(50), nullable=False),
    Column('salary', Integer),
    Column('create_date', Date),
    Column('accepted_by', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('start_date', Date)
)

job_candidates = Table(
    'job_candidates', meta,

    Column('id', Integer, primary_key=True),
    Column('job_offer_id', Integer, ForeignKey('job_offers.id', ondelete='CASCADE')),
    Column('candidate_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
)
