"""Leitura do perfil a partir dos arquivos oficiais do LinkedIn.

Fontes aceitas:
- ZIP de "Obter uma cópia dos seus dados" (Configurações > Privacidade de dados),
  que traz Skills.csv, Certifications.csv, Courses.csv, Positions.csv etc.
- PDF do perfil (botão "Mais" > "Salvar como PDF" no seu perfil).
- Texto livre (colar o "Sobre", experiências, cursos...).
"""

from __future__ import annotations

import io
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field

import pandas as pd
from pypdf import PdfReader

from .taxonomy import PATTERNS, extract_skills

# Arquivo do export -> rótulo da fonte mostrada no app
EXPORT_FILES = {
    "Skills.csv": "Competências",
    "Certifications.csv": "Certificações",
    "Courses.csv": "Cursos",
    "Positions.csv": "Experiências",
    "Projects.csv": "Projetos",
    "Education.csv": "Formação",
    "Profile.csv": "Resumo do perfil",
    "Languages.csv": "Idiomas",
}


@dataclass
class Profile:
    # skill -> fontes onde apareceu (ex.: {"Python": {"Competências", "Cursos"}})
    skills: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    # competências declaradas que não estão no catálogo
    unmapped: set[str] = field(default_factory=set)
    # todo o texto lido, usado para checar palavras-chave das vagas
    text: str = ""

    def add_text(self, text: str, source: str) -> None:
        self.text += "\n" + text
        for skill in extract_skills(text):
            self.skills[skill].add(source)

    def merge(self, other: "Profile") -> None:
        for skill, sources in other.skills.items():
            self.skills[skill] |= sources
        self.unmapped |= other.unmapped
        self.text += "\n" + other.text


def _read_csv(raw: bytes) -> pd.DataFrame:
    text = raw.decode("utf-8-sig", errors="replace")
    # Alguns CSVs do export começam com linhas de "Notes:"; pula até o cabeçalho real.
    lines = text.splitlines()
    while lines and lines[0].lower().startswith("notes"):
        lines = lines[1:]
        while lines and lines[0].strip():
            lines = lines[1:]
        lines = lines[1:] if lines else lines
    return pd.read_csv(io.StringIO("\n".join(lines)), dtype=str, on_bad_lines="skip").fillna("")


def from_linkedin_export(zip_bytes: bytes) -> Profile:
    profile = Profile()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        by_name = {name.rsplit("/", 1)[-1]: name for name in zf.namelist()}
        for filename, source in EXPORT_FILES.items():
            if filename not in by_name:
                continue
            df = _read_csv(zf.read(by_name[filename]))
            if filename == "Skills.csv" and "Name" in df.columns:
                profile.text += "\n" + "\n".join(df["Name"])
                for name in df["Name"]:
                    found = extract_skills(name)
                    if not found:
                        profile.unmapped.add(name.strip())
                    for skill in found:
                        profile.skills[skill].add(source)
                continue
            text = "\n".join(" ".join(row) for row in df.astype(str).values.tolist())
            profile.add_text(text, source)
    return profile


def from_pdf(pdf_bytes: bytes) -> Profile:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    profile = Profile()
    profile.add_text(text, "PDF do perfil")
    return profile


def from_text(text: str, source: str = "Texto informado") -> Profile:
    profile = Profile()
    profile.add_text(text, source)
    return profile


def from_manual(skills: list[str]) -> Profile:
    profile = Profile()
    for skill in skills:
        if skill in PATTERNS:
            profile.skills[skill].add("Marcado manualmente")
    return profile
