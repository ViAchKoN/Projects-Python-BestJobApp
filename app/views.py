from datetime import (
    datetime,
    timedelta
)

from aiohttp import web
from aiohttp_apispec import (
    request_schema,
    docs
)

import db

from schemas import (
    Message,
    JobOffer,
    JobOfferWithPhones,
    PhoneListValidation,
    ShowOffer,
    SignOffer
)

from utils import CustomException


async def index(request: web.Request) -> web.Response:
    return web.Response(text='Hello! This is Super Job App!')


async def get_job_offer_data(request):
    job_offer_id = request['data']['job_offer_id']

    async with request.app['pool'].acquire() as connection:
        records = await connection.fetch('''
            SELECT
                t1.candidate_id, t2.phone, t3.department, t3.manager
                , t3.salary, t3.start_date, t4.name
            FROM
                (SELECT
                    candidate_id , job_offer_id
                FROM
                    job_candidates jc
                WHERE
                    job_offer_id = $1) AS t1
                LEFT JOIN
                (SELECT
                    id, phone
                FROM
                    users u
                WHERE
                    user_group_id = 2) AS t2 ON t1.candidate_id = t2.id
                LEFT JOIN
                (SELECT
                    *
                FROM
                    job_offers jo
                ) AS t3 ON t3.id = t1.job_offer_id
                LEFT JOIN
                (SELECT
                    *
                FROM
                    users u
                ) AS t4 ON t4.id = t3.employer_id
        ''', job_offer_id)

        if len(records) == 0:
            raise CustomException(message='No job offer has been found with id: {0}.'.format(job_offer_id), status=422)

        phone = request['data']['phone']

        data = [dict(q) for q in records]

        data = [item for item in data if item['phone'] == phone]

        if not data:
            raise CustomException(message='User with phone number: {0} is not a candidate for job offer with id: {1}.'.format(phone, job_offer_id), status=403)
    return data


@docs(
    tags=['job_offer'],
    summary='Create new job offer',
    description='Add new job offer to database',
    responses={
        200: {'description': 'Ok. Job offer created.', 'schema': Message},
        422: {'description': 'Validation error. ', 'schema': PhoneListValidation},
    }
)
@request_schema(JobOfferWithPhones)
async def create_job_offer(request: web.Request) -> web.json_response:
    post_data = request['data']
    phone_list_data = post_data['phoneList']
    employer_id_data = post_data['employer_id']

    async with request.app['pool'].acquire() as connection:
        records = await connection.fetch('''
            SELECT
                *
            FROM
                users
            WHERE
                user_group_id = 1
                AND
                id = $1
            ''', employer_id_data)
        if len(records) == 0:
            return web.json_response({'message': 'No employer with id: {0} has been found.'.format(employer_id_data)},
                                     status=422)

        records = await connection.fetch('''
            SELECT
                id, phone
            FROM
                users
            WHERE
                phone IS NOT NULL
                AND user_group_id = 2
        ''')
        user_phones = [dict(q) for q in records]
        user_phones_dict = {element['id']: element['phone']
                            for element in user_phones if element['phone'] in phone_list_data for k, v in element.items()}

        found_phones = set(user_phones_dict.values()
                           ).intersection(set(phone_list_data))
        different_phones = list(set(phone_list_data) - found_phones)

        if different_phones:
            return web.json_response({'message': 'Users with these phone numbers have been not found.',
                                      'phoneList': different_phones},
                                     status=422)
        async with connection.transaction():
            res = await connection.fetch('''
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
                ''', employer_id_data,
                post_data['department'],
                post_data['manager'],
                post_data['salary'],
                datetime.now()
            )

            data = [(res[0].get('id'), item) for item in user_phones_dict]

            await connection.copy_records_to_table('job_candidates', records=data, columns=('job_offer_id', 'candidate_id'))

    return web.json_response({'message': 'Successful.'}, status=200)


@docs(
    tags=['job_offer'],
    summary='Show offer to canditate.',
    description='Show offer details to canditate.',
    responses={
        200: {'description': 'Ok.', 'schema': JobOffer},
        403: {'description': 'Permission error.', 'schema': Message},
        422: {'description': 'Validation error. ', 'schema': Message},
    }
)
@request_schema(ShowOffer)
async def get_job_offer_details(request: web.Request) -> web.json_response:
    try:
        data = await get_job_offer_data(request)
    except CustomException as e:
        return web.json_response({'message': e.message}, status=e.status)

    return web.json_response(JobOffer(exclude=['employer_id']).dump(data[0]), status=200)


@docs(
    tags=['job_offer'],
    summary='Sign offer by canditate.',
    description='Sign offer by canditate.',
    responses={
        200: {'description': 'Ok.', 'schema': JobOffer},
        401: {'description': 'Offer is not longer active.', 'schema': Message},
        403: {'description': 'Permission error.', 'schema': Message},
        422: {'description': 'Validation error.', 'schema': Message},
    }
)
@request_schema(SignOffer)
async def sign_job_offer(request: web.Request) -> web.json_response:
    start_date = request['data']['start_date']

    min_date = datetime.now().date() + timedelta(days=1)
    max_date = datetime.now().date() + timedelta(days=30)

    if not min_date <= start_date <= max_date:
        return web.json_response({'message': 'Wrong start date provided. Start date should be between {0} and {1}, provided: {2}.'
                                  .format(min_date, max_date, start_date)}, status=422)

    try:
        data = await get_job_offer_data(request)
    except CustomException as e:
        return web.json_response({'message': e.message}, status=e.status)

    async with request.app['pool'].acquire() as connection:
        candiate_id = data[0]['candidate_id']
        job_offer_id = request['data']['job_offer_id']

        res = await connection.fetch('''
            UPDATE
                job_offers
            SET
                accepted_by = COALESCE(accepted_by, $1)
                , start_date = COALESCE(start_date, $2)
            WHERE
                id = $3
            RETURNING accepted_by, start_date
        ''',  candiate_id, start_date, job_offer_id)
        if candiate_id == res[0].get('accepted_by'):
            return web.json_response({'message': 'Offer was signed successfully. Start date: {0}.'
                                      .format(res[0].get('start_date'))}, status=200)
        else:
            return web.json_response({'message': 'Offer is not longer active.'}, status=401)
