"""Peças visuais do app: CSS, cabeçalho, cards e estilo dos gráficos."""

from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

COLOR_HAVE = "#2a78d6"   # azul: skill que você tem / demanda do mercado
COLOR_GAP = "#eb6834"    # laranja: skill que falta
REPO_URL = "https://github.com/guinho0/hunter"

_CSS = """
<style>
/* Mais respiro no topo e largura confortável */
.block-container { padding-top: 4.2rem; padding-bottom: 3rem; max-width: 1280px; }

/* ---------- Cabeçalho */
.hx-hero { padding: 1.6rem 1.8rem; border-radius: 1rem; margin-bottom: 1.2rem;
  background: linear-gradient(135deg, rgba(42,120,214,.14) 0%, rgba(235,104,52,.10) 100%);
  border: 1px solid rgba(128,128,128,.18); }
.hx-hero h1 { margin: 0; padding: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -.02em; }
.hx-hero h1 span { background: linear-gradient(90deg, #2a78d6, #eb6834);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.hx-hero p { margin: .35rem 0 1rem; opacity: .8; font-size: 1.02rem; }
.hx-steps { display: flex; flex-wrap: wrap; gap: .5rem; }
.hx-step { display: inline-flex; align-items: center; gap: .45rem; padding: .3rem .75rem;
  border-radius: 999px; font-size: .85rem; font-weight: 500;
  border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.06); }
.hx-step b { display: inline-grid; place-items: center; width: 1.25rem; height: 1.25rem;
  border-radius: 50%; font-size: .72rem; background: rgba(128,128,128,.22); }
.hx-step.done { border-color: rgba(42,120,214,.55); background: rgba(42,120,214,.12); }
.hx-step.done b { background: #2a78d6; color: #fff; }

/* ---------- Cards de "como funciona" */
.hx-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: .9rem; margin: .4rem 0 1rem; }
.hx-card { padding: 1.1rem 1.2rem; border-radius: .9rem;
  border: 1px solid rgba(128,128,128,.2); background: rgba(128,128,128,.04); }
.hx-card .ic { font-size: 1.6rem; }
.hx-card h4 { margin: .4rem 0 .3rem; padding: 0; font-size: 1rem; font-weight: 700; }
.hx-card p { margin: 0; font-size: .88rem; opacity: .78; line-height: 1.45; }

/* ---------- Chips de skills */
.hx-chips { display: flex; flex-wrap: wrap; gap: .4rem; margin: .3rem 0 .8rem; }
.hx-chip { padding: .22rem .65rem; border-radius: 999px; font-size: .82rem; font-weight: 500;
  border: 1px solid rgba(42,120,214,.4); background: rgba(42,120,214,.1); }
.hx-chip.gap { border-color: rgba(235,104,52,.45); background: rgba(235,104,52,.1); }

/* ---------- Métricas e abas */
[data-testid="stMetricValue"] { font-weight: 700; }
.stTabs [data-baseweb="tab-list"] { gap: .3rem; }
.stTabs [data-baseweb="tab"] { padding: .55rem 1rem; font-weight: 600; }

/* ---------- Rodapé */
.hx-footer { margin-top: 2.5rem; padding-top: 1rem; text-align: center; font-size: .85rem;
  opacity: .65; border-top: 1px solid rgba(128,128,128,.2); }
.hx-footer a { color: inherit; font-weight: 600; }
</style>
"""


def inject_css() -> None:
    st.html(_CSS)


def hero(steps: list[tuple[str, bool]]) -> None:
    """Cabeçalho com título e as etapas do fluxo (marcadas quando concluídas)."""
    chips = "".join(
        f'<span class="hx-step{" done" if done else ""}"><b>{"✓" if done else i}</b>'
        f"{html.escape(label)}</span>"
        for i, (label, done) in enumerate(steps, 1))
    st.html(f"""
    <div class="hx-hero">
      <h1>🎯 <span>Hunter</span></h1>
      <p>Descubra quais skills o mercado pede no LinkedIn para a sua carreira
         e quanto o seu perfil está aderente a ele.</p>
      <div class="hx-steps">{chips}</div>
    </div>""")


def cards(items: list[tuple[str, str, str]]) -> None:
    """Grade de cards (ícone, título, texto)."""
    body = "".join(
        f'<div class="hx-card"><div class="ic">{icon}</div><h4>{html.escape(title)}</h4>'
        f"<p>{html.escape(text)}</p></div>" for icon, title, text in items)
    st.html(f'<div class="hx-cards">{body}</div>')


def chips(values: list[str], gap: bool = False) -> None:
    if not values:
        st.caption("—")
        return
    cls = "hx-chip gap" if gap else "hx-chip"
    st.html('<div class="hx-chips">' + "".join(
        f'<span class="{cls}">{html.escape(v)}</span>' for v in values) + "</div>")


def footer() -> None:
    st.html(f"""
    <div class="hx-footer">
      Hunter é open source · <a href="{REPO_URL}" target="_blank">código no GitHub</a>
      · dados de vagas públicas do LinkedIn, coletadas localmente no seu computador
    </div>""")


def style_fig(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Visual único para todos os gráficos: fundo transparente, grade discreta."""
    fig.update_layout(
        template="plotly_white" if st.context.theme.type != "dark" else "plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13),
        hoverlabel=dict(font_family="Inter, sans-serif"),
        bargap=0.3, yaxis_title=None,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,.15)", zeroline=False)
    fig.update_yaxes(showgrid=False)
    fig.update_traces(selector=dict(type="bar"), marker_line_width=0)
    if height:
        fig.update_layout(height=height)
    return fig


def gauge(value: float, title: str) -> go.Figure:
    color = COLOR_HAVE if value >= 50 else COLOR_GAP
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number=dict(suffix="%", valueformat=".0f", font=dict(size=38)),
        title=dict(text=title, font=dict(size=15)),
        gauge=dict(
            axis=dict(range=[0, 100], ticksuffix="%", tickwidth=0),
            bar=dict(color=color, thickness=0.75),
            bgcolor="rgba(128,128,128,.12)", borderwidth=0,
            steps=[dict(range=[0, 100], color="rgba(128,128,128,.06)")],
        )))
    fig.update_layout(height=260, margin=dict(l=40, r=40, t=60, b=20))
    return style_fig(fig)
