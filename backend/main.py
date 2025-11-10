from __future__ import annotations
import os, datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from .model import Resume, Experience, Education, render_local
from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT


load_dotenv()
app = FastAPI(title="TailorCover API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/generate", response_model=GenerateOut)
async def generate(data: GenerateIn):
    # Convert pydantic model to dataclass
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
            ) for x in data.resume.experience
        ],
        education=[
            Education(degree=e.degree, school=e.school, start=e.start, end=e.end)
            for e in data.resume.education
        ],
    )

    # Extract simple keywords from JD
    kw = [w.strip(",.()\n ").lower() for w in data.job_description.split() if len(w) > 3]
    kw = list(dict.fromkeys(kw))  # unique, order preserving

    today = datetime.date.today().strftime("%d %B %Y")
    use_llm = os.getenv("OPENAI_API_KEY") and os.getenv("ENABLE_LLM", "0") == "1"

    if not use_llm:
        text = render_local(r, company=data.company, role=data.role, job_keywords=kw, today=today)
        return {"cover_letter": text, "mode": "local"}

    # --- Optional LLM path (pseudo; implement with your preferred provider) ---
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])  # requires openai>=1.x
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
        # Fallback to local on any failure
        text = render_local(r, company=data.company, role=data.role, job_keywords=kw, today=today)
        return {"cover_letter": text, "mode": "local"}

@app.get("/healthz")
async def healthz():
    return {"ok": True}
