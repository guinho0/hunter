"""Peças visuais do app: CSS, cabeçalho, cards e estilo dos gráficos."""

from __future__ import annotations

import base64
import html

import plotly.graph_objects as go
import streamlit as st

COLOR_HAVE = "#2a78d6"   # azul: skill que você tem / demanda do mercado
COLOR_GAP = "#eb6834"    # laranja: skill que falta
REPO_URL = "https://github.com/guinho0/hunter"

# Marca: alvo minimalista em SVG. O st.html remove <svg> embutido, então vira <img> em data URI.
_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24"
  fill="none" stroke="#2a78d6"
  stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/>
  <circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1" fill="#2a78d6" stroke="none"/>
  <path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3"/></svg>"""

_GITHUB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"
  fill="#8b8f98">
  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
  0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01
  1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95
  0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09
  2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65
  3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>"""


def _img(svg: str, size: int) -> str:
    data = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{data}" width="{size}" height="{size}" alt="">'


LOGO, GITHUB = _img(_LOGO_SVG, 26), _img(_GITHUB_SVG, 16)

_CSS = """
<style>
.block-container { padding-top: 3.4rem; padding-bottom: 3rem; max-width: 1240px; }

/* Aviso do Streamlit para desenvolvedores, sem sentido para quem usa o app */
.stSkillsNudge { display: none !important; }

/* Sem o ícone de link que o Streamlit põe ao lado dos títulos */
[data-testid="stHeaderActionElements"] { display: none; }
h1, h2, h3, h4 { letter-spacing: -.01em; }

/* ---------- Barra de topo */
.hx-top { display: flex; align-items: center; justify-content: space-between;
  padding-bottom: .9rem; border-bottom: 1px solid rgba(128,128,128,.2); }
.hx-brand { display: flex; align-items: center; gap: .55rem; font-weight: 700; font-size: 1.15rem;
  letter-spacing: -.01em; }
.hx-top a { display: inline-flex; align-items: center; gap: .4rem; font-size: .85rem; font-weight: 500;
  color: inherit; text-decoration: none; padding: .35rem .75rem; border-radius: .5rem;
  border: 1px solid rgba(128,128,128,.25); }
.hx-top a:hover { border-color: rgba(128,128,128,.5); }

/* ---------- Título da página */
.hx-intro { padding: 1.8rem 0 1.4rem; }
.hx-intro h1 { margin: 0; padding: 0; font-size: 2rem; font-weight: 700; line-height: 1.2; }
.hx-intro p { margin: .5rem 0 0; max-width: 46rem; opacity: .7; font-size: 1rem; line-height: 1.5; }

/* ---------- Etapas */
.hx-steps { display: flex; gap: 0; margin: 0 0 .6rem !important; padding: 0 !important;
  list-style: none; flex-wrap: wrap; }
.hx-steps li { margin-left: 0 !important; display: flex; align-items: center; gap: .5rem; font-size: .85rem; opacity: .55;
  padding-right: 1.1rem; margin-right: 1.1rem; border-right: 1px solid rgba(128,128,128,.25); }
.hx-steps li:last-child { border-right: 0; }
.hx-steps li span { display: inline-grid; place-items: center; width: 1.35rem; height: 1.35rem;
  border-radius: 50%; font-size: .72rem; font-weight: 600; border: 1px solid currentColor; }
.hx-steps li.done { opacity: 1; }
.hx-steps li.done span { background: #2a78d6; border-color: #2a78d6; color: #fff; }

/* ---------- Rótulo de seção (sidebar) */
.hx-label { font-size: .72rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
  opacity: .55; margin: .2rem 0 -.2rem; }

/* ---------- Cards de "como funciona" */
.hx-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 1px; margin: .6rem 0 1.4rem; border: 1px solid rgba(128,128,128,.2); border-radius: .75rem;
  overflow: hidden; background: rgba(128,128,128,.2); }
