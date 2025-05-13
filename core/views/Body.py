from rest_framework import status

from core import Message, Exception as CustomException


def get(request, key, raise_exception=False):

    if key not in request.data:

        if raise_exception:
            raise_not_found_exception(key)

        return None

    value = request.data.get(key)

    if not value and raise_exception:
        raise_not_found_exception(key)

    return value


def raise_not_found_exception(key):
    raise CustomException.raise_bad_request(f"{key} is required.")


def get_int(request, key, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value is None:
        return default_value

    try:
        return int(value)

    except Exception as e:
        if raise_exception:
            raise CustomException.raise_bad_request(f"{key} value must be a valid integer")

        return default_value


def get_str(request, key, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value is None:
        return default_value

    return value


def get_enum(request, key, options, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value not in options:
        if raise_exception:
            raise CustomException.raise_bad_request(f"Invalid value {value}, must be one of {options}")

        return default_value

    return value


def get_str_list(request, key, raise_exception=False):
    value = get(request, key, raise_exception)

    if not isinstance(value, list) or not all(isinstance(f, str) for f in value):
        raise CustomException.raise_bad_request(f"Invalid data format. Expected a list of strings for {key}")

    return value


