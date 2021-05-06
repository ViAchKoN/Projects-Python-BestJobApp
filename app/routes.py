from views import index, create_job_offer, get_job_offer_details, sign_job_offer


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_route('POST', '/add_job_offer', create_job_offer)
    app.router.add_route('POST', '/get_job_offer_details', get_job_offer_details)
    app.router.add_route('PATCH', '/sign_job_offer', sign_job_offer)
