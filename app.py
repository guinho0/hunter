"""Hunter: skills mais pedidas no LinkedIn para uma carreira e aderência do seu perfil.

Rodar:  streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from hunter import analysis, keywords as kw, locations as loc, profile as prof, ui
from hunter.linkedin_jobs import EXPERIENCE_LEVELS, Job, collect_jobs
from hunter.taxonomy import SKILLS, add_custom_skills
from hunter.ui import COLOR_GAP, COLOR_HAVE

SEARCHES_DIR = Path(__file__).parent / ".cache" / "searches"
PCT = st.column_config.ProgressColumn("% das vagas", format="%.0f%%", min_value=0, max_value=100)


def saved_label(path: Path) -> str:
    """'2026-10-13_1248_engenheiro-de-dados' → '13/10 12:48 · engenheiro de dados'."""
    parts = path.stem.split("_", 2)
    if len(parts) < 3:
        return path.stem
    date, time, slug = parts
    return f"{date[8:10]}/{date[5:7]} {time[:2]}:{time[2:]} · {slug.replace('-', ' ')}"


st.set_page_config(page_title="Hunter · Skills do mercado", page_icon="🎯", layout="wide",
                   menu_items={"About": f"Hunter · {ui.REPO_URL}",
                               "Report a bug": f"{ui.REPO_URL}/issues"})
ui.inject_css()
header = st.empty()   # preenchido no fim, quando já se sabe quais etapas foram concluídas

# ---------------------------------------------------------------- Sidebar: busca
with st.sidebar:
    st.markdown("### 🔎 Qual carreira?")
    keywords = st.text_input("Cargo", "Engenheiro de dados")
    places = st.multiselect(
        "Localidade", loc.SUGGESTIONS, [loc.BRAZIL], accept_new_options=True,
        placeholder="Cidade, estado, sigla ou região…",
        help="Combine quantas quiser: regiões (Sudeste), estados (ES ou Espírito Santo), "
             "cidades (Vitória, ES) ou qualquer lugar que o LinkedIn conheça. Digite e tecle Enter "
             "para usar algo fora da lista. Regiões são buscadas estado por estado.")
    include_remote = st.checkbox("Incluir vagas remotas de todo o Brasil",
                                 help="Útil quando você escolhe uma cidade ou estado e também aceita "
                                      "trabalhar remoto para empresas de outros lugares.")
    levels = st.multiselect("Nível de experiência", list(EXPERIENCE_LEVELS), ["Júnior (entry level)"])
    with st.expander("⚙️ Opções avançadas"):
        max_jobs = st.slider("Quantidade de vagas", 10, 200, 50, step=10,
                             help="Dividida entre as localidades (mínimo 10 por localidade). Cada vaga "
                                  "leva ~2s na primeira vez; depois fica em cache.")
        last_days = st.selectbox("Publicadas nos últimos", [None, 1, 7, 30],
                                 format_func=lambda d: "qualquer data" if d is None else f"{d} dia(s)",
                                 index=3)
        custom = st.text_input("Skills extras para rastrear", placeholder="ex.: Kedro, Metabase",
                               help="Separadas por vírgula. Passam a ser contadas nas vagas e no perfil.")
    add_custom_skills(custom.split(","))
    run = st.button("Buscar vagas", type="primary", icon="🚀", width="stretch")

    saved = sorted(SEARCHES_DIR.glob("*.json"), reverse=True) if SEARCHES_DIR.exists() else []
    if saved:
        st.divider()
        st.markdown("### 🗂️ Buscas anteriores")
        pick = st.selectbox("Carregar busca salva", [None] + saved, label_visibility="collapsed",
                            format_func=lambda p: "Escolha uma busca salva…" if p is None
                            else saved_label(p))
        if pick and st.button("Carregar", width="stretch"):
            data = json.loads(pick.read_text(encoding="utf-8"))
            st.session_state["jobs"] = [Job(**j) for j in data["jobs"]]
            st.session_state["query"] = data["query"]

if run:
    bar = st.progress(0.0, "Buscando vagas no LinkedIn…")
    jobs, searched, missing = collect_jobs(
        keywords, places, [EXPERIENCE_LEVELS[l] for l in levels], max_jobs, last_days,
        include_remote,
        progress=lambda i, n, j: bar.progress(i / n, f"Lendo vaga {i}/{n}: {j.title[:60]}"),
    )
    bar.empty()
    if missing:
        st.warning(f"O LinkedIn não reconheceu: {', '.join(missing)}. "
                   "Tente outro nome ou o formato 'Cidade, UF'.")
    query = f"{keywords} · {', '.join(searched)} · {', '.join(levels) or 'todos os níveis'}"
    st.session_state["jobs"], st.session_state["query"] = jobs, query
    if jobs:
        SEARCHES_DIR.mkdir(parents=True, exist_ok=True)
        stamp = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M")
        slug = "".join(c if c.isalnum() else "-" for c in keywords.lower())
        (SEARCHES_DIR / f"{stamp}_{slug}.json").write_text(
            json.dumps({"query": query, "jobs": [j.__dict__ for j in jobs]}, ensure_ascii=False),
            encoding="utf-8")

jobs: list[Job] = st.session_state.get("jobs", [])

tab_market, tab_kw, tab_profile, tab_fit = st.tabs(
    ["📊 Mercado", "🔑 Palavras-chave", "👤 Meu perfil", "✅ Aderência"])

# ---------------------------------------------------------------- Mercado
with tab_market:
    if not jobs:
        st.markdown("#### Como funciona")
        ui.cards([
            ("📊", "1 · Mapeie o mercado", "Escolha cargo, localidade e nível na barra lateral. "
             "O Hunter lê as vagas públicas do LinkedIn e mede quais skills mais aparecem."),
            ("🔑", "2 · Pegue as palavras-chave", "Veja como as vagas chamam o cargo e os termos "
             "mais frequentes, para usar no seu título, no 'Sobre' e nas experiências."),
            ("👤", "3 · Envie o seu perfil", "ZIP de dados do LinkedIn, PDF do perfil ou texto livre. "
             "Tudo é processado localmente, no seu computador."),
            ("✅", "4 · Veja a sua aderência", "Quanto você cobre do que o mercado pede, o que estudar "
             "primeiro e quais vagas têm mais a ver com você."),
        ])
        st.info("👈 Configure a carreira na barra lateral e clique em **Buscar vagas** para começar.")
    else:
        jobs_df = analysis.jobs_dataframe(jobs)

        def options(col: str, within: pd.DataFrame) -> list[str]:
            return within[col].value_counts().index.tolist()   # mais frequentes primeiro

        f1, f2, f3, f4 = st.columns(4)
        keep = f1.multiselect(
            "Nível (pelo título)", options("Nível (título)", jobs_df), placeholder="Todos",
            help="O filtro de nível do LinkedIn é frouxo; aqui você refina pelo título "
                 "(ex.: manter só 'Júnior' e 'Não informado').")
        regions = f2.multiselect("Região", options("Região", jobs_df), placeholder="Todas")
        in_region = jobs_df[jobs_df["Região"].isin(regions)] if regions else jobs_df
        states = f3.multiselect("Estado", options("Estado", in_region), placeholder="Todos")
        modes = f4.multiselect("Modalidade", options("Modalidade", jobs_df), placeholder="Todas",
                               help="Detectada pela menção a remoto/híbrido/presencial no título "
                                    "ou na descrição.")
        for col, chosen in [("Nível (título)", keep), ("Região", regions), ("Estado", states),
                            ("Modalidade", modes)]:
            if chosen:
                jobs_df = jobs_df[jobs_df[col].isin(chosen)]
        st.session_state["jobs_df"] = jobs_df

        if jobs_df.empty:
            st.warning("Nenhuma vaga com esse filtro.")
        else:
            ranking = analysis.skill_ranking(jobs_df)
            st.session_state["ranking"] = ranking

            st.caption("🔎 " + st.session_state.get("query", ""))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vagas analisadas", len(jobs_df), border=True)
            c2.metric("Empresas", jobs_df["Empresa"].nunique(), border=True)
            c3.metric("Skills distintas", len(ranking), border=True)
            c4.metric("Skills por vaga (mediana)", int(jobs_df["skills"].map(len).median()), border=True)

            with st.container(border=True):
                head, ctrl = st.columns([3, 1], vertical_alignment="bottom")
                head.markdown("#### 🏆 Skills mais pedidas")
                top_n = ctrl.slider("Mostrar top", 5, 50, 25)
                top = ranking.head(top_n)
                fig = px.bar(top.iloc[::-1], x="% das vagas", y="Skill", orientation="h",
                             text="% das vagas", hover_data={"Vagas": True, "Categoria": True},
                             color="% das vagas", color_continuous_scale=["#b9d3f3", COLOR_HAVE])
                fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", cliponaxis=False)
                fig.update_layout(xaxis_title="% das vagas que citam a skill", coloraxis_showscale=False,
                                  margin=dict(l=0, r=40, t=10, b=0))
                st.plotly_chart(ui.style_fig(fig, max(320, 26 * len(top))), width="stretch")

            st.markdown("#### 🧩 Por categoria")
            by_cat = ranking.groupby("Categoria")["Skill"].apply(
                lambda s: ", ".join(s.head(6))).reset_index(name="Mais pedidas")
            by_cat["% das vagas"] = ranking.groupby("Categoria")["% das vagas"].max().values
            st.dataframe(by_cat.sort_values("% das vagas", ascending=False), hide_index=True,
                         width="stretch", column_config={"% das vagas": st.column_config.ProgressColumn(
                             "Skill mais citada", format="%.0f%%", min_value=0, max_value=100)})

            with st.expander(f"Ver as {len(jobs_df)} vagas"):
                view = jobs_df.assign(skills=jobs_df["skills"].map(", ".join)).drop(columns=["job_id", "Descrição"])
                st.dataframe(view, hide_index=True, width="stretch",
                             column_config={"Link": st.column_config.LinkColumn("Link")})
            with st.expander("📍 Onde estão as vagas"):
                c1, c2 = st.columns(2)
                by_state = jobs_df["Estado"].value_counts().rename_axis("Estado").reset_index(name="Vagas")
                fig = px.bar(by_state.head(15).iloc[::-1], x="Vagas", y="Estado", orientation="h",
                             text="Vagas", color_discrete_sequence=[COLOR_HAVE])
                fig.update_traces(textposition="outside", cliponaxis=False)
                fig.update_layout(margin=dict(l=0, r=30, t=10, b=0))
                c1.plotly_chart(ui.style_fig(fig, max(220, 28 * min(15, len(by_state)))), width="stretch")
                modes_df = jobs_df["Modalidade"].value_counts().rename_axis("Modalidade").reset_index(name="Vagas")
                fig = px.pie(modes_df, names="Modalidade", values="Vagas", hole=0.6,
                             color_discrete_sequence=[COLOR_HAVE, COLOR_GAP, "#7fb0ea", "#f4a582", "#9aa4b2"])
                fig.update_traces(textinfo="percent+label", textposition="outside")
                fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
                c2.plotly_chart(ui.style_fig(fig, 300), width="stretch")

            st.download_button("Baixar ranking (CSV)", ranking.to_csv(index=False).encode("utf-8"),
                               "ranking_skills.csv", "text/csv", icon="⬇️")

# ---------------------------------------------------------------- Perfil
with tab_profile:
    st.markdown("#### 👤 Envie o seu perfil")
    st.caption("Use **uma ou mais** fontes. Os arquivos são lidos só no seu computador; nada é enviado "
               "para fora.")

    c1, c2, c3 = st.columns(3)
    with c1.container(border=True):
        st.markdown("**📦 ZIP de dados** · mais completo")
        st.caption("LinkedIn → Configurações e Privacidade → Privacidade de dados → Baixe seus dados. "
                   "Selecione Perfil, Competências, Cargos, Certificações, Cursos, Projetos, Formação "
                   "e Idiomas.")
        zip_file = st.file_uploader("ZIP de dados do LinkedIn", type="zip", label_visibility="collapsed")
    with c2.container(border=True):
        st.markdown("**📄 PDF do perfil** · mais rápido")
        st.caption("No seu perfil → Mais → Salvar como PDF.")
        pdf_file = st.file_uploader("PDF do perfil", type="pdf", label_visibility="collapsed")
    with c3.container(border=True):
        st.markdown("**✍️ Texto livre**")
        st.caption("Experiências, cursos ou certificações que não estão no LinkedIn.")
        free_text = st.text_area("Texto livre", height=110, label_visibility="collapsed")

    p = prof.Profile()
    if zip_file:
        p.merge(prof.from_linkedin_export(zip_file.getvalue()))
    if pdf_file:
        p.merge(prof.from_pdf(pdf_file.getvalue()))
    if free_text.strip():
        p.merge(prof.from_text(free_text))

    detected = sorted(p.skills)
    manual = st.multiselect("Skills detectadas (ajuste: remova o que não domina, adicione o que faltou)",
                            sorted(SKILLS), detected, key=f"manual_{'|'.join(detected)}")
    final = prof.Profile()
    for s in manual:
        final.skills[s] = p.skills.get(s) or {"Marcado manualmente"}
    final.unmapped = p.unmapped
    final.text = p.text + "\n" + "\n".join(manual)
    st.session_state["profile"] = final

    if final.skills:
        st.dataframe(pd.DataFrame(
            [{"Skill": s, "Categoria": SKILLS[s][0], "Onde aparece": ", ".join(sorted(src))}
             for s, src in sorted(final.skills.items())]), hide_index=True, width="stretch")
    if p.unmapped:
        st.caption("Competências do seu perfil fora do catálogo (use 'Skills extras' na barra lateral "
                   "para rastreá-las): " + ", ".join(sorted(p.unmapped)))

# ---------------------------------------------------------------- Aderência
with tab_fit:
    ranking = st.session_state.get("ranking")
    profile = st.session_state.get("profile")
    if ranking is None or ranking.empty:
        st.info("Primeiro busque vagas na aba **Mercado**.")
    elif profile is None or not profile.skills:
        st.info("Agora envie seu perfil na aba **Meu perfil**.")
    else:
        c1, c2 = st.columns(2)
        top_n = c1.slider("Considerar as top N skills do mercado", 5, 40, 20)
        min_pct = c2.slider("Ignorar skills citadas em menos de (% das vagas)", 0, 30, 5)
        res = analysis.fit(ranking, profile, top_n, min_pct)

        g, m = st.columns([1.3, 1], vertical_alignment="center")
        with g.container(border=True):
            st.plotly_chart(ui.gauge(res.score, "Aderência ao mercado"), width="stretch",
                            config={"displayModeBar": False})
            st.caption("Soma da demanda (% das vagas) das skills que você tem ÷ demanda total das "
                       "top N. Skills mais pedidas pesam mais.")
        with m:
            st.metric("Cobertura das top skills", f"{res.coverage:.0f}%", border=True,
                      help="Quantas das top N skills você tem, sem ponderar.")
            st.metric("Skills do top que você tem", int(res.table["Você tem?"].sum()), border=True)
            st.metric("Skills que faltam", len(res.gaps), border=True)

        chart = res.table.assign(Status=res.table["Você tem?"].map({True: "Você tem", False: "Falta"}))
        fig = px.bar(chart.iloc[::-1], x="% das vagas", y="Skill", color="Status", orientation="h",
                     color_discrete_map={"Você tem": COLOR_HAVE, "Falta": COLOR_GAP},
                     category_orders={"Status": ["Você tem", "Falta"]},
                     hover_data={"Categoria": True, "Onde aparece no seu perfil": True})
        fig.update_yaxes(categoryorder="total ascending")   # ordem de demanda, sem agrupar por cor
        fig.update_layout(xaxis_title="% das vagas que citam a skill", legend_title=None,
                          legend=dict(orientation="h", y=1.05), margin=dict(l=0, r=10, t=30, b=0))
        with st.container(border=True):
            st.markdown("#### 📈 Você × mercado")
            st.plotly_chart(ui.style_fig(fig, max(320, 26 * len(chart))), width="stretch")

        left, right = st.columns(2)
        with left.container(border=True):
            st.markdown("#### 📚 O que estudar primeiro")
            st.caption("Skills do top que faltam no seu perfil, ordenadas pela demanda.")
            if res.gaps.empty:
                st.success("Você cobre todas as top skills deste recorte! 🎉")
            else:
                ui.chips(res.gaps["Skill"].head(8).tolist(), gap=True)
                st.dataframe(res.gaps, hide_index=True, width="stretch", column_config={"% das vagas": PCT})
        with right.container(border=True):
            st.markdown("#### 💪 Seus diferenciais")
            st.caption("Skills que você tem e que não estão no top deste recorte.")
            ui.chips(res.extras)

        st.markdown("#### 🎯 Vagas com maior match com o seu perfil")
        matches = analysis.job_matches(st.session_state["jobs_df"], profile)
        st.dataframe(matches[["Título", "Empresa", "Local", "Match %", "Faltam", "Link"]].head(30),
                     hide_index=True, width="stretch",
                     column_config={"Link": st.column_config.LinkColumn("Link"),
                                    "Match %": st.column_config.ProgressColumn(
                                        "Match %", format="%.0f%%", min_value=0, max_value=100)})

# ---------------------------------------------------------------- Palavras-chave
with tab_kw:
    jobs_df = st.session_state.get("jobs_df")
    if jobs_df is None or jobs_df.empty:
        st.info("Primeiro busque vagas na aba **Mercado**.")
    else:
        descriptions = jobs_df["Descrição"].tolist()
        profile = st.session_state.get("profile")
        has_profile = bool(profile and profile.text.strip())

        # --- Títulos de cargo
        st.subheader("🏷️ Como as vagas chamam esse cargo")
        st.caption("Use os títulos mais frequentes no seu título do LinkedIn e no cargo desejado: "
                   "é por eles que recrutadores pesquisam.")
        titles = kw.title_frequency(jobs_df["Título"].tolist())
        c1, c2 = st.columns([3, 2])
        c1.dataframe(titles.head(15), hide_index=True, width="stretch", column_config={"% das vagas": PCT})
        with c2.container(border=True):
            ranking = st.session_state["ranking"]
            st.markdown("**✍️ Sugestão de título para o seu perfil**")
            target = st.selectbox("Cargo-alvo", titles["Título"].head(10))
            skills_for_headline = set(profile.skills) if profile and profile.skills else set(ranking["Skill"])
            st.code(kw.suggest_headline(target, ranking, skills_for_headline), language=None,
                    wrap_lines=True)
            st.caption("Cargo-alvo + as suas skills mais pedidas, em ordem de demanda."
                       if profile and profile.skills else
                       "Sem perfil carregado: usando as skills mais pedidas. Envie seu perfil "
                       "para a sugestão usar só o que você domina.")

        # --- Termos frequentes
        st.divider()
        st.subheader("🔍 Termos mais frequentes nas descrições")
        f1, f2, f3 = st.columns(3)
        min_pct = f1.slider("Aparece em pelo menos (% das vagas)", 5, 50, 10)
        kind = f2.radio("Mostrar", ["Todos", "Só termos livres", "Só skills do catálogo"], horizontal=True,
                        help="Termos livres são expressões fora do catálogo de skills (ex.: 'arquitetura "
                             "de dados', 'boas práticas'), úteis para o texto do 'Sobre' e das experiências.")
        sizes = f3.multiselect("Tamanho do termo", [1, 2, 3], [1, 2, 3],
                               format_func=lambda n: f"{n} palavra{'s' if n > 1 else ''}")

        terms = kw.term_frequency(descriptions, min_pct)
        if terms.empty:
            st.warning("Nenhum termo com essa frequência. Diminua o mínimo ou busque mais vagas.")
        else:
            if has_profile:
                terms = kw.missing_in_profile(terms, profile.text)
            view = terms[terms["Palavras"].isin(sizes)]
            if kind == "Só termos livres":
                view = view[view["Categoria"] == "Termo livre"]
            elif kind == "Só skills do catálogo":
                view = view[view["Categoria"] != "Termo livre"]

            config = {"% das vagas": PCT}
            left, right = st.columns(2) if has_profile else (st.container(), None)
            with left:
                st.markdown(f"**Ranking ({len(view)} termos)**")
                st.dataframe(view.drop(columns=["Palavras"]), hide_index=True, width="stretch",
                             height=420, column_config=config)
            if right is not None:
                with right:
                    missing = view[~view["No seu perfil?"]]
                    st.markdown(f"**📌 Faltam no seu perfil ({len(missing)})**")
                    st.caption("Termos frequentes nas vagas que não aparecem em nenhum lugar do seu "
                               "perfil. Se você tem a experiência, escreva-os no título, no 'Sobre', "
                               "nas experiências ou em Competências. Se não tem, entram no plano de estudo.")
                    st.dataframe(missing[["Termo", "% das vagas", "Categoria"]], hide_index=True,
                                 width="stretch", height=420, column_config=config)
            else:
                st.caption("Envie seu perfil na aba **Meu perfil** para ver quais termos faltam nele.")

            st.download_button("Baixar palavras-chave (CSV)", terms.to_csv(index=False).encode("utf-8"),
                               "palavras_chave.csv", "text/csv", icon="⬇️")

            # --- Contexto
            st.divider()
            st.subheader("💬 Como o termo aparece nas vagas")
            term = st.selectbox("Escolha um termo", view["Termo"].tolist() or terms["Termo"].tolist())
            for snip in kw.snippets(descriptions, term):
                st.markdown("> " + snip.replace("$", r"\$"))

# ---------------------------------------------------------------- Cabeçalho e rodapé
profile = st.session_state.get("profile")
has_jobs, has_profile = bool(jobs), bool(profile and profile.skills)
with header.container():
    ui.hero([("Buscar vagas", has_jobs), ("Palavras-chave", has_jobs),
             ("Enviar perfil", has_profile), ("Ver aderência", has_jobs and has_profile)])
ui.footer()
