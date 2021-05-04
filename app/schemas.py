from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)

class JobOffer(Schema):
    employer_id = fields.Integer(required=True)
    department = fields.String(required=True)
    manager = fields.String(required=True)
    salary = fields.Integer(required=True)
    name = fields.String()

    @validates('employer_id')
    def validate_employer_id(self, data, **kwargs):
        if data <= 0:
            raise ValidationError('employer_id must be bigger than 0.')


class JobOfferWithPhones(JobOffer):
    phoneList = fields.List(fields.String(), required=True)

    class Meta:
        exclude = ('name',)


class Message(Schema):
    message = fields.String()


class PhoneListValidation(Message):
    phoneList = fields.List(fields.String())


class ShowOffer(Schema):
    job_offer_id = fields.Integer(required=True)
    phone = fields.String(required=True)


class SignOffer(ShowOffer):
    start_date = fields.Date(required=True)
