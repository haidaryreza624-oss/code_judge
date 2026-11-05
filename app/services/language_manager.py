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
    ),

    "java": LanguageConfig(
        id=3,
        name="Java",
        extension=".java",
        needs_compilation=True,
        compiler="javac",
        runtime="java",
        compile_args=(
            "-encoding", "UTF-8",
            "-d", "{build_dir}",
            "{source}"
        ),
        run_args=(
            "-cp", "{build_dir}",
            "{class_name}"
        )
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

    compiler_available = (
        shutil.which(config.compiler) is not None
        if config.compiler else True
    )

    runtime_available = (
        shutil.which(config.runtime) is not None
        if config.runtime else True
    )

    return {
        "id": config.id,
        "name": config.name,
        "available": compiler_available and runtime_available,
        "needs_compilation": config.needs_compilation
    }