"""Localidades: traduz o que o usuário digita (cidade, estado, sigla, região) em geoIds do
LinkedIn e identifica estado/região/modalidade de cada vaga.

Exemplos aceitos: "Brasil", "Sudeste", "ES", "Espírito Santo", "Vitória", "Campinas",
"Lisboa" (qualquer lugar que o LinkedIn conheça).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

GEO_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "geo.json"
TYPEAHEAD_URL = "https://www.linkedin.com/jobs-guest/api/typeaheadHits"
BRAZIL_GEO_ID = "106057199"
BRAZIL = "Brasil (todo)"

UFS: dict[str, tuple[str, str]] = {
    "AC": ("Acre", "Norte"), "AL": ("Alagoas", "Nordeste"), "AP": ("Amapá", "Norte"),
    "AM": ("Amazonas", "Norte"), "BA": ("Bahia", "Nordeste"), "CE": ("Ceará", "Nordeste"),
    "DF": ("Distrito Federal", "Centro-Oeste"), "ES": ("Espírito Santo", "Sudeste"),
    "GO": ("Goiás", "Centro-Oeste"), "MA": ("Maranhão", "Nordeste"),
    "MT": ("Mato Grosso", "Centro-Oeste"), "MS": ("Mato Grosso do Sul", "Centro-Oeste"),
    "MG": ("Minas Gerais", "Sudeste"), "PA": ("Pará", "Norte"), "PB": ("Paraíba", "Nordeste"),
    "PR": ("Paraná", "Sul"), "PE": ("Pernambuco", "Nordeste"), "PI": ("Piauí", "Nordeste"),
    "RJ": ("Rio de Janeiro", "Sudeste"), "RN": ("Rio Grande do Norte", "Nordeste"),
    "RS": ("Rio Grande do Sul", "Sul"), "RO": ("Rondônia", "Norte"), "RR": ("Roraima", "Norte"),
    "SC": ("Santa Catarina", "Sul"), "SP": ("São Paulo", "Sudeste"), "SE": ("Sergipe", "Nordeste"),
    "TO": ("Tocantins", "Norte"),
}
REGIONS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

# Cidades que o LinkedIn mostra como "<Cidade> e Região" ou sem a sigla do estado.
CITY_UF = {
    "são paulo": "SP", "campinas": "SP", "rio de janeiro": "RJ", "belo horizonte": "MG",
    "vitória": "ES", "curitiba": "PR", "porto alegre": "RS", "florianópolis": "SC",
    "salvador": "BA", "recife": "PE", "fortaleza": "CE", "brasília": "DF", "goiânia": "GO",
    "manaus": "AM", "belém": "PA", "natal": "RN", "joão pessoa": "PB", "maceió": "AL",
    "aracaju": "SE", "teresina": "PI", "são luís": "MA", "cuiabá": "MT", "campo grande": "MS",
    "londrina": "PR", "joinville": "SC", "ribeirão preto": "SP", "sorocaba": "SP",
    "são josé dos campos": "SP", "santos": "SP", "uberlândia": "MG", "juiz de fora": "MG",
}

def _city_label(city: str, uf: str) -> str:
    words = [w if w in ("de", "dos", "da") else w.capitalize() for w in city.split()]
    return f"{' '.join(words)}, {uf}"


# Sugestões do seletor; qualquer outro lugar pode ser digitado.
SUGGESTIONS = ([BRAZIL] + REGIONS + sorted(name for name, _ in UFS.values())
               + sorted(_city_label(c, uf) for c, uf in CITY_UF.items()))


def _fold(text: str) -> str:
    """minúsculas e sem acento: 'Espírito Santo' -> 'espirito santo'."""
    text = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in text if not unicodedata.combining(c))


_NAME_TO_UF = {_fold(name): uf for uf, (name, _) in UFS.items()}
_REGION_KEYS = {_fold(r): r for r in REGIONS}


def _load_cache() -> dict:
    try:
        return json.loads(GEO_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _typeahead(client, query: str, exact: str = "") -> tuple[str, str] | None:
    """Autocompletar do LinkedIn -> (geoId, nome exibido).

    Preferência: nome exibido igual a `exact` > começa com o termo e é no Brasil >
    começa com o termo > primeiro resultado.
    """
    hits = []
    for _ in range(3):  # o LinkedIn às vezes devolve os nomes vazios; tenta de novo
        resp = client._get(TYPEAHEAD_URL, {
            "query": _fold(query), "typeaheadType": "GEO",
            "geoTypes": "POPULATED_PLACE,ADMIN_DIVISION_1,ADMIN_DIVISION_2,MARKET_AREA,COUNTRY_REGION",
        })
        hits = json.loads(resp.text) if resp is not None else []
        if not hits or any(h.get("displayName") for h in hits):
            break
    if not hits:
        return None
    name = lambda h: _fold(h.get("displayName", ""))
    head = _fold(query).split(",")[0]
    ranked = (
        [h for h in hits if exact and name(h) == _fold(exact)]
        + [h for h in hits if name(h).startswith(head + ",") and name(h).endswith(", brasil")]
        + [h for h in hits if name(h).startswith(head + ",")]
        + hits
    )
    return ranked[0]["id"], ranked[0].get("displayName") or query


def resolve(client, terms: list[str]) -> tuple[list[tuple[str, str]], list[str]]:
    """Converte termos digitados em [(rótulo, geoId)]. Regiões viram seus estados.

    Retorna (localidades encontradas, termos que o LinkedIn não reconheceu).
    """
    cache = _load_cache()
    out: list[tuple[str, str]] = []
    missing: list[str] = []
    for term in terms:
        key = _fold(term)
        if not key:
            continue
        if key in (_fold(BRAZIL), "brasil", "brazil"):
            out.append(("Brasil", BRAZIL_GEO_ID))
            continue
        if key in _REGION_KEYS:
            region = _REGION_KEYS[key]
            states = [name for name, reg in UFS.values() if reg == region]
            out.extend(resolve(client, states)[0])
            continue
        uf = term.strip().upper() if term.strip().upper() in UFS else _NAME_TO_UF.get(key)
        city = re.fullmatch(r"(.+?),\s*([A-Za-z]{2})", term.strip())
        if uf:                                          # estado: "ES", "Espírito Santo"
            query, exact = UFS[uf][0], f"{UFS[uf][0]}, Brasil"
        elif city and city.group(2).upper() in UFS:     # cidade: "Vitória, ES"
            state = UFS[city.group(2).upper()][0]
            query, exact = f"{city.group(1)}, {state}", f"{city.group(1)}, {state}, Brasil"
        else:                                           # qualquer outro lugar
            query, exact = term, ""
        if query not in cache:
            hit = _typeahead(client, query, exact)
            if hit is None:
                missing.append(term)
                continue
            cache[query] = hit
        out.append((cache[query][1] or query, cache[query][0]))
    GEO_CACHE.parent.mkdir(parents=True, exist_ok=True)
    GEO_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return list(dict.fromkeys(out)), missing


def uf_of(location: str) -> str | None:
    """'Vila Velha, ES' / 'Minas Gerais, Brasil' / 'Recife e Região' -> sigla do estado."""
    m = re.search(r",\s*([A-Z]{2})\b", location)
    if m and m.group(1) in UFS:
        return m.group(1)
    folded = _fold(location)
    for name, uf in sorted(_NAME_TO_UF.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"\b{re.escape(name)}\b", folded):
            return uf
    city = re.sub(r"\s+e regi[aã]o.*$", "", folded).split(",")[0].strip()
    return {_fold(c): u for c, u in CITY_UF.items()}.get(city)


def place_label(location: str) -> tuple[str, str]:
    """-> (Estado, Região) para exibir/filtrar; vagas sem estado viram 'Brasil (não especificado)'."""
    uf = uf_of(location)
    if uf:
        name, region = UFS[uf]
        return f"{name} ({uf})", region
    if _fold(location) in ("brasil", "brazil"):
        return "Brasil (não especificado)", "Não especificada"
    return location or "Não informado", "Exterior/Outra"


_REMOTE = re.compile(r"\b(remot[oa]|remote|home[- ]office|100% remot|trabalho remoto|anywhere)\b", re.I)
_HYBRID = re.compile(r"\b(h[íi]brid[oa]|hybrid)\b", re.I)
_ONSITE = re.compile(r"\b(presencial|on[- ]site|onsite)\b", re.I)


def work_mode(title: str, description: str) -> str:
    """Modalidade pela menção no título (prioridade) ou na descrição."""
    for text in (title, description):
        if _HYBRID.search(text):
            return "Híbrido"
        if _REMOTE.search(text):
            return "Remoto"
        if _ONSITE.search(text):
            return "Presencial"
    return "Não informado"
