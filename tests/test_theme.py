from ui.theme import THEME_CSS, plotly_layout
import plotly.graph_objects as go


def test_theme_defines_tokens_and_dark_mode():
    assert ":root" in THEME_CSS
    assert "prefers-color-scheme: dark" in THEME_CSS


def test_plotly_layout_sets_template():
    fig = plotly_layout(go.Figure())
    assert fig.layout.template is not None
