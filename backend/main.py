from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from jinja2 import Template

# ----------------- Data models -----------------

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
    links: List[str]
    summary: Optional[str]
    skills: List[str]
    experience: List[Experience]
    education: List[Education]


# ----------------- Domain logic -----------------

DOMAIN_KEYWORDS = {
    "hospitality": [
        "catering", "hospitality", "waitstaff", "server", "barista", "kitchen",
        "banquet", "front-of-house", "foh", "pos", "plating", "haccp",
        "food safety", "allergen", "chef", "venue", "function", "event",
    ],
    "software": [
        "python", "javascript", "typescript", "react", "api", "fastapi", "docker",
        "ci/cd", "git", "aws", "azure", "gcp", "database", "sql",
        "ml", "machine learning", "ai", "testing", "unit",
    ],
    "retail": [
        "retail", "sales", "pos", "store", "merchandising", "customer",
        "inventory", "stock", "cash", "replenishment", "register", "floor",
    ],
}


def infer_domain(text: str) -> str:
    t = text.lower()
    scores = {
        dom: sum(t.count(kw) for kw in kws)
        for dom, kws in DOMAIN_KEYWORDS.items()
    }
    return max(scores, key=scores.get) if any(scores.values()) else "generic"


def select_bullets(resume: Resume, job_keywords: List[str], max_items: int = 5) -> List[str]:
    kws = [k.lower() for k in job_keywords]
    scored: List[tuple[int, str]] = []

    # score bullets by keyword overlap
    for xp in resume.experience:
        for b in xp.bullets:
            score = sum(1 for k in kws if k and k in b.lower())
            if score:
                scored.append((score, b))

    # fallback: recent experience if nothing matched
    if not scored:
        for xp in resume.experience[:2]:
            for b in xp.bullets:
                scored.append((0, b))

    scored.sort(key=lambda t: t[0], reverse=True)
    out: List[str] = []
    seen = set()
    for _, b in scored:
        if b not in seen:
            seen.add(b)
            out.append(b)
        if len(out) >= max_items:
            break
    return out


# ----------------- Template + renderer -----------------

LOCAL_TEMPLATE = Template(
    """
{{ name }}
{{ location or '' }} | {{ email }}{% if phone %} | {{ phone }}{% endif %}{% if links %} | {{ ', '.join(links) }}{% endif %}

{{ today }}

Hiring Manager
{{ company }}

Re: {{ role }}

Dear Hiring Team,

{% if summary %}{{ summary }} {% endif %}I'm applying for the {{ role }} role at {{ company }}.

{% if domain == 'hospitality' -%}
I work comfortably in fast-paced, customer-facing service environments and follow food-safety standards. Highlights:
{% elif domain == 'retail' -%}
I bring reliable customer service, accurate POS handling, and tidy, well-presented stock. Highlights:
{% elif domain == 'software' -%}
I ship maintainable code, communicate clearly in reviews, and automate repetitive tasks. Highlights:
{% else -%}
Relevant highlights:
{% endif %}

{% for b in matched_bullets -%}
- {{ b }}
{% endfor %}

I value clear outcomes and reliability. I’d be happy to discuss availability or complete a short trial to demonstrate fit.

Kind regards,
{{ name }}
"""
)


def render_local(
    resume: Resume,
    company: str,
    role: str,
    job_keywords: List[str],
    today: str,
    jd_text: Optional[str] = None,
) -> str:
    """
    Local template-based generator.

    jd_text is used to help infer the domain (hospitality/software/retail/generic).
    """
    combined = " ".join(job_keywords) + " " + (jd_text or "")
    domain = infer_domain(combined)
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
        domain=domain,
    )