.hx-card { padding: 1.3rem 1.3rem 1.4rem; background: var(--hx-bg, #fff); }
.hx-card .n { font-size: .8rem; font-weight: 600; color: #2a78d6; font-variant-numeric: tabular-nums; }
.hx-card h4 { margin: .5rem 0 .35rem; padding: 0; font-size: 1rem; font-weight: 600; }
.hx-card p { margin: 0; font-size: .88rem; opacity: .7; line-height: 1.5; }

/* ---------- Chips de skills */
.hx-chips { display: flex; flex-wrap: wrap; gap: .4rem; margin: .3rem 0 .8rem; }
.hx-chip { padding: .2rem .6rem; border-radius: .4rem; font-size: .82rem; font-weight: 500;
  border: 1px solid rgba(42,120,214,.35); background: rgba(42,120,214,.08); }
.hx-chip.gap { border-color: rgba(235,104,52,.4); background: rgba(235,104,52,.08); }

/* ---------- Métricas e abas */
[data-testid="stMetricValue"] { font-weight: 600; }
[data-testid="stMetricLabel"] { opacity: .75; }
.stTabs [data-baseweb="tab-list"] { gap: 1.4rem; }
.stTabs [data-baseweb="tab"] { padding: .6rem 0; font-weight: 500; }

/* ---------- Rodapé */
.hx-footer { margin-top: 3rem; padding-top: 1.1rem; display: flex; justify-content: space-between;
  flex-wrap: wrap; gap: .5rem; font-size: .82rem; opacity: .6; border-top: 1px solid rgba(128,128,128,.2); }
.hx-footer a { color: inherit; }
</style>
"""


def inject_css() -> None:
    # Fundo dos cards acompanha o tema (claro/escuro) do Streamlit.
    bg = st.context.theme.type == "dark" and "#0e1117" or "#ffffff"
    st.html(_CSS.replace("var(--hx-bg, #fff)", bg))


def hero(steps: list[tuple[str, bool]]) -> None:
    """Barra de topo, título da página e etapas do fluxo (marcadas quando concluídas)."""
    items = "".join(
        f'<li class="{"done" if done else ""}"><span>{"&#10003;" if done else i}</span>'
        f"{html.escape(label)}</li>"
        for i, (label, done) in enumerate(steps, 1))
    st.html(f"""
    <div class="hx-top">
      <div class="hx-brand">{LOGO}Hunter</div>
      <a href="{REPO_URL}" target="_blank" rel="noopener">{GITHUB}GitHub</a>
    </div>
    <div class="hx-intro">
      <h1>O que o mercado pede para a sua carreira</h1>
      <p>Lê as vagas públicas do LinkedIn, mede quais skills aparecem com mais frequência
         e compara com o seu perfil.</p>
    </div>
    <ol class="hx-steps">{items}</ol>""")


def label(text: str) -> None:
    st.html(f'<div class="hx-label">{html.escape(text)}</div>')


def cards(items: list[tuple[str, str]]) -> None:
    """Grade de cards numerados (título, texto)."""
    body = "".join(
        f'<div class="hx-card"><div class="n">{i:02d}</div><h4>{html.escape(title)}</h4>'
        f"<p>{html.escape(text)}</p></div>" for i, (title, text) in enumerate(items, 1))
    st.html(f'<div class="hx-cards">{body}</div>')


def chips(values: list[str], gap: bool = False) -> None:
    if not values:
        st.caption("Nenhuma.")
        return
    cls = "hx-chip gap" if gap else "hx-chip"
    st.html('<div class="hx-chips">' + "".join(
        f'<span class="{cls}">{html.escape(v)}</span>' for v in values) + "</div>")


def footer() -> None:
    st.html(f"""
    <div class="hx-footer">
      <span>Hunter · código aberto sob licença MIT</span>
      <span>Os dados ficam no seu computador · <a href="{REPO_URL}" target="_blank">GitHub</a></span>
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
