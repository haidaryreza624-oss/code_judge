from fastapi import APIRouter

from app.services.language_manager import (
    get_all_languages,
    check_language_availability
)

router = APIRouter(
    prefix="/api/v1/languages",
    tags=["Languages"]
)


@router.get("/")
def list_languages():
    languages = []

    for language_key, config in get_all_languages():
        result = check_language_availability(language_key)
        languages.append(result)

    return {
        "languages": languages
    }