"""
Llama-3 alert explainer.

Builds a structured prompt from a flagged transaction and the rules that fired,
asks Llama-3 (via Ollama) to explain in plain analyst-friendly English why the
transaction is suspicious and what to check next, then caches the result on the
alert so repeat requests are free.

The model only *describes* findings — it never decides risk. All risk signals
come from the deterministic rule engine.
"""
from django.utils import timezone

from .ollama_client import OllamaError, generate

SYSTEM_PROMPT = (
    "You are a financial fraud analyst assistant. You explain, in clear and "
    "concise plain English, why a transaction was flagged based ONLY on the "
    "signals provided. Do not invent facts beyond the given signals. Keep it "
    "to a short paragraph followed by 2-3 recommended next actions as a bullet "
    "list."
)


class ExplanationError(Exception):
    """Raised when an explanation could not be generated."""


def _build_prompt(alert) -> str:
    txn = alert.transaction
    facts = [
        f"- Amount: {txn.amount} {txn.currency}",
        f"- Merchant: {txn.merchant or 'unknown'} (category: {txn.category or 'n/a'})",
        f"- Country: {txn.country or 'n/a'}, Channel: {txn.channel or 'n/a'}",
        f"- Time: {txn.timestamp.isoformat()}",
        f"- Card: ••{txn.card_last4 or '????'}, Customer: {txn.customer_id or 'n/a'}",
        f"- Computed risk score: {alert.risk_score}/100",
    ]
    triggered = [
        f"- {hit.rule_label} (+{hit.weight}): {hit.detail}"
        for hit in alert.rule_hits.all()
    ]
    return (
        "A transaction was flagged by our rule-based fraud engine.\n\n"
        "Transaction details:\n" + "\n".join(facts) + "\n\n"
        "Rules that fired:\n" + ("\n".join(triggered) or "- (none)") + "\n\n"
        "Explain why this looks suspicious and what the analyst should do next."
    )


def explain_alert(alert, *, force: bool = False) -> str:
    """Return the alert's explanation, generating and caching it if needed."""
    if alert.ai_explanation and not force:
        return alert.ai_explanation

    try:
        explanation = generate(_build_prompt(alert), system=SYSTEM_PROMPT)
    except OllamaError as exc:
        raise ExplanationError(str(exc)) from exc

    alert.ai_explanation = explanation
    alert.ai_explained_at = timezone.now()
    alert.save(update_fields=["ai_explanation", "ai_explained_at"])
    return explanation
