from django.conf import settings
from django.utils.translation import activate


class RequestLanguageMiddleware:
    """Keep the selected language active across requests in development and production."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = request.session.get("language") or request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        supported = {code for code, _label in settings.LANGUAGES}
        if language in supported:
            activate(language)
            request.LANGUAGE_CODE = language
        return self.get_response(request)
