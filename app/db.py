import asyncpg

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Date
)

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


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


class UserGroups(Base):
    __tablename__ = 'user_groups'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_group_id = Column(Integer, ForeignKey(
        'user_groups.id', ondelete='CASCADE'))
    name = Column(String(50), nullable=False)
    phone = Column(String(50))

    user_group = relationship("UserGroups")


class JobOffers(Base):
    __tablename__ = 'job_offers'

    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    department = Column(String(200), nullable=False)
    manager = Column(String(50), nullable=False)
    salary = Column(Integer)
    create_date = Column(Date)
    accepted_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    start_date = Column(Date)

    employer = relationship("Users", foreign_keys=[employer_id])
    accepted = relationship("Users", foreign_keys=[accepted_by])


class JobCandidates(Base):
    __tablename__ = 'job_candidates'

    id = Column(Integer, primary_key=True)
    job_offer_id = Column(Integer, ForeignKey(
        'job_offers.id', ondelete='CASCADE'))
    candidate_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    job_offer = relationship("JobOffers")
    candidate = relationship("Users")
