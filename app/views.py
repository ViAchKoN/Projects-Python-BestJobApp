from aiohttp import web
from aiohttp_apispec import (
    request_schema,
    docs
)

from datacls import (
    UserDC,
    JobOfferDC,
    JobCandidateDC
)

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
    u = UserDC()
    jo = JobOfferDC()
    jc = JobCandidateDC()

    job_offer_id = request['data']['job_offer_id']
    phone_data = request['data']['phone']

    async with request.app['pool'].acquire() as connection:
        job_offer = await jo.get_job_offer_by_id(connection, job_offer_id)

        if not job_offer:
            raise CustomException(message='No job offer has been found with id: {0}.'.format(
                job_offer_id), status=422)

        candidates_list = await u.get_candidates_list_by_phone(connection, phone_data)

        if not candidates_list:
            raise CustomException(message='Users with these phone numbers have been not found phone: {0}.'
                                  .format(phone_data), status=422)
        job_candidates_list = await jc.get_job_candidates_list_by_job_offer_id(connection, job_offer_id)

        wrong_candidates = set([candidate.phone for candidate in candidates_list if
                                candidate.id not in [job_candidate.candidate_id for job_candidate in job_candidates_list]])

        if wrong_candidates:
            raise CustomException(message='User with phone number: {0} is not a candidate for job offer with id: {1}.'.format(
                phone_data, job_offer_id), status=403)
        employer = await u.get_employer_by_id(connection, job_offer.employer_id)

    return job_offer, employer, candidates_list


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
    u = UserDC()
    jo = JobOfferDC()
    jc = JobCandidateDC()

    post_data = request['data']
    phone_list_data = post_data['phoneList']
    employer_id_data = post_data['employer_id']

    async with request.app['pool'].acquire() as connection:
        user = await u.get_employer_by_id(connection, employer_id_data)

        if not user:
            return web.json_response({'message': 'No employer with id: {0} has been found.'.format(employer_id_data)},
                                     status=422)
        missing_phones = await user.get_missing_phones(connection, phone_list_data)

        if missing_phones:
            return web.json_response({'message': 'Users with these phone numbers have been not found.',
                                      'phoneList': missing_phones},
                                     status=422)
        async with connection.transaction():
            job_offer = await jo.create_job_offer(connection, employer_id_data, request['data']['department'],
                                                  request['data']['manager'], request['data']['salary'])

            candidates_list = await u.get_candidates_list_by_phone(connection, phone_list_data)

            await jc.fill_job_canidates(connection, job_offer.id, [candidate.id for candidate in candidates_list])

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
        job_offer, employer, candidates_list = await get_job_offer_data(request)
    except CustomException as e:
        return web.json_response({'message': e.message}, status=e.status)

    return web.json_response(
        {**JobOfferDC.Schema(exclude=['employer_id', 'accepted_by', 'start_date', 'id']).dump(job_offer),
         **UserDC.Schema(exclude=['id', 'phone', 'user_group_id']).dump(employer)})


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
    try:
        job_offer, employer, candidates_list = await get_job_offer_data(request)
    except CustomException as e:
        return web.json_response({'message': e.message}, status=e.status)

    jo = JobOfferDC()
    candidate_id = candidates_list[0].id

    async with request.app['pool'].acquire() as connection:
        job_offer = await jo.sign_job_offer(connection, candidate_id, request['data']['start_date'], request['data']['job_offer_id'])

        if candidate_id == job_offer.accepted_by:
            return web.json_response({'message': 'Offer was signed successfully. Start date: {0}.'
                                      .format(job_offer.start_date)}, status=200)
        else:
            return web.json_response({'message': 'Offer is not longer active.'}, status=401)
