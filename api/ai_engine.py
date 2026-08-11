import os
from openai import OpenAI

try:
    from django.conf import settings
except Exception:
    settings = None


ELAB_SYSTEM_PROMPT = """
You are E-Lab Innovation Mentor AI inside Efunza School OS.

CRITICAL BEHAVIOR RULES:
- You are NOT a book, library, reading, or E-Readathon assistant.
- Do NOT reference books, reading lists, chapters, novels, authors, library activities, book summaries, stories, or chapters unless the user explicitly asks for books.
- Do NOT say "in the book", "this book", "the story", "the chapter", "reading activity", or "Readathon" unless the user explicitly asks for reading support.
- Focus only on STEM innovation, engineering, science fair projects, experiments, prototypes, research design, product development, entrepreneurship, patent readiness, E²IO analysis, circuits, robotics, IoT, and practical implementation.

Your normal response structure:
1. Project diagnosis
2. Practical improvement
3. Materials/tools
4. Method/experiment/prototype plan
5. Risks/safety
6. Data to collect
7. Innovation score or judging insight where relevant
8. Next actions

Keep advice practical for Kenyan schools and high-school/TVET learners.
"""


AGENTS = {
    "tutor": """
You are Efunza Tutor AI. Explain clearly, adapt to Kenyan learners, and give examples.
Only discuss books if the user asks about books or reading.
""",
    "readathon": """
You are E-Readathon AI. Your job is specifically reading support: summarize books, generate quizzes, explain vocabulary, and produce parent/teacher reading reports.
""",
    "elab": ELAB_SYSTEM_PROMPT,
    "innovation": ELAB_SYSTEM_PROMPT,
    "circuit": """
You are E-Lab Circuit Reviewer AI.
Do NOT reference books unless explicitly asked.
Focus on Arduino, ESP32, IoT, robotics, power, wiring, components, sensors, safety, cost, and debugging.
Give practical wiring risks, power issues, missing components, and improvements.
""",
    "judge": """
You are E-Lab Science Fair Judge AI.
Do NOT reference books unless explicitly asked.
Evaluate originality, scientific method, engineering design, data evidence, feasibility, impact, presentation and commercialization.
Give score out of 100 and improvement actions.
""",
    "patent": """
You are E-Lab Patent Readiness AI.
Do NOT reference books unless explicitly asked.
Evaluate novelty, usefulness, non-obviousness, prior-art search terms, claim potential, commercialization value and protection strategy.
This is educational guidance, not legal advice.
""",
    "business": """
You are E-Lab Business Model AI.
Do NOT reference books unless explicitly asked.
Evaluate users, customer pain, market, pricing, competitors, revenue model, distribution, scalability and launch strategy.
""",
    "career": """
You are Career Guidance AI. Match learners to careers based on strengths, interests, performance and innovation patterns.
Do not reference books unless explicitly asked.
""",
    "teacher": """
You are Teacher Intelligence AI. Give teacher insights, weak topic analysis, interventions and class support plans.
Do not default to books unless the module is readathon.
""",
    "principal": "You are Principal AI. Provide school-level operational insights and recommendations.",
    "parent": "You are Parent Companion AI. Explain student progress in simple supportive language.",
    "nexus": """
You are Nexus Innovation AI. Help with inventions, patents, science fair projects, and product concepts.
Only discuss books if the user explicitly asks for books.
""",
}


ELAB_MODULES = {
    "elab",
    "elab_project",
    "elab_free_prompt",
    "elab_free_coach",
    "elab_free_mentor",
    "elab_free_research",
    "elab_free_experiment",
    "elab_free_report",
    "elab_free_pitch",
    "elab_free_score",
    "elab_free_circuit",
    "elab_free_business",
    "elab_free_patent",
    "elab_free_judge",
    "elab_free_e2io",
    "science_fair",
    "innovation",
    "prototype",
    "circuit",
    "patent",
    "business_model",
    "innovation_score",
}


def _safe_lower(value, fallback=""):
    return str(value or fallback).strip().lower()


def _get_setting(name, default=""):
    if settings is None:
        return default
    return getattr(settings, name, default) or default


def get_openai_api_key():
    """Return OpenAI key from the most reliable available source.

    Priority:
    1. OS environment variable OPENAI_API_KEY
    2. Django settings.OPENAI_API_KEY
    3. Empty string

    This supports projects using python-decouple in settings.py, where the key
    exists in Django settings but may not be visible through os.getenv().
    """

    env_key = os.getenv("OPENAI_API_KEY", "") or ""
    settings_key = _get_setting("OPENAI_API_KEY", "") or ""

    api_key = env_key or settings_key

    print("=" * 80)
    print("AI_ENGINE KEY DEBUG")
    print("ENV KEY:", env_key[:20] if env_key else "NONE")
    print("SETTINGS KEY:", settings_key[:20] if settings_key else "NONE")
    print("FINAL KEY:", api_key[:20] if api_key else "NONE")
    print("=" * 80)

    return api_key


