"""Palavras-chave das vagas: termos frequentes, títulos de cargo e o que falta no perfil."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from .taxonomy import category, extract_skills

STOPWORDS = set("""
a à ao aos as às até com como da das de dela dele do dos e é em entre era essa esse esta este
eu foi for ha há isso isto já la lhe mais mas me mesmo meu minha muito na nas não nem no nos
nossa nosso nossos nossas num numa o os ou para pela pelas pelo pelos por qual quando que quem
se sem ser seu seus sua suas só também te tem têm ter um uma umas uns você vocês vai seja são
sobre cada todo toda todos todas outro outra outros outras onde bem estar está estão será serão
pode podem possa possui possuir tenha forma através além assim ainda após aqui lá isso deve
the and or of to in for with on at by from as is are be an a our we you your will this that
it its their they us all any can have has who which what about into within more other such
not but also than well using use used work working including include includes ability
""".split())

# Palavras comuns em qualquer anúncio de vaga, que não dizem nada sobre a carreira.
BOILERPLATE = set("""
vaga vagas empresa empresas oportunidade oportunidades candidato candidata candidatos pessoa
pessoas profissional profissionais buscamos procuramos requisitos requisito responsabilidades
atividades atribuições benefícios beneficios vale refeição alimentação transporte plano saúde
odontológico seguro vida auxílio gympass wellhub salário remuneração clt pj contratação
modelo regime home office híbrido hibrido presencial remoto local horário diferencial
diferenciais desejável desejáveis obrigatório obrigatórios conhecimento conhecimentos
experiência experiências inclusão diversidade igualdade gênero raça orientação sexual
deficiência pcd etc ex anos ano dia dias time times equipe equipes área áreas cliente clientes
grande grandes novo novos nova novas melhor melhores mercado brasil sp são paulo junte-se
venha faça parte nosso nossa somos missão valores cultura job jobs role team company
experience knowledge skills skill requirements responsibilities benefits years year strong
looking join candidate opportunity position preferred required plus etc e.g i.e please
assistência médica odontológica previdência privada participação lucros plr day off adicionais
estamos busca buscando américa latina provenientes utilizando utilizar usando through
completo completa cursando superior ensino formação graduação bacharelado degree
""".split())

# Verbos genéricos: não valem sozinhos nem nas pontas ("desenvolver e manter").
GENERIC_VERBS = set("""
desenvolver manter atuar apoiar fazer garantir realizar trabalhar construir criar contribuir
participar implementar executar identificar propor buscar acompanhar elaborar suportar atender
entender compreender colaborar auxiliar assegurar promover gerar transformar disponibilizar
otimizar garantindo atuando apoiando develop maintain build ensure support create design
implement collaborate help drive deliver
""".split())
# Substantivos genéricos: não valem sozinhos nem abrindo uma expressão ("dados em ambientes"),
# mas podem fechá-la ("bancos de dados").
GENERIC_NOUNS = set("""
processos soluções solução negócio negócios informações informação ambiente ambientes
ferramentas sistemas tecnologia tecnologias diferentes capacidade avançado avançada trabalho
resultados desenvolvimento construção análise análises atividades projetos projeto principais
demandas parte forte boa bom bons alta alto níveis nível tipo tipos fontes volumes
qualificações vivência organização evolução domínio correlatas parceria atuação serviços
práticas melhoria analista engenharia
""".split())
# Óbvias para a carreira buscada: só são descartadas quando aparecem sozinhas.
GENERIC_SOLO = {"dados", "data"}

_TOKEN = re.compile(r"[a-zà-ú0-9][a-zà-ú0-9+#.\-/]*[a-zà-ú0-9+#]|[a-zà-ú]")
_IGNORE = STOPWORDS | BOILERPLATE
_SOLO = _IGNORE | GENERIC_VERBS | GENERIC_NOUNS | GENERIC_SOLO
_FIRST = _IGNORE | GENERIC_VERBS | GENERIC_NOUNS
_LAST = _IGNORE | GENERIC_VERBS


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _ngrams(tokens: list[str], n_max: int = 3) -> set[str]:
    grams = set()
    for n in range(1, n_max + 1):
        for i in range(len(tokens) - n + 1):
            gram = tokens[i:i + n]
            if n == 1 and gram[0] in _SOLO:
                continue
            if gram[0] in _FIRST or gram[-1] in _LAST or any(t in BOILERPLATE for t in gram):
                continue
            if any(t.isdigit() for t in gram):
                continue
            if n == 1 and len(gram[0]) < 3:
                continue
            grams.add(" ".join(gram))
    return grams


def term_frequency(descriptions: list[str], min_pct: float = 5.0, top: int = 150) -> pd.DataFrame:
    """% de vagas em que cada termo (1 a 3 palavras) aparece."""
    total = len(descriptions)
    df_count: Counter = Counter()
    for desc in descriptions:
        df_count.update(_ngrams(_tokens(desc)))

    min_docs = max(2, total * min_pct / 100)
    candidates = {t: c for t, c in df_count.items() if c >= min_docs}

    # Remove termos "engolidos" por uma expressão maior quase tão frequente
    # (ex.: "pipelines" some se "pipelines de dados" aparece em quase as mesmas vagas).
    longer = sorted((t for t in candidates if " " in t), key=lambda t: -candidates[t])
    kept = {}
    for term, count in sorted(candidates.items(), key=lambda kv: -kv[1]):
        absorbed = any(
            f" {term} " in f" {big} " and big != term and candidates[big] >= 0.8 * count
            for big in longer)
        if not absorbed:
            kept[term] = count
        if len(kept) >= top:
            break

    rows = []
    for term, count in kept.items():
        skills = extract_skills(term)
        rows.append({
            "Termo": term,
            "Vagas": count,
            "% das vagas": round(count / total * 100, 1),
            "Palavras": len(term.split()),
            "Skill do catálogo": ", ".join(sorted(skills)),
            "Categoria": category(next(iter(skills))) if skills else "Termo livre",
        })
    return pd.DataFrame(rows)


_TITLE_GENDER = re.compile(r"\s*\((a|o|as|os)\)|/a\b", re.IGNORECASE)   # "Engenheiro(a)"
_TITLE_NOISE = re.compile(
    r"\s*[\(\[|–—].*$|"                        # corta tudo após ( [ | – —
    r"\s+-\s+.*$|"                             # e após " - "
    r"\b(j[úu]nior|jr\.?|pleno|pl|s[êe]nior|sr\.?|i{1,3}|est[áa]gi[oá]ri[oa]?|"
    r"entry[- ]level|mid[- ]level|trainee)\b",
    re.IGNORECASE)
_LOWER_WORDS = {"de", "da", "do", "das", "dos", "e", "em", "of", "and"}


def normalize_title(title: str) -> str:
    title = _TITLE_NOISE.sub(" ", _TITLE_GENDER.sub("", title))
    words = []
    for w in title.split():
        if w.lower() in _LOWER_WORDS:
            words.append(w.lower())
        elif w.isupper() and len(w) <= 3:      # siglas: BI, MIS, AWS
            words.append(w)
        else:
            words.append(w[:1].upper() + w[1:].lower())
    return " ".join(words).strip(" -,.")


def title_frequency(titles: list[str]) -> pd.DataFrame:
    counts = Counter(t for t in map(normalize_title, titles) if t)
    total = len(titles)
    return pd.DataFrame(
        [{"Título": t, "Vagas": c, "% das vagas": round(c / total * 100, 1)}
         for t, c in counts.most_common()])


def missing_in_profile(terms: pd.DataFrame, profile_text: str) -> pd.DataFrame:
    """Termos frequentes nas vagas que não aparecem em nenhum lugar do seu perfil."""
    text = f" {' '.join(_tokens(profile_text))} "
    present = terms["Termo"].map(lambda t: f" {t} " in text)
    return terms.assign(**{"No seu perfil?": present})


def snippets(descriptions: list[str], term: str, max_items: int = 8, width: int = 110) -> list[str]:
    pattern = re.compile(rf"(?<![\w]){re.escape(term)}(?![\w])", re.IGNORECASE)
    out = []
    for desc in descriptions:
        m = pattern.search(desc)
        if not m:
            continue
        start, end = max(0, m.start() - width), min(len(desc), m.end() + width)
        out.append(("…" if start else "") + desc[start:m.start()] + f"**{m.group(0)}**"
                   + desc[m.end():end] + ("…" if end < len(desc) else ""))
        if len(out) >= max_items:
            break
    return out


def suggest_headline(top_title: str, ranking: pd.DataFrame, profile_skills: set[str],
                     max_skills: int = 5) -> str:
    """Título do LinkedIn: cargo-alvo + suas skills mais pedidas pelo mercado."""
    mine = [s for s in ranking["Skill"] if s in profile_skills][:max_skills]
    return " | ".join([top_title] + mine)
