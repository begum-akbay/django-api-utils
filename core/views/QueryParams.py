from core import DateUtils, Exception as CustomException


def get(request, key, raise_exception=False):

    if key not in request.query_params:

        if raise_exception:
            raise_not_found_exception(key)

        return None

    return request.query_params.get(key)


def raise_not_found_exception(key):
    raise CustomException.raise_bad_request(f"{key} not found")


def get_bool(request, key, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value is None:
        return default_value

    if value.lower() not in ["true", "false"]:
        return default_value

    return value.lower() == "true"


def get_str(request, key, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value is None:
        return default_value

    return value


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


def get_float(request, key, default_value=None, raise_exception=False):
    value = get(request, key, raise_exception)

    if value is None:
        return default_value

    try:
        return float(value)
    except Exception as e:
        if raise_exception:
            raise CustomException.raise_bad_request(f"{key} value must be a valid float")

        return default_value


def get_int_list(request, key, default_value=None, raise_exception=False):
    list = default_value
    source = get_str(request, key, raise_exception=raise_exception)

    if source is None:
        return list

    source = source.rstrip(',')
    list_str = source.split(",")

    try:
        for str in list_str:
            value = int(str)
            list.append(value)
    except:
        if raise_exception:
            raise CustomException.raise_bad_request(f"{key} contained an invalid valid float")

        return default_value

    return list


def get_str_list(request, key, default_value=None, raise_exception=False):
    source = get_str(request, key, default_value, raise_exception)

    if source is None:
        return default_value

    source = source.strip()

    if len(source) == 0:
        return default_value

    source = source.rstrip(',')
    list = source.split(",")

    return list


def get_enum_list(request, key, options, default_value=None, raise_exception=False):
    list = get_str_list(request, key, default_value, raise_exception)

    if list is None:
        return default_value

    for item in list:
        if item not in options:
            if raise_exception:
                raise CustomException.raise_bad_request(f"Invalid value '{item}', must be one of {options}")


    return list


def get_enum(request, key, options, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value not in options:
        if raise_exception:
            raise CustomException.raise_bad_request(f"Invalid value {value}, must be one of {options}")

        return default_value

    return value


def get_datetime(request, key, default_value=None, raise_exception=False):

    datetime_str = get(request, key, raise_exception)

    if datetime_str is None:
        return default_value

    try:
        DateUtils.validate(datetime_str)
    except Exception as error:
        if raise_exception:
            raise CustomException.raise_bad_request(error)
        return default_value

    datetime = DateUtils.parse(datetime_str)

    return datetime


def get_date(request, key, default_value=None, raise_exception=False):

    date_str = get(request, key, raise_exception)
    if date_str is None:
        return default_value
    try:
        DateUtils.validate(date_str)
    except Exception as error:
        if raise_exception:
            raise CustomException.raise_bad_request(error)
        return default_value
    date = DateUtils.parse_date(date_str)
    return date


