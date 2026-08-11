import logging
from typing import List, Dict, Any, Optional
from django.conf import settings

from api.ai_utils import retrieve_relevant_chunks, build_rag_context

logger = logging.getLogger(__name__)


def _call_llm(prompt: str, max_tokens: int = 800, temperature: float = 0.2) -> Optional[str]:
    """Call OpenAI Responses API (if configured) and return text; otherwise None."""
    try:
        from openai import OpenAI
    except Exception:
        OpenAI = None

    if not getattr(settings, 'OPENAI_API_KEY', '') or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        model = getattr(settings, 'OPENAI_MODEL', getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'gpt-4o-mini'))
        resp = client.responses.create(model=model, input=prompt, max_tokens=max_tokens, temperature=temperature)

        # Try common response fields
        if hasattr(resp, 'output_text') and resp.output_text:
            return resp.output_text

        # Newer SDKs: resp.output is a list of message objects
        output = []
        out = getattr(resp, 'output', None)
        if out:
            for item in out:
                # item may contain 'content' which is a list of dicts
                content = item.get('content') if isinstance(item, dict) else getattr(item, 'content', None)
                if content:
                    for c in content:
                        if isinstance(c, dict) and 'text' in c:
                            output.append(c['text'])
                        elif isinstance(c, str):
                            output.append(c)
                else:
                    # fallback to string representation
                    output.append(str(item))
        if output:
            return "\n".join(output)

        # Final fallback: string of resp
        return str(resp)

    except Exception as e:
        logger.exception(f"LLM call failed: {e}")
        return None


def generate_rag_answer(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve relevant chunks and generate an answer using the LLM if available.

    Returns a dict with keys: answer (str), recommendations (list), sources (list of chunks)
    """
    retrieved = retrieve_relevant_chunks(query, top_k=top_k) or []

    sources = retrieved

    rag_context = build_rag_context(retrieved)

    prompt = (
        f"You are a maritime training tutor. Use the following sources to answer the question. "
        f"Always prioritize safety and cite sources.\n\nSOURCES:\n{rag_context}\n---\nQUESTION: {query}\n\n"
        "Produce:\n1) A concise answer (<=200 words).\n2) Two short recommended practical exercises.\n3) A list of referenced source ids in the format source_type:source_id#chunk_index."
    )

    llm_text = _call_llm(prompt)

    if llm_text:
        # Very simple parsing: split sections by numbered items if present
        return {
            'answer': llm_text,
            'recommendations': [],
            'sources': [
                {'id': s['id'], 'source_type': s['source_type'], 'source_id': s['source_id'], 'chunk_index': s['chunk_index'], 'score': s['score']}
                for s in sources
            ]
        }

    # Fallback: return top snippets concatenated
    combined = "\n\n".join([s['text'] for s in sources]) or "No relevant sources found."
    answer = f"(Fallback extract) Relevant content:\n{combined[:2000]}"
    recommendations = ["Review the referenced manuals.", "Practice the procedure in simulations."]

    return {'answer': answer, 'recommendations': recommendations, 'sources': sources}


def generate_debrief(telemetry: Dict[str, Any], transcript: str = "", top_k: int = 6) -> Dict[str, Any]:
    """Generate a debrief given telemetry and optional transcript.

    Returns dict: debrief_text, issues (list), score (float or None), sources (list)
    """
    # Build a short query from telemetry to retrieve context
    query = telemetry.get('summary') if isinstance(telemetry, dict) and telemetry.get('summary') else 'simulator run debrief'

    retrieved = retrieve_relevant_chunks(query, top_k=top_k) or []
    rag_context = build_rag_context(retrieved)

    # Build prompt
    prompt = (
        f"You are an experienced maritime instructor. Given the telemetry and transcript below, and reference materials, produce:\n"
        f"1) A concise performance summary (3-5 sentences).\n2) Top 3 strengths.\n3) Top 3 corrective actions (clear steps).\n4) Any safety-critical flags and immediate recommended actions.\n5) A simple numeric score (0-100).\n\n"
        f"REFERENCE MATERIALS:\n{rag_context}\n---\nTELEMETRY:\n{telemetry}\n---\nTRANSCRIPT:\n{transcript}\n\n"
    )

    llm_text = _call_llm(prompt, max_tokens=1000)

    if llm_text:
        # We won't attempt to robustly parse structured fields; store raw text and no structured score
        return {
            'debrief_text': llm_text,
            'issues': [],
            'score': None,
            'sources': [
                {'id': s['id'], 'source_type': s['source_type'], 'source_id': s['source_id'], 'chunk_index': s['chunk_index'], 'score': s['score']}
                for s in retrieved
            ]
        }

    # Fallback extractive debrief
    snippets = "\n\n".join([s['text'] for s in retrieved]) or "No reference materials found."
    debrief = f"(Fallback debrief) Observations from telemetry: {telemetry}. Reference excerpts:\n{snippets[:2000]}"
    return {'debrief_text': debrief, 'issues': [], 'score': None, 'sources': retrieved}
