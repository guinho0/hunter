"""Coleta de vagas públicas do LinkedIn (endpoints "jobs-guest", sem login).

Não usa sua conta. Faz pausas entre requisições e guarda as descrições em cache
(.cache/jobs/<id>.json), então buscas repetidas não voltam ao LinkedIn.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterator

import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
POSTING_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "jobs"
PAGE_SIZE = 10  # o endpoint de busca devolve ~10 cards por página

# Filtro f_E do LinkedIn
EXPERIENCE_LEVELS = {
    "Estágio": "1",
    "Júnior (entry level)": "2",
    "Assistente": "3",
    "Pleno/Sênior": "4",
    "Diretor": "5",
    "Executivo": "6",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


@dataclass
class Job:
    job_id: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    seniority: str = ""


class LinkedInClient:
    def __init__(self, delay: tuple[float, float] = (1.0, 2.5), max_retries: int = 4):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay
        self.max_retries = max_retries
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get(self, url: str, params: dict | None = None) -> requests.Response | None:
        for attempt in range(self.max_retries):
            time.sleep(random.uniform(*self.delay))
            resp = self.session.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 999) or resp.status_code >= 500:
                time.sleep(5 * 2**attempt)  # backoff: 5s, 10s, 20s...
                continue
            return None  # 400/404: página vazia ou vaga removida
        return None

    def search(self, keywords: str, location: str, experience: list[str],
               max_jobs: int, last_days: int | None = None) -> Iterator[Job]:
        seen: set[str] = set()
        start = 0
        while len(seen) < max_jobs:
            params = {"keywords": keywords, "location": location, "start": start}
            if experience:
                params["f_E"] = ",".join(experience)
            if last_days:
                params["f_TPR"] = f"r{last_days * 86400}"
            resp = self._get(SEARCH_URL, params)
            if resp is None or not resp.text.strip():
                break
            cards = BeautifulSoup(resp.text, "html.parser").select("li")
            new = 0
            for card in cards:
                job = _parse_card(card)
                if job and job.job_id not in seen:
                    seen.add(job.job_id)
                    new += 1
                    yield job
                    if len(seen) >= max_jobs:
                        return
            if new == 0:
                break
            start += PAGE_SIZE

    def fill_description(self, job: Job) -> Job:
        cache_file = CACHE_DIR / f"{job.job_id}.json"
        if cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            job.description, job.seniority = cached["description"], cached.get("seniority", "")
            return job
        resp = self._get(POSTING_URL.format(job_id=job.job_id))
        if resp is None:
            return job
        soup = BeautifulSoup(resp.text, "html.parser")
        desc = soup.select_one(".show-more-less-html__markup") or soup.select_one(".description__text")
        job.description = desc.get_text(" ", strip=True) if desc else ""
        for item in soup.select(".description__job-criteria-item"):
            header = item.select_one("h3")
            if header and header.get_text(strip=True).lower() in ("nível de experiência", "seniority level"):
                value = item.select_one("span")
                job.seniority = value.get_text(strip=True) if value else ""
        if job.description:
            cache_file.write_text(json.dumps(asdict(job), ensure_ascii=False), encoding="utf-8")
        return job


def _parse_card(card) -> Job | None:
    root = card.select_one("[data-entity-urn]")
    if root is None:
        return None
    job_id = root["data-entity-urn"].rsplit(":", 1)[-1]

    def text(selector: str) -> str:
        el = card.select_one(selector)
        return el.get_text(strip=True) if el else ""

    link = card.select_one("a.base-card__full-link")
    return Job(
        job_id=job_id,
        title=text(".base-search-card__title"),
        company=text(".base-search-card__subtitle"),
        location=text(".job-search-card__location"),
        url=link["href"].split("?")[0] if link else f"https://www.linkedin.com/jobs/view/{job_id}",
    )


def collect_jobs(keywords: str, location: str, experience: list[str], max_jobs: int,
                 last_days: int | None = None,
                 progress: Callable[[int, int, Job], None] | None = None) -> list[Job]:
    client = LinkedInClient()
    cards = list(client.search(keywords, location, experience, max_jobs, last_days))
    jobs = []
    for i, job in enumerate(cards, 1):
        jobs.append(client.fill_description(job))
        if progress:
            progress(i, len(cards), job)
    return [j for j in jobs if j.description]
