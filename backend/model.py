from __future__ import annotations
import os
from typing import List, Optional
from dataclasses import dataclass
from jinja2 import Template

# -------- Data models --------
@dataclass
class Experience:
    company: str
    title: str
    start: str
    end: str
    bullets: List[str]

@dataclass
class Education:
    degree: str
    school: str
    start: str
    end: str

@dataclass
class Resume:
    name: str
    email: str
    phone: Optional[str]
    location: Optional[str]
    links: Optional[List[str]]
    summary: Optional[str]
    skills: List[str]
    experience: List[Experience]
    education: List[Education]

LOCAL_TEMPLATE = Template(
    """
{{ name }}
{{ location or '' }} | {{ email }}{% if phone %} | {{ phone }}{% endif %}{% if links %} | {{ ', '.join(links) }}{% endif %}

{{ today }}

Hiring Manager
{{ company }}

Re: {{ role }}

Dear Hiring Team,

{% if summary %}{{ summary }} {% endif %}I'm applying for the {{ role }} role at {{ company }}. Below are a few reasons I'm a strong match for your requirements:

{% for b in matched_bullets %}- {{ b }}
{% endfor %}

I value clear outcomes over buzzwords. If helpful, I'm happy to share a small code sample or walk through how I'd ship the first milestone in week one.

Kind regards,
{{ name }}
"""
)

# -------- Simple matching logic --------
def select_bullets(resume: Resume, job_keywords: List[str], max_items: int = 5) -> List[str]:
    kws = [k.lower() for k in job_keywords]
    scored: List[tuple[int, str]] = []
    for xp in resume.experience:
        for b in xp.bullets:
            score = sum(1 for k in kws if k in b.lower())
            if score:
                scored.append((score, b))
    # fall back to any bullets if none matched
    if not scored:
        for xp in resume.experience:
            for b in xp.bullets:
                scored.append((0, b))
    scored.sort(key=lambda t: t[0], reverse=True)
    uniq: List[str] = []
    for _, b in scored:
        if b not in uniq:
            uniq.append(b)
        if len(uniq) >= max_items:
            break
    return uniq

# -------- Renderer --------
def render_local(resume: Resume, company: str, role: str, job_keywords: List[str], today: str) -> str:
    bullets = select_bullets(resume, job_keywords)
    return LOCAL_TEMPLATE.render(
        name=resume.name,
        email=resume.email,
        phone=resume.phone,
        location=resume.location,
        links=resume.links,
        summary=resume.summary,
        company=company,
        role=role,
        matched_bullets=bullets,
        today=today,
    )