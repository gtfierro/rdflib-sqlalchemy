import pytest
from rdflib import BNode, ConjunctiveGraph, Literal, URIRef, plugin
from rdflib.namespace import RDF, XSD
from rdflib.store import Store

from rdflib_sqlalchemy import registerplugins


registerplugins()

ex = "http://example.org/"
s = URIRef(ex + "s")
p = URIRef(ex + "p")
g = URIRef(ex + "g")
triples = [
    (s, p, Literal("5")),
    (s, p, Literal("5", lang="en")),
    (s, p, Literal("5", datatype=XSD.integer)),
    (s, p, URIRef("5")),
    (s, p, Literal(ex + "o")),
    (s, p, URIRef(ex + "o")),
    (s, RDF.type, URIRef(ex + "Class")),
    (BNode("b"), p, BNode("c")),
]


@pytest.fixture
def graph(tmp_path):
    store = plugin.get("SQLAlchemy", Store)(identifier=URIRef("test"))
    store.open(Literal("sqlite:///%s" % (tmp_path / "test.db")), create=True)
    graph = ConjunctiveGraph(store).get_context(g)
    for t in triples:
        graph.add(t)
    yield graph
    store.close()


@pytest.mark.parametrize("removed", triples)
def test_remove_is_exact(graph, removed):
    graph.remove(removed)
    assert set(graph) == set(triples) - {removed}


@pytest.mark.parametrize("removed", triples)
def test_removeN_is_exact(graph, removed):
    graph.store.removeN([removed + (graph,)])
    assert set(graph) == set(triples) - {removed}


def test_removeN_batch(graph):
    removed = triples[::2]
    graph.store.removeN([t + (graph,) for t in removed])
    assert set(graph) == set(triples) - set(removed)


def test_removeN_wildcard_falls_back_to_remove(graph):
    graph.store.removeN([(s, p, None, graph), (s, RDF.type, URIRef(ex + "Class"), graph)])
    assert set(graph) == {(BNode("b"), p, BNode("c"))}


def test_removeN_rolls_back_with_transaction(graph):
    with pytest.raises(RuntimeError):
        with graph.store.transaction():
            graph.store.removeN([t + (graph,) for t in triples])
            assert len(graph) == 0
            raise RuntimeError("abort")
    assert set(graph) == set(triples)


@pytest.mark.parametrize("pattern", triples)
def test_triples_is_exact(graph, pattern):
    assert set(graph.triples(pattern)) == {pattern}


@pytest.mark.parametrize("pattern", triples)
def test_contexts_is_exact(graph, pattern):
    graph.store.remove(pattern, graph)
    assert list(graph.store.contexts(pattern)) == []
