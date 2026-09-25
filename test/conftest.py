import os

import pytest
from rdflib import Literal, URIRef, plugin
from rdflib.store import Store

from rdflib_sqlalchemy import registerplugins


registerplugins()

STORE_ID = URIRef("test")

# Same defaults as test_sqlalchemy_postgresql.py and test_sqlalchemy_mysql.py
DEFAULT_URLS = {
    "pgsql": "postgresql+psycopg2://postgres@localhost/test",
    "mysql": "mysql+pymysql://root@127.0.0.1:3306/test?charset=utf8mb4",
}


def _drop_tables(url):
    store = plugin.get("SQLAlchemy", Store)(identifier=STORE_ID)
    store.open(Literal(url), create=True)
    store.metadata.drop_all(store.engine)
    store.close()


@pytest.fixture
def db_url(tmp_path):
    """
    Database URL for store tests: the server selected by $DB (pgsql or mysql, at $DBURI),
    otherwise a fresh SQLite file.
    """
    db = os.environ.get("DB")
    if db in DEFAULT_URLS:
        url = os.environ.get("DBURI", DEFAULT_URLS[db])
        _drop_tables(url)
        yield Literal(url)
        _drop_tables(url)
    else:
        yield Literal("sqlite:///%s" % (tmp_path / "test.db"))


@pytest.fixture
def open_store(db_url):
    """Factory that opens a store on `db_url`; every store it opens is closed after the test."""
    stores = []

    def open_store(create=True):
        store = plugin.get("SQLAlchemy", Store)(identifier=STORE_ID)
        store.open(db_url, create=create)
        stores.append(store)
        return store

    yield open_store
    for store in stores:
        store.close()


@pytest.fixture
def store(open_store):
    return open_store()
