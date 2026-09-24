import pytest
from rdflib import ConjunctiveGraph, Literal, URIRef, plugin
from rdflib.store import Store

from rdflib_sqlalchemy import registerplugins


registerplugins()

graph_id = URIRef("http://example.org/g")
triples = [
    (URIRef("http://example.org/s%d" % i), URIRef("http://example.org/p"), Literal(i))
    for i in range(5)
]


@pytest.fixture
def store(tmp_path):
    store = plugin.get("SQLAlchemy", Store)(identifier=URIRef("test"))
    store.open(Literal("sqlite:///%s" % (tmp_path / "test.db")), create=True)
    yield store
    store.close()


def test_rollback_on_exception(store):
    graph = ConjunctiveGraph(store).get_context(graph_id)
    with pytest.raises(RuntimeError):
        with store.transaction():
            for t in triples:
                graph.add(t)
            store.bind("ex", URIRef("http://example.org/"))
            # reads inside the block see the pending rows
            assert len(graph) == len(triples)
            assert set(graph.triples((None, None, None))) == set(triples)
            raise RuntimeError("abort")

    assert len(graph) == 0
    assert store.namespace("ex") is None


def test_commit(store):
    graph = ConjunctiveGraph(store).get_context(graph_id)
    with store.transaction():
        for t in triples:
            graph.add(t)
        graph.remove(triples[0])
    assert set(graph.triples((None, None, None))) == set(triples[1:])


def test_nested_reuses_outer_transaction(store):
    graph = ConjunctiveGraph(store).get_context(graph_id)
    with pytest.raises(RuntimeError):
        with store.transaction() as outer:
            with store.transaction() as inner:
                assert inner is outer
                graph.add(triples[0])
            # leaving the inner block must not commit
            raise RuntimeError("abort")
    assert len(graph) == 0
