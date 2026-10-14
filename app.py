"""Hunter: skills mais pedidas no LinkedIn para uma carreira e aderência do seu perfil.

Rodar:  streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from hunter import analysis, keywords as kw, profile as prof
from hunter.linkedin_jobs import EXPERIENCE_LEVELS, Job, collect_jobs
from hunter.taxonomy import SKILLS, add_custom_skills

SEARCHES_DIR = Path(__file__).parent / ".cache" / "searches"
COLOR_HAVE = "#2a78d6"   # azul: skill que você tem / demanda do mercado
COLOR_GAP = "#eb6834"    # laranja: skill que falta

st.set_page_config(page_title="Hunter · Skills do mercado", page_icon="🎯", layout="wide")
st.title("🎯 Hunter")
st.caption("Quais skills o mercado pede no LinkedIn para uma carreira e quanto o seu perfil está aderente.")

# ---------------------------------------------------------------- Sidebar: busca
with st.sidebar:
    st.header("1. Carreira")
    keywords = st.text_input("Cargo", "Engenheiro de dados")
    location = st.text_input("Local (em inglês)", "Brazil",
                             help='Ex.: "Brazil", "São Paulo, Brazil", "Remote"')
    levels = st.multiselect("Nível de experiência", list(EXPERIENCE_LEVELS), ["Júnior (entry level)"])
    max_jobs = st.slider("Quantidade de vagas", 10, 200, 50, step=10,
                         help="Cada vaga leva ~2s na primeira vez; depois fica em cache.")
    last_days = st.selectbox("Publicadas nos últimos", [None, 1, 7, 30],
                             format_func=lambda d: "qualquer data" if d is None else f"{d} dia(s)", index=3)
    custom = st.text_input("Skills extras para rastrear (separadas por vírgula)",
                           placeholder="ex.: Kedro, Metabase")
    add_custom_skills(custom.split(","))
    run = st.button("🔎 Buscar vagas", type="primary", width="stretch")

    saved = sorted(SEARCHES_DIR.glob("*.json"), reverse=True) if SEARCHES_DIR.exists() else []
    if saved:
        st.divider()
        pick = st.selectbox("…ou carregar busca salva", [None] + saved,
                            format_func=lambda p: "—" if p is None else p.stem)
        if pick and st.button("Carregar", width="stretch"):
            data = json.loads(pick.read_text(encoding="utf-8"))
            st.session_state["jobs"] = [Job(**j) for j in data["jobs"]]
            st.session_state["query"] = data["query"]

if run:
    bar = st.progress(0.0, "Buscando vagas no LinkedIn…")
    jobs = collect_jobs(
        keywords, location, [EXPERIENCE_LEVELS[l] for l in levels], max_jobs, last_days,
        progress=lambda i, n, j: bar.progress(i / n, f"Lendo vaga {i}/{n}: {j.title[:60]}"),
    )
    bar.empty()
    query = f"{keywords} · {location} · {', '.join(levels) or 'todos os níveis'}"
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
        st.info("Configure a carreira na barra lateral e clique em **Buscar vagas**.")
    else:
        jobs_df = analysis.jobs_dataframe(jobs)
        all_levels = sorted(jobs_df["Nível (título)"].unique())
        keep = st.multiselect(
            "Filtrar pelo nível indicado no título da vaga", all_levels, all_levels,
            help="O filtro de nível do LinkedIn é frouxo; aqui você refina pelo título "
                 "(ex.: manter só 'Júnior' e 'Não informado').")
        jobs_df = jobs_df[jobs_df["Nível (título)"].isin(keep)]
        st.session_state["jobs_df"] = jobs_df

        if jobs_df.empty:
            st.warning("Nenhuma vaga com esse filtro.")
        else:
            ranking = analysis.skill_ranking(jobs_df)
            st.session_state["ranking"] = ranking

            st.subheader(st.session_state.get("query", ""))
            c1, c2, c3 = st.columns(3)
            c1.metric("Vagas analisadas", len(jobs_df))
            c2.metric("Skills distintas encontradas", len(ranking))
            c3.metric("Skills por vaga (mediana)", int(jobs_df["skills"].map(len).median()))

            top_n = st.slider("Mostrar top", 5, 50, 25)
            top = ranking.head(top_n)
            fig = px.bar(top.iloc[::-1], x="% das vagas", y="Skill", orientation="h",
                         text="% das vagas", hover_data={"Vagas": True, "Categoria": True},
                         color_discrete_sequence=[COLOR_HAVE])
            fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", cliponaxis=False)
            fig.update_layout(height=max(320, 24 * len(top)), yaxis_title=None,
                              xaxis_title="% das vagas que citam a skill", bargap=0.25,
                              margin=dict(l=0, r=40, t=10, b=0))
            st.plotly_chart(fig, width="stretch")

            st.markdown("**Por categoria**")
            by_cat = ranking.groupby("Categoria")["Skill"].apply(
                lambda s: ", ".join(s.head(6))).reset_index(name="Mais pedidas")
            by_cat["Maior %"] = ranking.groupby("Categoria")["% das vagas"].max().values
            st.dataframe(by_cat.sort_values("Maior %", ascending=False), hide_index=True,
                         width="stretch")

            with st.expander(f"Ver as {len(jobs_df)} vagas"):
                view = jobs_df.assign(skills=jobs_df["skills"].map(", ".join)).drop(columns=["job_id", "Descrição"])
                st.dataframe(view, hide_index=True, width="stretch",
                             column_config={"Link": st.column_config.LinkColumn("Link")})
            st.download_button("⬇️ Baixar ranking (CSV)", ranking.to_csv(index=False).encode("utf-8"),
                               "ranking_skills.csv", "text/csv")

# ---------------------------------------------------------------- Perfil
with tab_profile:
    st.markdown(
        "Envie seus dados do LinkedIn por **uma ou mais** fontes abaixo:\n"
        "- **ZIP de dados** (mais completo): LinkedIn → *Configurações e Privacidade* → "
        "*Privacidade de dados* → *Baixe seus dados* → selecione Perfil, Competências, Cargos, "
        "Certificações, Cursos, Projetos, Formação e Idiomas.\n"
        "- **PDF do perfil**: no seu perfil → *Mais* → *Salvar como PDF*.\n"
        "- **Texto livre**: cole experiências, cursos ou certificações que não estão no LinkedIn.")

    c1, c2 = st.columns(2)
    zip_file = c1.file_uploader("ZIP de dados do LinkedIn", type="zip")
    pdf_file = c2.file_uploader("PDF do perfil", type="pdf")
    free_text = st.text_area("Texto livre", height=120)

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

        m1, m2, m3 = st.columns(3)
        m1.metric("Aderência ao mercado", f"{res.score:.0f}%",
                  help="Soma da demanda (% das vagas) das skills que você tem ÷ demanda total das top N. "
                       "Skills mais pedidas pesam mais.")
        m2.metric("Cobertura das top skills", f"{res.coverage:.0f}%",
                  help="Quantas das top N skills você tem, sem ponderar.")
        m3.metric("Skills que faltam", len(res.gaps))

        chart = res.table.assign(Status=res.table["Você tem?"].map({True: "Você tem", False: "Falta"}))
        fig = px.bar(chart.iloc[::-1], x="% das vagas", y="Skill", color="Status", orientation="h",
                     color_discrete_map={"Você tem": COLOR_HAVE, "Falta": COLOR_GAP},
                     category_orders={"Status": ["Você tem", "Falta"]},
                     hover_data={"Categoria": True, "Onde aparece no seu perfil": True})
        fig.update_layout(height=max(320, 24 * len(chart)), yaxis_title=None, bargap=0.25,
                          xaxis_title="% das vagas que citam a skill", legend_title=None,
                          legend=dict(orientation="h", y=1.05), margin=dict(l=0, r=10, t=30, b=0))
        st.plotly_chart(fig, width="stretch")

        left, right = st.columns(2)
        with left:
            st.markdown("**📚 O que estudar primeiro** (ordenado pela demanda)")
            if res.gaps.empty:
                st.success("Você cobre todas as top skills deste recorte!")
            else:
                st.dataframe(res.gaps, hide_index=True, width="stretch",
                             column_config={"% das vagas": st.column_config.ProgressColumn(
                                 "% das vagas", format="%.0f%%", min_value=0, max_value=100)})
        with right:
            st.markdown("**💪 Seus diferenciais** (você tem, mas não estão no top)")
            st.write(", ".join(res.extras) or "—")

        st.markdown("**🎯 Vagas com maior match com o seu perfil**")
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
        c1.dataframe(titles.head(15), hide_index=True, width="stretch",
                     column_config={"% das vagas": st.column_config.ProgressColumn(
                         "% das vagas", format="%.0f%%", min_value=0, max_value=100)})
        with c2:
            ranking = st.session_state["ranking"]
            st.markdown("**✍️ Sugestão de título para o seu perfil**")
            target = st.selectbox("Cargo-alvo", titles["Título"].head(10))
            skills_for_headline = set(profile.skills) if profile and profile.skills else set(ranking["Skill"])
            st.code(kw.suggest_headline(target, ranking, skills_for_headline), language=None)
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

            config = {"% das vagas": st.column_config.ProgressColumn(
                "% das vagas", format="%.0f%%", min_value=0, max_value=100)}
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

            st.download_button("⬇️ Baixar palavras-chave (CSV)", terms.to_csv(index=False).encode("utf-8"),
                               "palavras_chave.csv", "text/csv")

            # --- Contexto
            st.divider()
            st.subheader("💬 Como o termo aparece nas vagas")
            term = st.selectbox("Escolha um termo", view["Termo"].tolist() or terms["Termo"].tolist())
            for snip in kw.snippets(descriptions, term):
                st.markdown("> " + snip.replace("$", r"\$"))
