SYSTEM_PROMPT = "You are a concise, specific application writer. Avoid buzzwords. Write in plain English."
USER_PROMPT = (
    "Using the resume and job description, write a short cover letter (220-320 words) "
    "with a 2-sentence intro, 3-5 bullet achievements tailored to the JD, and a brief close.\n\n"
    "RESUME: {resume}\n\nJOB DESCRIPTION: {jd}\n\n"
    "ROLE: {role}\nCOMPANY: {company}\nTONE: {tone}\nLENGTH: {length}"
)