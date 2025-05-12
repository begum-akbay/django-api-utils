from rest_framework.exceptions import APIException, ErrorDetail
from rest_framework import status
from rest_framework.utils.serializer_helpers import ReturnDict
from . import Message

from django.core.exceptions import ValidationError


class CustomValidation(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = {"detail": 'A server error occurred.'}

    def __init__(self, data, status_code):
        if status_code is not None:
            self.status_code = status_code

        if data is not None:
            self.detail = data


def raise_error(data, status_code=500):
    raise CustomValidation(data, status_code)


def raise_bad_request(text):
    raise raise_error(Message.create(text), 400)


def parse_errors(e: Exception):
    try:
        if isinstance(e, ValidationError):
            error_data = parse_errors(e.message_dict)

        elif isinstance(e, APIException):
            error_data = _parse_errors(e.detail)

        elif isinstance(e, ReturnDict):
            error_data = _parse_errors(e)

        else:
            return str(e)

        return str(error_data)

    except Exception as exception:
        return str(e)


def _parse_errors(error_dict):
    """
    Recursively parse a Django error dictionary containing ErrorDetail objects into a JSON-friendly format.
    """
    if isinstance(error_dict, dict):
        parsed = {}
        for key, value in error_dict.items():
            parsed[key] = _parse_errors(value)
        return parsed
    elif isinstance(error_dict, list):
        return [parse_errors(item) for item in error_dict]
    elif isinstance(error_dict, ErrorDetail):
        return str(error_dict)

    return error_dict
