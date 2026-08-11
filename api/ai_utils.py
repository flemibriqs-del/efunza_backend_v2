import math, logging
from typing import List, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    try:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    except Exception as e:
        logger.error(f"Cosine similarity error: {e}")
        return 0.0


def create_item_attempts(user, assessment, answers: Dict[str, Any]):
    """Create ItemAttempt rows for each question in an assessment.

    answers: mapping of question_id (string) -> submitted answer
    Returns list of created ItemAttempt objects.
    """
    from intelligence.models import ItemAttempt
    from django.utils import timezone

    created = []
    questions = assessment.questions or []

    for idx, q in enumerate(questions):
        q_id = str(q.get('id', idx))
        submitted = answers.get(q_id) if isinstance(answers, dict) else None
        correct = q.get('correct_answer')

        score = None
        try:
            # For MCQ style: exact match
            if submitted is not None and correct is not None:
                score = 1.0 if submitted == correct else 0.0
        except Exception:
            score = 0.0

        attempt = ItemAttempt.objects.create(
            user=user,
            assessment=assessment,
            question_index=idx,
            submitted_answer={'raw': submitted},
            score=score,
            started_at=timezone.now(),
            finished_at=timezone.now(),
            metadata={'question_meta': q}
        )
        created.append(attempt)

    return created


def retrieve_relevant_chunks(query_text: str, top_k: int = 5):
    """Retrieve top-k EmbeddingRecord chunks relevant to query_text using OpenAI embeddings and cosine similarity.

    Returns list of dicts: {id, source_type, source_id, chunk_index, text, score}
    If embeddings or OpenAI not configured, returns empty list.
    """
    try:
        from openai import OpenAI
    except Exception:
        OpenAI = None

    client = None
    if getattr(settings, 'OPENAI_API_KEY', '') and OpenAI is not None:
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            embedding_model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        except Exception as e:
            logger.error(f"OpenAI client init failed: {e}")
            client = None
            embedding_model = None
    else:
        client = None
        embedding_model = None

    if not client or not embedding_model or not query_text:
        return []

    try:
        resp = client.embeddings.create(model=embedding_model, input=query_text)
        q_vec = resp.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed for query: {e}")
        return []

    # Lazy import
    from intelligence.models import EmbeddingRecord

    candidates = EmbeddingRecord.objects.exclude(vector=[]).only('id', 'source_type', 'source_id', 'chunk_index', 'text', 'vector')

    scored = []
    for c in candidates:
        try:
            vec = c.vector or []
            if not vec:
                continue
            score = _cosine_similarity(q_vec, vec)
            scored.append((score, c))
        except Exception as e:
            logger.error(f"Scoring failed for embedding {c.id}: {e}")

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, c in scored[:top_k]:
        results.append({
            'id': c.id,
            'source_type': c.source_type,
            'source_id': c.source_id,
            'chunk_index': c.chunk_index,
            'text': (c.text or '')[:2000],
            'score': float(score),
        })

    return results


def build_rag_context(retrieved: List[Dict[str, Any]], max_chars: int = 8000) -> str:
    pieces = []
    total = 0
    for r in retrieved:
        t = r.get('text', '') or ''
        if not t:
            continue
        if total + len(t) > max_chars:
            # truncate remaining part
            remaining = max_chars - total
            if remaining <= 0:
                break
            t = t[:remaining]
        pieces.append(f"Source ({r.get('source_type')}:{r.get('source_id')}#{r.get('chunk_index')}):\n{t}\n")
        total += len(t)
    return "\n\n".join(pieces)
