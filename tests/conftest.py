import pytest
from parser.pdf_parser import ParsedPDF, FigureDef, FigureResult, AthleteResult


@pytest.fixture
def sample_parsed_pdf():
    return ParsedPDF(
        competition_name="Test Cup",
        date="01.01.2026",
        category_name="Beginner L1",
        figures=[
            FigureDef("F1", "Ballet Leg", 1.6),
            FigureDef("F2", "Kipnus", 1.4),
        ],
        results=[
            AthleteResult(
                rank=1,
                entry_number=5,
                name="Test Athlete",
                club="Test Club",
                country="CZE",
                yob=2015,
                total_score=60.56,
                penalty=0.0,
                points_behind=0.0,
                figure_results=[
                    FigureResult("F1", [6.0, 6.1, 6.2, 6.0, 6.1, 6.0, 6.0], 9.44, 0.0),
                    FigureResult("F2", [5.8, 5.9, 6.0, 5.8, 5.9, 5.8, 5.8], 8.32, 0.0),
                ],
            )
        ],
    )
