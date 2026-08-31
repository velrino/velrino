# /// script
# requires-python = ">=3.11"
# dependencies = ["diagrams>=0.25,<0.26", "pillow>=11,<13"]
# ///
"""Render the AdaptaMidia production architecture.

Run from any directory:

    uv run diagrams/adapta-midia/architecture.py

The script writes PNG and SVG versions beside itself and publishes the PNG to
``assets/adapta-midia/architecture.png`` for the profile README.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAGRAMS_ROOT = ROOT.parent
PROJECT_ROOT = ROOT.parents[1]
sys.path.insert(0, str(DIAGRAMS_ROOT))

from _shared.theme import (
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
    RED,
    TEAL,
    card,
    flow,
    panel,
    pulse,
    render_slide,
)
from diagrams.firebase.base import Firebase
from diagrams.gcp.compute import Run
from diagrams.gcp.ml import VertexAI, VisionAPI
from diagrams.gcp.storage import GCS
from diagrams.onprem.database import MongoDB
from diagrams.onprem.inmemory import Redis
from diagrams.programming.framework import Flutter, React
from diagrams.programming.language import NodeJS
from diagrams.saas.cdn import Cloudflare


def build_graph() -> None:
    with panel("EXPERIENCES", rank="same"):
        mobile = card(Flutter, "Edge vision app", "Flutter · Android")
        edge_inference = card(VisionAPI, "YOLO inference", "on-device · privacy-first")
        dashboard = card(React, "Admin dashboard", "React · Vercel")

        (
            mobile
            >> flow(TEAL, label="camera frames", constraint="false")
            >> edge_inference
        )

    with panel("EDGE"):
        cloudflare = card(Cloudflare, "Cloudflare", "DNS · CDN · TLS · protection")

    with panel("GOOGLE CLOUD"):
        api = card(Run, "AdaptaMidia API", "NestJS · Cloud Run")
        jobs = card(NodeJS, "Campaign workers", "analytics · optimization")

        api >> flow(ORANGE, label="async jobs") >> jobs

    with panel("IDENTITY + AI", rank="same"):
        firebase = card(Firebase, "Firebase", "auth · realtime sync")
        vertex = card(VertexAI, "Vertex AI", "audience intelligence")

    with panel("DATA + MEDIA", rank="same"):
        storage = card(GCS, "Cloud Storage", "media · processed outputs")
        mongo = card(MongoDB, "MongoDB", "campaigns · audience insights")
        redis = card(Redis, "Redis", "cache · job queue")

    # Both product surfaces cross the same protected edge before the API.
    mobile >> flow(label="events") >> cloudflare
    dashboard >> flow(label="API requests") >> cloudflare
    cloudflare >> flow(label="HTTPS", weight="8") >> api

    # Cloud Run is the synchronous spine; each color names a concern.
    api >> flow(BLUE, label="auth · realtime") >> firebase
    api >> flow(PURPLE, label="managed inference") >> vertex
    jobs >> flow(GREEN, label="reads · writes") >> mongo
    jobs >> flow(RED, label="cache · queue") >> redis
    jobs >> flow(ORANGE, label="media") >> storage

    # Edge detections become aggregate events; raw camera frames stay local.
    edge_inference >> pulse(TEAL, label="anonymous signals", constraint="false") >> api
    jobs >> pulse(PURPLE, label="AI optimization", constraint="false") >> vertex


render_slide(
    root=ROOT,
    title="AdaptaMidia · Production Architecture",
    subtitle="Privacy-first edge vision turns real-world attention into measurable campaign intelligence",
    aria_label="AdaptaMidia production architecture",
    build_graph=build_graph,
    asset_output=PROJECT_ROOT / "assets" / "adapta-midia" / "architecture.png",
)
