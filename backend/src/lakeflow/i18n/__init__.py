"""
LakeFlow i18n: English + 5 languages (vi, zh, ja, fr, es).
- Use t(key, locale, **params) for translation.
- Use get_locale_from_request(request) to get locale from ?locale= or Accept-Language.
- Exception handler translates HTTPException when detail is {"key": "...", ...params}.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from .strings import (
    STRINGS,
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
)


def t(key: str, locale: str = DEFAULT_LOCALE, **params) -> str:
    """Translate key for locale, with optional {placeholder} substitution."""
    locale = locale if locale in STRINGS else DEFAULT_LOCALE
    strings = STRINGS.get(locale, STRINGS[DEFAULT_LOCALE])
    template = strings.get(key) or STRINGS[DEFAULT_LOCALE].get(key) or key

    # Format params: list -> ", ".join for readability
    formatted = {}
    for k, v in params.items():
        if isinstance(v, list) and v and isinstance(v[0], str):
            formatted[k] = ", ".join(str(x) for x in v)
        else:
            formatted[k] = v
    try:
        return template.format(**formatted)
    except KeyError:
        return template


def get_locale_from_request(request: Request) -> str:
    """
    Get locale from query ?locale= or Accept-Language header.
    Falls back to DEFAULT_LOCALE.
    """
    # 1. Query param ?locale=vi
    locale = request.query_params.get("locale") or request.query_params.get("lang")
    if locale:
        locale = locale.split("-")[0].strip().lower()
        if locale in STRINGS:
            return locale

    # 2. Accept-Language: vi,en;q=0.9
    accept = request.headers.get("accept-language", "")
    for part in accept.split(","):
        lang = part.split(";")[0].strip().split("-")[0].lower()
        if lang in STRINGS:
            return lang
    return DEFAULT_LOCALE


def i18n_detail(key: str, **params):
    """
    Create HTTPException detail that the exception handler will translate.
    Use: raise HTTPException(status_code=400, detail=i18n_detail("auth.invalid_credentials"))
    Or:  raise HTTPException(status_code=400, detail=i18n_detail("system.missing_zones", missing=missing))
    """
    if params:
        return {"key": key, **params}
    return {"key": key}


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Translate i18n-aware HTTPException details before sending response."""
    detail = exc.detail
    if isinstance(detail, dict) and "key" in detail:
        key = detail["key"]
        params = {k: v for k, v in detail.items() if k != "key"}
        locale = get_locale_from_request(request)
        detail = t(key, locale, **params)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
    )
