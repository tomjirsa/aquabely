import pytest
from parser.registry import detect_format, get_parser, UnknownFormatError, AmbiguousFormatError


def test_l3_header_is_detected():
    assert detect_format("Delfinek cup\nBeginner L3 FIG (2019-2014)").format_id == "l3"


def test_unknown_header_raises():
    with pytest.raises(UnknownFormatError):
        detect_format("Some other federation document")


def test_get_parser_by_id_for_override():
    assert get_parser("l3").level_code == "L3"


def test_ambiguous_header_raises(monkeypatch):
    import parser.registry as reg
    class Always:
        format_id = "x"; level_code = "X"
        def detect(self, t): return True
        def parse(self, p): raise NotImplementedError
    monkeypatch.setattr(reg, "PARSERS", [Always(), Always()])
    with pytest.raises(AmbiguousFormatError):
        reg.detect_format("anything")
