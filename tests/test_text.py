from parser.text import normalize_club, normalize_person_name


def test_person_name_diacritic_caps():
    assert normalize_person_name("FRISCHOVÁ Tereza") == "Frischová Tereza"


def test_person_name_ascii_caps():
    assert normalize_person_name("ASDF Jan") == "Asdf Jan"


def test_person_name_keeps_hyphen_title():
    assert normalize_person_name("Novák-Dvořák Eva") == "Novák-Dvořák Eva"


def test_person_name_multiple_given_names():
    assert normalize_person_name("JELINKOVÁ Josefína Grace") == "Jelinková Josefína Grace"


def test_club_keeps_abbreviations():
    assert normalize_club("TJ TESLA BRNO z.s.") == "TJ TESLA BRNO z.s."
