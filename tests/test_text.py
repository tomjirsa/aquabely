from parser.text import normalize_club, normalize_person_name


def test_person_name_diacritic_caps():
    assert normalize_person_name("FRISCHOVÁ Tereza") == "Frischová Tereza"


def test_person_name_ascii_caps():
    assert normalize_person_name("ASDF Jan") == "Asdf Jan"


def test_person_name_keeps_hyphen_title():
    assert normalize_person_name("Novák-Dvořák Eva") == "Novák-Dvořák Eva"


def test_person_name_multiple_given_names():
    assert normalize_person_name("JELINKOVÁ Josefína Grace") == "Jelinková Josefína Grace"


def test_club_capitalises_long_caps_keeps_abbreviations():
    assert normalize_club("TJ TESLA BRNO z.s.") == "TJ Tesla Brno z.s."


def test_club_capitalises_long_caps_mixed():
    assert normalize_club("Sportovní Klub policie KOMETA BRNO z.s.") == "Sportovní Klub Policie Kometa Brno z.s."


def test_club_keeps_three_letter_caps():
    assert normalize_club("VSK Univerzita Brno") == "VSK Univerzita Brno"


def test_club_keeps_short_caps_with_diacritics():
    assert normalize_club("Plavecký klub Slávia VŠ Plzeň z.s.") == "Plavecký Klub Slávia VŠ Plzeň z.s."


def test_club_keeps_short_caps_ascii():
    assert normalize_club("SK Brno") == "SK Brno"


def test_club_capitalizes_lowercase_words():
    assert normalize_club("Spolek pro akvabely, z.s.") == "Spolek Pro Akvabely, z.s."
