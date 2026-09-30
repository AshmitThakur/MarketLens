"""Grounded MarketLens prompt construction kept outside HTTP routes."""

import json
from typing import Any


SYSTEM_PROMPT = """You are the strategy copilot for MarketLens, a retail expansion analytics application.

All numerical facts must come from the structured MarketLens context supplied with the request. Never calculate, alter, or invent metrics. Do not introduce company information, revenue, profit, margins, population, demographics, competition, real-estate costs, logistics costs, market size, or any other unavailable facts.

The opportunity score is a transparent prioritization model, not a prediction or definitive store-opening recommendation. Do not claim causal relationships. Clearly distinguish what the data shows from what management may consider. Use concise management-oriented language. When evidence is insufficient, explicitly say that MarketLens cannot answer from its current data.
"""


def _context_block(context: dict[str, Any]) -> str:
    return json.dumps(context, indent=2, ensure_ascii=False)


def executive_insights_prompt(context: dict[str, Any]) -> str:
    return f"""Create a concise executive interpretation of the current MarketLens top-five ranking.

Explain the strongest observable signals, trade-offs, and prudent next investigation steps. Explicitly acknowledge the supplied limitations. Phrase opportunities as candidates for further evaluation, never directives to open stores.

MARKETLENS_CONTEXT:
{_context_block(context)}"""


def city_comparison_prompt(context: dict[str, Any]) -> str:
    return f"""Compare the two supplied cities under the current MarketLens weights.

Explain why their overall scores differ by referring to their actual raw metrics and percentile component scores. Separate analytical observations from management interpretation. Do not infer facts outside the supplied context.

MARKETLENS_CONTEXT:
{_context_block(context)}"""


def ask_marketlens_prompt(question: str, context: dict[str, Any]) -> str:
    return f"""Answer the user's analytical question using only the supplied MarketLens context.

If the answer is not supported by this dataset, say so directly. Do not answer from general knowledge. Do not make definitive opening recommendations. Include a caveat when the answer could be misread as a prediction or investment recommendation.

USER_QUESTION:
{question}

MARKETLENS_CONTEXT:
{_context_block(context)}"""
