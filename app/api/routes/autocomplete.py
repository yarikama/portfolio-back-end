import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from api.dependencies import CurrentAdmin
from core import config
from db.dependency import get_db
from db.models.autocomplete import AutocompleteSuggestion
from fastapi import APIRouter, Depends, HTTPException, Response
from schemas.autocomplete import (
    CompletionRequest,
    CompletionResponse,
    SuggestionFeedback,
)
from services import autocomplete
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/admin/complete")
async def complete(
    request: CompletionRequest,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Suggest how the note continues from the cursor.

    Every failure degrades to "no suggestion": the editor must keep working
    whatever happens to the model, and the model has its own alert.
    """
    if not config.AUTOCOMPLETE_URL:
        raise HTTPException(status_code=503, detail="Autocomplete is not configured")

    empty = {
        "data": CompletionResponse(id=None, suggestion="").model_dump(by_alias=True)
    }
    prompt = autocomplete.build_prompt(request.prefix, request.title)
    if not request.prefix.strip():
        return empty

    try:
        completion = await autocomplete.complete(prompt.text)
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as err:
        logger.warning("autocomplete request failed: %s", err)
        return empty

    suggestion = autocomplete.shape_suggestion(
        completion.tokens, prompt.trailing_space, config.AUTOCOMPLETE_MIN_TOKEN_PROB
    )
    if not suggestion:
        return empty

    row = AutocompleteSuggestion(
        model_version=config.AUTOCOMPLETE_MODEL_VERSION,
        note_id=request.note_id,
        prompt=prompt.text,
        completion=completion.text,
        suggestion=suggestion,
        tokens=[[token, logprob] for token, logprob in completion.tokens],
        latency_ms=completion.latency_ms,
    )
    db.add(row)
    db.commit()
    return {
        "data": CompletionResponse(id=row.id, suggestion=suggestion).model_dump(
            by_alias=True, mode="json"
        )
    }


@router.post("/admin/complete/{id}/feedback", status_code=204)
async def feedback(
    id: UUID,
    body: SuggestionFeedback,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Record what became of a suggestion. Only the first report counts."""
    row = db.get(AutocompleteSuggestion, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if row.outcome is None:
        row.outcome = body.outcome
        row.accepted_chars = body.accepted_chars
        row.resolved_at = datetime.now(timezone.utc)
        db.commit()
    return Response(status_code=204)
