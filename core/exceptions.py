from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "error").upper()
        message = str(getattr(exc, "detail", exc))
        response.data = {
            "error": {
                "code": code,
                "message": message,
            }
        }
    return response
