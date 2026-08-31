# /// script
# requires-python = ">=3.11"
# dependencies = ["diagrams>=0.25,<0.26", "pillow>=11,<13"]
# ///
"""Render the GoatVPN production architecture.

Run from any directory:

    uv run diagrams/goatvpn/architecture.py

The script writes PNG and SVG versions beside itself and publishes the PNG to
``assets/goatvpn/architecture.png`` for the profile README.
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
    RED,
    TEAL,
    card,
    flow,
    panel,
    pulse,
    render_slide,
)
from diagrams.aws.compute import ECS
from diagrams.gcp.operations import Monitoring
from diagrams.generic.network import VPN
from diagrams.generic.os import IOS, Android
from diagrams.onprem.client import Client
from diagrams.onprem.compute import Server
from diagrams.onprem.database import MongoDB
from diagrams.onprem.inmemory import Redis
from diagrams.programming.framework import React
from diagrams.saas.payment import Stripe

from diagrams import Edge


def build_graph() -> None:
    with panel("CLIENTS"):
        ios = card(IOS, "iOS app", "React Native")
        android = card(Android, "Android app", "React Native")
        web = card(React, "Web client", "React")
        extension = card(Client, "Browser extension", "Plasmo")

    with panel("AWS CONTROL PLANE"):
        api = card(ECS, "GoatVPN API", "NestJS · AWS")
        provisioning = card(VPN, "Provisioning service", "configs · server metadata")

        api >> flow(TEAL, label="issue config", weight="5") >> provisioning

    with panel("DATA"):
        mongo = card(MongoDB, "MongoDB Atlas", "users · subscriptions · servers")
        redis = card(Redis, "Redis", "cache · queues")

    with panel("BILLING"):
        payments = card(Stripe, "Payment gateways", "Stripe · Cryptomus · NoxPay")

    with panel("GROWTH + OPERATIONS"):
        operations = card(
            Monitoring,
            "Growth + observability",
            "GTM · Meta · New Relic · Slack",
        )

    with panel("VPN SERVER FLEET"):
        wireguard = card(VPN, "WireGuard", "encrypted client tunnels")
        dashboard = card(VPN, "WGDashboard", "fleet control")
        datapacket = card(Server, "DataPacket", "VPN servers")
        is_hosting = card(Server, "IS Hosting", "VPN servers")

        wireguard >> flow(TEAL, label="route") >> dashboard
        dashboard >> flow(TEAL, label="provision") >> datapacket
        dashboard >> flow(TEAL) >> is_hosting

    # Every client consumes one API surface for auth, subscriptions and config.
    ios >> flow(label="API") >> api
    android >> flow(label="API") >> api
    web >> flow(label="API") >> api
    extension >> flow(label="API") >> api

    # The API owns business state, resilient billing and the fleet control plane.
    api >> flow(GREEN, label="reads · writes") >> mongo
    api >> flow(RED, label="cache · jobs") >> redis
    api >> flow(PURPLE, label="billing") >> payments
    api >> pulse(ORANGE, label="events · metrics") >> operations
    provisioning >> flow(TEAL, label="manage fleet", weight="5") >> wireguard

    # Invisible layout guides distribute the business services across columns
    # instead of stacking every API dependency into one tall leaf column.
    mongo >> Edge(style="invis", weight="10") >> payments
    payments >> Edge(style="invis", weight="10") >> operations


render_slide(
    root=ROOT,
    title="GoatVPN · Production Architecture",
    subtitle="One control plane for subscriptions, per-user WireGuard configs and a multi-provider VPN fleet",
    aria_label="GoatVPN production architecture",
    build_graph=build_graph,
    asset_output=PROJECT_ROOT / "assets" / "goatvpn" / "architecture.png",
)
