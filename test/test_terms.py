from rdflib import BNode, Literal, URIRef
from rdflib.namespace import XSD

from rdflib_sqlalchemy.termutils import create_term


def test_literals_round_trip_and_are_cached():
    cases = [
        ("hello", None, None),
        ("hello", "en", None),
        ("5", None, str(XSD.integer)),
    ]
    for value, lang, datatype in cases:
        term = create_term(value, "L", None, lang, datatype)
        assert term == Literal(value, lang=lang, datatype=datatype)
        assert create_term(value, "L", None, lang, datatype) is term


def test_other_terms():
    assert create_term("http://example.org/a", "U", None) == URIRef("http://example.org/a")
    assert create_term("b0", "B", None) == BNode("b0")
