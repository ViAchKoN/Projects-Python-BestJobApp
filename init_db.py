import argparse

from datetime import datetime

from sqlalchemy import create_engine, MetaData

from app.settings import CONFIG

from app.db import user_groups, users, job_offers, job_candidates


DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"

ADMIN_DB_URL = DSN.format(
    user='postgres', password='postgres', database='postgres',
    host='localhost', port=5432
)

admin_engine = create_engine(ADMIN_DB_URL, isolation_level='AUTOCOMMIT')


def parse_args() -> None:
    parser = argparse.ArgumentParser('Great Job app database initializer')
    parser.add_argument(
        'mode', type=str, help='Use "setup" to create db and fill it with test data '
        'or "teardown" to delete all database data assossiated with this app'
    )
    return parser.parse_args()


def setup_db(config) -> None:

    db_name = config['database']
    db_user = config['user']
    db_pass = config['password']

    conn = admin_engine.connect()
    conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
    conn.execute("DROP ROLE IF EXISTS %s" % db_user)
    conn.execute("CREATE USER %s WITH PASSWORD '%s'" % (db_user, db_pass))
    conn.execute("CREATE DATABASE %s" % db_name)
    conn.execute("GRANT ALL PRIVILEGES ON DATABASE %s TO %s" %
                 (db_name, db_user))
    conn.close()


def teardown_db(config) -> None:

    db_name = config['database']
    db_user = config['user']

    conn = admin_engine.connect()
    conn.execute("""
      SELECT pg_terminate_backend(pg_stat_activity.pid)
      FROM pg_stat_activity
      WHERE pg_stat_activity.datname = '%s'
        AND pid <> pg_backend_pid();""" % db_name)
    conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
    conn.execute("DROP ROLE IF EXISTS %s" % db_user)
    conn.close()


def create_tables(engine) -> None:
    meta = MetaData()
    meta.create_all(bind=engine, tables=[
                    user_groups, users, job_offers, job_candidates])


def sample_data(engine) -> None:
    conn = engine.connect()
    conn.execute(
        user_groups.insert(), [
            {'name': 'employer'},   # id = 1
            {'name': 'candidate'}   # id = 2
        ]
    )

    conn.execute(
        users.insert(), [
            {'group_id': 1, 'name': 'sberbank', 'phone': None},    # id = 1
            {'group_id': 1, 'name': 'domclick', 'phone': None},    # id = 2
            {'group_id': 2, 'name': 'candidate_1',
                'phone': '+111111111'},             # id = 3
            {'group_id': 2, 'name': 'candidate_2',
                'phone': '+222222222'},             # id = 4
            {'group_id': 2, 'name': 'candidate_3',
                'phone': '+333333333'},             # id = 5
            {'group_id': 2, 'name': 'candidate_4',
                'phone': '+444444444'},             # id = 6
        ]
    )

    conn.execute(
        job_offers.insert(), [
            {'employer_id': 1, 'department': 'department_1', 'manager': 'manager_1',
             'salary': 500000, 'create_date': datetime.now()},                                             # id = 1
            {'employer_id': 2, 'department': 'department_2', 'manager': 'manager_2',
             'salary': 100000000, 'create_date': datetime.now()},                                          # id = 2
        ]
    )

    conn.execute(
        job_candidates.insert(), [
            {'job_offer_id': 1, 'candidate_id': 3},   # id = 1
            {'job_offer_id': 1, 'candidate_id': 4},   # id = 2
            {'job_offer_id': 2, 'candidate_id': 5},   # id = 3
            {'job_offer_id': 2, 'candidate_id': 6}    # id = 4
        ]
    )

    conn.close()


if __name__ == '__main__':
    db_url = DSN.format(**CONFIG['postgres'])
    engine = create_engine(db_url)

    args = parse_args()

    mode = args.mode

    if mode == 'setup':
        setup_db(CONFIG['postgres'])
        create_tables(engine)
        sample_data(engine)
    elif mode == 'teardown':
        teardown_db(CONFIG['postgres'])
    print('Done!')
