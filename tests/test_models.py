from parser.formats.base import FormatParser
from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult


def test_parsed_competition_holds_results_and_figures():
    fr = FigureResult("F1", [6.0, 6.0, 6.0, 6.0, 6.0], 9.6, 0.0)
    r = ParsedResult(1, 14, "Name", "Club", "CZE", 2016, 58.0, 0.0, 0.0, [fr])
    c = ParsedCompetition("Cup", "2026-05-16", "", "L3", "2014–2019", 2014, 2019, 5,
                          [FigureDef("F1", "Ballet", 1.6)], [r])
    assert c.results[0].figure_results[0].judge_scores == [6.0] * 5
    assert c.figures[0].difficulty is None or c.figures[0].difficulty == 1.6


def test_format_parser_protocol_is_runtime_checkable():
    class Fake:
        format_id = "fake"
        level_code = "L3"

        def detect(self, first_page_text: str) -> bool:
            return False

        def parse(self, pdf_path):
            raise NotImplementedError

    assert isinstance(Fake(), FormatParser)
