
from typing import List

from datetime import datetime

from marshmallow_dataclass import dataclass

from aiohttp import web
from asyncpg import connection


@dataclass
class UserGroupDC:
    id: int = None
    name: str = None


@dataclass
class UserDC:
    id: int = None
    user_group_id: int = None
    name: str = None
    phone: str = None

    @staticmethod
    async def get_employer_by_id(conn: connection, id: int):
        sql_query = '''
            SELECT
                *
            FROM
                users
            WHERE
                user_group_id = 1
                AND id = {0}
            '''.format(id)
        res = await conn.fetchrow(sql_query)
        if not res:
            return None
        return UserDC(**res)

    @staticmethod
    async def get_candidates_list(conn: connection):
        sql_query = '''
            SELECT
                *
            FROM
                users
            WHERE
                phone IS NOT NULL
                AND user_group_id = 2
            '''
        res = await conn.fetch(sql_query)
        return [UserDC(**item) for item in res]

    async def get_missing_phones(self, conn: connection, phone_list_data=List[str]) -> List[str]:
        candidates_list = await self.get_candidates_list(conn)
        return list(set(phone_list_data).difference(set(candidate.phone for candidate in candidates_list)))

    @staticmethod
    async def get_candidates_list_by_phone(conn: connection, phone_data: List[str] or str):
        if isinstance(phone_data, str):
            phone_data = [phone_data]

        sql_query = '''
            SELECT
                *
            FROM
                users
            WHERE
                user_group_id = 2
                AND phone = any($1::text[])
            '''
        res = await conn.fetch(sql_query, phone_data)
        return [UserDC(**item) for item in res]


@dataclass
class JobOfferDC:
    id: int = None
    employer_id: int = None
    department: str = None
    manager: str = None
    salary: int = None
    create_date: datetime = None
    accepted_by: int = None
    start_date: datetime = None

    @staticmethod
    async def get_job_offer_by_id(conn: connection, id: int):
        sql_query = '''
            SELECT
                *
            FROM
                job_offers
            WHERE
                id = {0}
        '''.format(id)

        res = await conn.fetchrow(sql_query)
        if not res:
            return None
        return JobOfferDC(**res)

    async def create_job_offer(self, conn: connection, employer_id: int,
                               department: str, manager: str, salary: int):
        sql_query = '''
            INSERT INTO
                job_offers(
                    employer_id,
                    department,
                    manager,
                    salary,
                    create_date
                )
            VALUES
                ($1, $2, $3, $4, $5)
            RETURNING id
        '''

        res = await conn.fetchrow(sql_query,
                                  employer_id,
                                  department,
                                  manager,
                                  salary,
                                  datetime.now())

        return await self.get_job_offer_by_id(conn, res['id'])

    async def sign_job_offer(self, conn: connection, candidate_id: int, start_date: datetime, job_offer_id: int):
        await conn.execute('''
            UPDATE
                job_offers
            SET
                accepted_by = COALESCE(accepted_by, $1)
                , start_date = COALESCE(start_date, $2)
            WHERE
                id = $3
        ''',  candidate_id, start_date, job_offer_id)
        return await self.get_job_offer_by_id(conn, job_offer_id)


@dataclass
class JobCandidateDC:
    id: int = None
    job_offer_id: int = None
    candidate_id: int = None

    @staticmethod
    async def fill_job_canidates(conn: connection, job_offer_id: int, job_candidates_id_list: List[int]):
        data = [(job_offer_id, item) for item in job_candidates_id_list]
        await conn.copy_records_to_table('job_candidates', records=data, columns=('job_offer_id', 'candidate_id'))

    @staticmethod
    async def get_job_candidates_list_by_job_offer_id(conn: connection, job_offer_id: int):
        sql_query = '''
            SELECT
                *
            FROM
                job_candidates
            WHERE
                job_offer_id = {0}
        '''.format(job_offer_id)

        res = await conn.fetch(sql_query)
        return [JobCandidateDC(**item) for item in res]
