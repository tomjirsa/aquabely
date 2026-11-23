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
  --aq-accent: #5B4BD6;
  --aq-card: #FFFFFF;
  --aq-card-hover: #F5F3FF;
  --aq-shadow: rgba(15, 23, 42, 0.08);
  --aq-good-bg: #DCFCE7; --aq-good-fg: #166534;
  --aq-bad-bg: #FEE2E2; --aq-bad-fg: #991B1B;
  --aq-eq-bg: #F3F4F6; --aq-eq-fg: #4B5563;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --aq-bg: #0B1220;
    --aq-surface: #151F32;
    --aq-text: #E5EAF2;
    --aq-muted: #94A3B8;
    --aq-primary: #22D3EE;
    --aq-border: #25324A;
    --aq-accent: #8B7FF0;
    --aq-card: #151F32;
    --aq-card-hover: #1E2A44;
    --aq-shadow: rgba(0, 0, 0, 0.45);
    --aq-good-bg: #14532D; --aq-good-fg: #BBF7D0;
    --aq-bad-bg: #7F1D1D; --aq-bad-fg: #FECACA;
    --aq-eq-bg: #25324A; --aq-eq-fg: #CBD5E1;
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
.aq-tbl { display: flex; flex-direction: column; gap: 10px; padding: 4px 2px; }
.aq-tbl-head, .aq-tbl-row { display: grid; grid-template-columns: 3fr 1fr 1fr; align-items: center; padding: 0 22px; }
.aq-tbl-head { color: var(--aq-muted); font-size: 0.78rem; font-weight: 400; }
.aq-tbl-row {
  background: var(--aq-card); border-radius: 10px; padding: 18px 22px;
  box-shadow: 0 2px 10px var(--aq-shadow); color: var(--aq-text);
  transition: background 0.15s ease, box-shadow 0.15s ease;
}
.aq-tbl-row:hover { background: var(--aq-card-hover); box-shadow: 0 4px 16px var(--aq-shadow); }
.aq-tbl-name { color: var(--aq-accent); font-weight: 500; }
.aq-tbl-of { color: var(--aq-muted); }
.aq-tbl-rank { display: inline-block; min-width: 2rem; text-align: center; padding: 2px 10px; border-radius: 6px; }
.aq-tbl-good { background: var(--aq-good-bg); color: var(--aq-good-fg); }
.aq-tbl-bad { background: var(--aq-bad-bg); color: var(--aq-bad-fg); }
.aq-tbl-eq { background: var(--aq-eq-bg); color: var(--aq-eq-fg); }
.aq-stat-value { color: var(--aq-primary); font-size: 1.6rem; font-weight: 600; }
.aq-fig-wrap { overflow-x: auto; border: 1px solid var(--aq-border); border-radius: 10px; }
.aq-fig-table { width: 100%; border-collapse: collapse; font-size: 14px; min-width: 620px; font-variant-numeric: tabular-nums; }
.aq-fig-table th { background: var(--aq-surface); color: var(--aq-muted); font-weight: 500; padding: 12px 14px; text-align: right; }
.aq-fig-table td { border-top: 1px solid var(--aq-border); padding: 12px 14px; text-align: right; }
.aq-fig-table th:first-child, .aq-fig-table td:first-child { text-align: left; }
.aq-fig-table td:first-child { font-weight: 500; }
.aq-fig-table s { color: var(--aq-muted); }
.aq-fig-table tfoot td { font-weight: 600; background: var(--aq-surface); }
.aq-fig-table .aq-fig-score { color: var(--aq-primary); font-weight: 600; }
.aq-fig-table .aq-left { text-align: left; }
.aq-fig-table .aq-athlete { font-weight: 500; vertical-align: top; }
.aq-rank { display: inline-flex; align-items: stretch; }
.aq-rank-pos { display: inline-block; min-width: 2rem; text-align: center; padding: 2px 8px; border-radius: 6px; font-weight: 500; }
.aq-rank-pos.aq-rank-split { border-radius: 6px 0 0 6px; }
.aq-rank-orig { display: inline-block; min-width: 2rem; text-align: center; padding: 2px 8px; border-radius: 0 6px 6px 0; background: var(--aq-surface); color: var(--aq-muted); font-weight: 500; }
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
