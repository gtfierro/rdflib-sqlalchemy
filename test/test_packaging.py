import re

from rdflib_sqlalchemy import importlib_metadata


def test_no_development_tools_in_runtime_requirements():
    """0.6.2 required flake8, tox, pytest and setuptools, which then got installed along with the package."""
    requirements = importlib_metadata.requires("brickschema_rdflib_sqlalchemy")
    runtime = {
        re.split(r"[^A-Za-z0-9_.-]", requirement, maxsplit=1)[0].lower()
        for requirement in requirements
        if "extra ==" not in requirement
    }
    assert runtime <= {"alembic", "rdflib", "six", "sqlalchemy", "importlib-metadata"}