def get_openai_model():
    return (
        os.getenv("OPENAI_MODEL", "")
        or _get_setting("OPENAI_MODEL", "")
        or "gpt-4o-mini"
    )


def resolve_agent(agent="tutor", module="general"):
    agent_key = _safe_lower(agent, "tutor")
    module_key = _safe_lower(module, "general")

    if (
        module_key in ELAB_MODULES
        or module_key.startswith("elab")
        or agent_key in ["elab", "innovation", "circuit", "judge", "patent", "business", "nexus"]
    ):
        if agent_key in ["circuit", "judge", "patent", "business"]:
            return agent_key
        return "elab"

    if agent_key in AGENTS:
        return agent_key

    return "tutor"


def sanitize_context_for_agent(agent_key, context):
    if not isinstance(context, dict):
        return {}

    if agent_key in ["elab", "innovation", "circuit", "judge", "patent", "business"]:
        allowed = {
            "title",
            "project_title",
            "category",
            "difficulty",
            "duration",
            "description",
            "problem_statement",
            "stage",
            "materials",
            "method",
            "outcomes",
            "expected_outcome",
            "rubric",
            "careers",
            "e2io",
            "innovation_score",
            "screen",
            "aiMode",
            "mode",
            "prototype",
            "components",
            "budget",
            "variables",
            "hypothesis",
            "data",
            "safety",
            "testing_plan",
            "business_model",
            "patent_notes",
            "circuit",
            "wiring",
            "sensors",
            "power",
            "cost",
        }
        return {key: value for key, value in context.items() if key in allowed}

    return context


def is_elab_agent(agent_key):
    return agent_key in ["elab", "innovation", "circuit", "judge", "patent", "business"]


def build_user_prompt(agent_key, prompt):
    if is_elab_agent(agent_key):
        return f"""
E-Lab task. Respond as an innovation/STEM mentor only.
Do not reference books, chapters, reading, stories, authors, or E-Readathon unless the user explicitly asks for books.

User request:
{prompt}
"""

    return prompt or ""


def sanitize_elab_response(text):
    if not text:
        return text

    banned_phrases = [
        "in the book",
        "this book",
        "the chapter",
        "the story",
        "reading activity",
        "readathon",
        "book summary",
        "book title",
        "author of the book",
    ]

    if any(phrase in text.lower() for phrase in banned_phrases):
        return (
            "Project Diagnosis:\n"
            "Your request is an E-Lab STEM innovation task, so the response should focus on engineering, experimentation, prototyping and science fair readiness.\n\n"
            "Practical Improvement:\n"
            "Define the exact problem your project solves, identify the users, choose measurable variables, and build a simple prototype that can be tested safely.\n\n"
            "Materials/Tools:\n"
            "- ESP32 or Arduino-compatible controller\n"
            "- Relevant sensor/module for the project\n"
            "- Breadboard/jumper wires\n"
            "- Power source\n"
            "- Notebook for data collection\n\n"
            "Method/Prototype Plan:\n"
            "1. State the problem.\n"
            "2. Draw the system diagram.\n"
            "3. Build the minimum working circuit.\n"
            "4. Test one variable at a time.\n"
            "5. Record data in a table.\n"
            "6. Improve the design based on test results.\n\n"
            "Risks/Safety:\n"
            "Check power polarity, avoid short circuits, keep water away from live electronics, and use low-voltage DC power.\n\n"
            "Next Actions:\n"
            "Share your exact project idea, components available, budget, and expected demonstration so I can refine it."
        )

    return text


def run_ai(agent="tutor", prompt="", context=None, module="general"):
    agent_key = resolve_agent(agent, module)
    system = AGENTS.get(agent_key, AGENTS["tutor"])
    clean_context = sanitize_context_for_agent(agent_key, context or {})
    final_prompt = build_user_prompt(agent_key, prompt or "")
    context_text = f"\n\nContext:\n{clean_context}" if clean_context else ""

    api_key = get_openai_api_key()

    if not api_key or "replace" in api_key.lower():
        return (
            f"[DEMO MODE - {agent_key.upper()}]\n\n"
            f"{final_prompt.strip()}\n"
            f"{context_text}\n\n"
            "Add OPENAI_API_KEY to enable live AI responses."
        )

    try:
        client = OpenAI(api_key=api_key)
        model = get_openai_model()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system.strip()},
                {"role": "user", "content": f"{final_prompt}{context_text}"},
            ],
            temperature=0.42,
        )

        text = response.choices[0].message.content or ""

        if is_elab_agent(agent_key):
            text = sanitize_elab_response(text)

        return text

    except Exception as exc:
        return f"[AI ERROR] {str(exc)}"
