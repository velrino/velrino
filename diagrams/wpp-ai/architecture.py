# /// script
# requires-python = ">=3.11"
# dependencies = ["diagrams>=0.25,<0.26", "pillow>=11,<13"]
# ///
"""Render the WPP AI production architecture.

Run from any directory:

    uv run diagrams/wpp-ai/architecture.py

The script writes PNG and SVG versions beside itself and publishes the PNG to
``assets/wpp-ai/architecture.png`` for the profile README.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAGRAMS_ROOT = ROOT.parent
PROJECT_ROOT = ROOT.parents[1]
sys.path.insert(0, str(DIAGRAMS_ROOT))

from _shared.theme import (
    GREEN,
    ORANGE,
    PURPLE,
    card,
    flow,
    panel,
    pulse,
    render_slide,
)
from diagrams.gcp.ml import AIPlatform, VertexAI
from diagrams.onprem.client import Users
from diagrams.onprem.database import MongoDB
from diagrams.onprem.inmemory import Redis
from diagrams.programming.flowchart import Action, Decision
from diagrams.programming.framework import React
from diagrams.programming.language import NodeJS


def build_graph() -> None:
    with panel("CHANNELS + ADMIN"):
        whatsapp = card(Users, "WhatsApp", "users · groups")
        admin = card(React, "Admin frontend", "conversations · AI audits")

    with panel("WHATSAPP RUNTIME"):
        baileys = card(NodeJS, "Baileys adapter", "send · receive · media")
        mapper = card(Action, "Message mapper", "normalize · route")
        sender = card(NodeJS, "Reply sender", "quoted replies")

        baileys >> flow(GREEN, label="normalize") >> mapper

    with panel("NESTJS API", rank="same"):
        api = card(NodeJS, "WPP AI API", "auth · orchestration")
        tenant = card(Users, "Tenant resolver", "tenant · account · bot profile")

        api >> flow(GREEN, label="resolve context", constraint="false") >> tenant

    with panel("PERSISTENCE"):
        mongo = card(MongoDB, "MongoDB", "tenants · conversations · audits")

    with panel("QUEUE + WORKERS"):
        reviewers = card(Decision, "Deterministic review", "guardrails before LLM")
        queue = card(Redis, "Redis + Bull", "priority · retries · jobs")
        processor = card(NodeJS, "LLM processor", "evidence · provider routing")

        reviewers >> flow(ORANGE, label="enqueue") >> queue
        queue >> flow(ORANGE, label="process") >> processor

    with panel("AI + GUARDRAILS", rank="same"):
        guardrails = card(Decision, "Output guardrails", "validate · safe reply")
        gemini = card(VertexAI, "Gemini", "primary · Vertex AI")
        openai = card(AIPlatform, "OpenAI", "provider fallback")

        guardrails >> flow(PURPLE, label="primary", constraint="false") >> gemini
        guardrails >> pulse(ORANGE, label="fallback", constraint="false") >> openai

    # Incoming messages and admin reads converge on the tenant-aware API.
    whatsapp >> flow(GREEN, label="messages") >> baileys
    mapper >> flow(GREEN, label="normalized event", weight="6") >> api
    admin >> flow(GREEN, label="auth · conversations") >> api

    # Context is resolved before persistence or asynchronous AI execution.
    tenant >> flow(GREEN, label="record · query") >> mongo
    api >> flow(ORANGE, label="review · queue") >> reviewers
    processor >> flow(PURPLE, label="prompt · validate", weight="5") >> guardrails
    processor >> pulse(GREEN, label="audit snapshot", constraint="false") >> mongo

    # The validated response returns through the same WhatsApp account adapter.
    processor >> pulse(GREEN, label="validated reply", constraint="false") >> sender
    sender >> pulse(GREEN, label="send reply", constraint="false") >> whatsapp


render_slide(
    root=ROOT,
    title="WPP AI · Production Architecture",
    subtitle="Multi-tenant WhatsApp support with deterministic review, queued LLM analysis and provider fallback",
    aria_label="WPP AI production architecture",
    build_graph=build_graph,
    asset_output=PROJECT_ROOT / "assets" / "wpp-ai" / "architecture.png",
)
