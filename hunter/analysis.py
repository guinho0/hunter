"""Ranking de skills do mercado e aderência do perfil."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .linkedin_jobs import Job
from .profile import Profile
from .taxonomy import category, extract_skills

_LEVEL_RULES = [
    ("Estágio", r"est[áa]gi|intern(ship)?|trainee"),
    ("Júnior", r"j[úu]nior|\bjr\b|entry[- ]level|\bi\b$"),
    ("Pleno", r"pleno|\bpl\b|mid[- ]level|\bii\b"),
    ("Sênior", r"s[êe]nior|\bsr\b|\biii\b"),
    ("Especialista/Lead", r"especialista|lead|staff|principal|l[íi]der|head|tech lead"),
]


def level_from_title(title: str) -> str:
    t = title.lower()
    for level, pattern in _LEVEL_RULES:
        if re.search(pattern, t):
            return level
    return "Não informado"


def jobs_dataframe(jobs: list[Job]) -> pd.DataFrame:
    rows = []
    for job in jobs:
        rows.append({
            "job_id": job.job_id,
            "Título": job.title,
            "Empresa": job.company,
            "Local": job.location,
            "Nível (título)": level_from_title(job.title),
            "Nível (LinkedIn)": job.seniority,
            "skills": sorted(extract_skills(f"{job.title} {job.description}")),
            "Link": job.url,
            "Descrição": job.description,
        })
    return pd.DataFrame(rows)


def skill_ranking(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """% de vagas que citam cada skill (cada vaga conta no máximo 1x por skill)."""
    total = len(jobs_df)
    exploded = jobs_df.explode("skills").dropna(subset=["skills"])
    counts = exploded["skills"].value_counts()
    df = counts.rename_axis("Skill").reset_index(name="Vagas")
    df["% das vagas"] = (df["Vagas"] / total * 100).round(1)
    df["Categoria"] = df["Skill"].map(category)
    return df


@dataclass
class FitResult:
    score: float               # 0-100, ponderado pela demanda de cada skill
    coverage: float            # % das top-N skills que você tem
    table: pd.DataFrame        # top-N com coluna "Você tem?" e "Onde aparece"
    gaps: pd.DataFrame         # skills que faltam, ordenadas por demanda
    extras: list[str]          # skills suas que o mercado (top-N) não pediu


def fit(ranking: pd.DataFrame, profile: Profile, top_n: int = 20,
        min_pct: float = 5.0) -> FitResult:
    top = ranking[ranking["% das vagas"] >= min_pct].head(top_n).copy()
    have = set(profile.skills)
    top["Você tem?"] = top["Skill"].isin(have)
    top["Onde aparece no seu perfil"] = top["Skill"].map(
        lambda s: ", ".join(sorted(profile.skills.get(s, []))))

    weight_total = top["% das vagas"].sum()
    score = top.loc[top["Você tem?"], "% das vagas"].sum() / weight_total * 100 if weight_total else 0
    coverage = top["Você tem?"].mean() * 100 if len(top) else 0

    gaps = top[~top["Você tem?"]][["Skill", "Categoria", "% das vagas"]].reset_index(drop=True)
    extras = sorted(have - set(top["Skill"]))
    return FitResult(round(score, 1), round(coverage, 1), top.reset_index(drop=True), gaps, extras)


def job_matches(jobs_df: pd.DataFrame, profile: Profile) -> pd.DataFrame:
    """Para cada vaga: % das skills pedidas que você já tem."""
    have = set(profile.skills)
    df = jobs_df.copy()
    df["Pedidas"] = df["skills"].map(len)
    df["Você tem"] = df["skills"].map(lambda s: len(have & set(s)))
    df["Match %"] = (df["Você tem"] / df["Pedidas"].where(df["Pedidas"] > 0) * 100).round(0).fillna(0)
    df["Faltam"] = df["skills"].map(lambda s: ", ".join(sorted(set(s) - have)))
    return df.sort_values("Match %", ascending=False)
