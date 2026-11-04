import shutil
import sys
from dataclasses import dataclass


@dataclass
class LanguageConfig:
    id: int
    name: str
    extension: str
    needs_compilation: bool
    compiler: str | None
    runtime: str
    compile_args: tuple[str, ...]
    run_args: tuple[str, ...]


LANGUAGES = {
    "cpp": LanguageConfig(
        id=1,
        name="C++",
        extension=".cpp",
        needs_compilation=True,
        compiler="g++",
        runtime="",
        compile_args=("{source}", "-o", "{output}"),
        run_args=("{output}",)
    ),

    "python": LanguageConfig(
        id=2,
        name="Python",
        extension=".py",
        needs_compilation=False,
        compiler=None,
        runtime=sys.executable,
        compile_args=(),
        run_args=("{source}",)
    )
}


def get_language(language: str) -> LanguageConfig:
    config = LANGUAGES.get(language.lower())

    if config is None:
        raise ValueError(f"Unsupported language: {language}")

    return config


def get_all_languages():
    return LANGUAGES.items()


def check_language_availability(language: str) -> dict:
    config = get_language(language)

    if config.needs_compilation:
        available = shutil.which(config.compiler) is not None
    else:
        available = shutil.which(config.runtime) is not None

    return {
        "id": config.id,
        "name": config.name,
        "available": available,
        "needs_compilation": config.needs_compilation
    }