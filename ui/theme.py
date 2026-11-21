import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

THEME_CSS = """
<style>
:root {
  --aq-bg: #FFFFFF;
  --aq-surface: #F3F6FA;
  --aq-text: #0F172A;
  --aq-muted: #64748B;
  --aq-primary: #0E7490;
  --aq-border: #E2E8F0;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --aq-bg: #0B1220;
    --aq-surface: #151F32;
    --aq-text: #E5EAF2;
    --aq-muted: #94A3B8;
    --aq-primary: #22D3EE;
    --aq-border: #25324A;
  }
}
body {
  background: var(--aq-bg);
  color: var(--aq-text);
}
.aq-stat-card {
  background: var(--aq-surface);
  border: 1px solid var(--aq-border);
  border-radius: 8px;
  padding: 12px 16px;
}
.aq-stat-label { color: var(--aq-muted); font-size: 0.8rem; }
.aq-stat-value { color: var(--aq-primary); font-size: 1.6rem; font-weight: 600; }
</style>
"""

PALETTE = ["#0E7490", "#F59E0B", "#10B981", "#6366F1", "#EF4444", "#64748B"]


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def plotly_layout(fig):
    template = pio.templates["plotly_white"]
    fig.update_layout(template=template, colorway=PALETTE,
                      margin=dict(l=40, r=20, t=40, b=40))
    return fig
