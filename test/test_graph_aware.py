import pytest
from rdflib import ConjunctiveGraph, Dataset, Literal, URIRef, plugin
from rdflib.store import Store

from rdflib_sqlalchemy import registerplugins


registerplugins()

g1 = URIRef("http://example.org/g1")
g2 = URIRef("http://example.org/g2")
triple = (URIRef("http://example.org/s"), URIRef("http://example.org/p"), Literal("o"))


@pytest.fixture
def db_url(tmp_path):
    return Literal("sqlite:///%s" % (tmp_path / "test.db"))


def open_store(db_url, create=True):
    store = plugin.get("SQLAlchemy", Store)(identifier=URIRef("test"))
    store.open(db_url, create=create)
    return store


def test_empty_graph_is_listed(db_url):
    ds = Dataset(open_store(db_url))
    ds.graph(g1)
    assert g1 in {g.identifier for g in ds.contexts()}


def test_clearing_a_graph_keeps_it_listed(db_url):
    ds = Dataset(open_store(db_url))
    ds.graph(g1).add(triple)
    ds.graph(g1).remove((None, None, None))
    assert len(ds.graph(g1)) == 0
    assert g1 in {g.identifier for g in ds.contexts()}


def test_remove_graph(db_url):
    ds = Dataset(open_store(db_url))
    ds.graph(g1).add(triple)
    ds.graph(g2).add(triple)
    ds.remove_graph(g1)
    identifiers = {g.identifier for g in ds.contexts()}
    assert g1 not in identifiers
    assert g2 in identifiers
    assert len(ds.get_context(g1)) == 0
    assert len(ds.get_context(g2)) == 1


def test_graphs_persist_across_reopen(db_url):
    store = open_store(db_url)
    Dataset(store).graph(g1)
    store.close()
    ds = Dataset(open_store(db_url, create=False))
    assert g1 in {g.identifier for g in ds.contexts()}


def test_opens_store_created_before_graphs_table(db_url):
    store = open_store(db_url)
    ConjunctiveGraph(store).get_context(g1).add(triple)
    store.tables["graphs"].drop(store.engine)
    store.close()

    store = open_store(db_url, create=False)
    assert list(store.contexts()) == [g1]
    Dataset(store).graph(g2)
    assert set(store.contexts()) == {g1, g2}
