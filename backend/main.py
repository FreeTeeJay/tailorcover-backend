from __future__ import annotations

import os
import datetime
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .model import Resume, Experience, Education, render_local
from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT

# -------------------------------------------------
# Setup
# -------------------------------------------------

load_dotenv()
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="TailorCover API", version="0.1.0")

# CORS: allow your GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://freeteejay.github.io",
        "https://freeteejay.github.io/",
        # optional: uncomment for local testing
        # "http://localhost:8000",
        # "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Schemas
# -------------------------------------------------

class ExperienceIn(BaseModel):
    company: str
    title: str
    start: str
    end: str
    bullets: List[str]


class EducationIn(BaseModel):
    degree: str
    school: str
    start: str
    end: str


class ResumeIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    links: Optional[List[str]] = None
    summary: Optional[str] = None
    skills: List[str] = []
    experience: List[ExperienceIn]
    education: List[EducationIn]


class GenerateIn(BaseModel):
    resume: ResumeIn
    job_description: str = Field(..., min_length=20)
    role: str
    company: str
    tone: str = "concise, confident"
    length: str = "short"


class GenerateOut(BaseModel):
    cover_letter: str
    mode: str


# -------------------------------------------------
# Routes
# -------------------------------------------------

@app.get("/")
def index():
    return {"ok": True, "routes": ["/healthz", "/generate", "/docs"]}


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/generate", response_model=GenerateOut)
async def generate(data: GenerateIn):
    """
    Generate a tailored cover letter.

    - If ENABLE_LLM=1 and OPENAI_API_KEY is set → use LLM mode.
    - Otherwise → use local, domain-aware template logic.
    """
    try:
        # Map Pydantic ResumeIn to dataclass Resume
        r = Resume(
            name=data.resume.name,
            email=data.resume.email,
            phone=data.resume.phone,
            location=data.resume.location,
            links=data.resume.links or [],
            summary=data.resume.summary,
            skills=data.resume.skills,
            experience=[
                Experience(
                    company=x.company,
                    title=x.title,
                    start=x.start,
                    end=x.end,
                    bullets=x.bullets,
                )
                for x in data.resume.experience
            ],
            education=[
                Education(
                    degree=e.degree,
                    school=e.school,
                    start=e.start,
                    end=e.end,
                )
                for e in data.resume.education
            ],
        )

        # simple keyword extraction from JD
        kw = [
            w.strip(",.()").lower()
            for w in data.job_description.split()
            if len(w) > 3
        ]
        # remove duplicates while keeping order
        kw = list(dict.fromkeys(kw))

        today = datetime.date.today().strftime("%d %B %Y")
        use_llm = bool(os.getenv("OPENAI_API_KEY")) and os.getenv("ENABLE_LLM", "0") == "1"

        # -------- Local mode --------
        if not use_llm:
            text = render_local(
                resume=r,
                company=data.company,
                role=data.role,
                job_keywords=kw,
                today=today,
                jd_text=data.job_description,
            )
            return {"cover_letter": text, "mode": "local"}

        # -------- LLM mode --------
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            prompt = USER_PROMPT.format(
                resume=data.resume.model_dump(),
                jd=data.job_description,
                role=data.role,
                company=data.company,
                tone=data.tone,
                length=data.length,
            )

            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            text = resp.choices[0].message.content
            return {"cover_letter": text, "mode": "llm"}
        except Exception:
            logger.exception("LLM path failed; falling back to local")
            text = render_local(
                resume=r,
                company=data.company,
                role=data.role,
                job_keywords=kw,
                today=today,
                jd_text=data.job_description,
            )
            return {"cover_letter": text, "mode": "local"}

    except Exception as e:
        logger.exception("generate() failed")
        # expose detail for debugging (fine for a demo)
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {e}",
        )
