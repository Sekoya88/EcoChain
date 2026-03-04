"""EcoChain AI — Streamlit Dashboard (Kodama Grove Theme).

Interface premium thème forêt kodama (21st.dev) : verts profonds, mousse,
glow organique, harmonie visuelle. Loader PrismFlux, upload PDF arbitraire.
"""

from __future__ import annotations

import io
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import httpx
import plotly.graph_objects as go
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MOCK_DATA_DIR = Path("data/mock")
PDF_DATA_DIR = Path("data/pdfs")

# ── Kodama Grove Theme (21st.dev) ──────────────────────
# Deep forest, moss, organic glow, bark — esprit forêt
C = {
    "bg": "#0a0f0a",
    "bg2": "#0f1610",
    "card": "rgba(15, 22, 16, 0.92)",
    "card_solid": "#141c14",
    "glass": "rgba(26, 44, 28, 0.5)",
    "glass_border": "rgba(61, 92, 61, 0.2)",
    "border": "rgba(61, 92, 61, 0.12)",
    "accent": "#5a9c5a",
    "accent2": "#7bc47b",
    "sage": "#8fcf8f",
    "moss": "#4a7c4a",
    "terracotta": "#c9a227",
    "amber": "#c9a227",
    "rose": "#c75d5d",
    "blue": "#6ba3b8",
    "text": "#e2f0e2",
    "text2": "#9fc69f",
    "muted": "#6b8f6b",
    "dim": "#3d5c3d",
    "green_glow": "rgba(90, 156, 90, 0.22)",
    "violet_glow": "rgba(127, 196, 123, 0.15)",
    "cyan_glow": "rgba(107, 163, 184, 0.12)",
    "violet": "#8fcf8f",
    "cyan": "#6ba3b8",
}

AGENT_COLORS = {
    "Orchestrator": C["terracotta"],
    "Extractor": C["blue"],
    "Validator": C["amber"],
    "CarbonCalculator": C["accent"],
    "Recommender": C["sage"],
    "System": C["muted"],
}

PIPELINE_STEPS = ["Extract", "Validate", "Calculate", "Recommend"]


# ═══════════════════════════════════════════════════════
#  CSS — Premium Dark Theme with Glassmorphism & Animations
# ═══════════════════════════════════════════════════════

def get_premium_css() -> str:
    """Return the complete premium CSS stylesheet."""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ── Kodama Grove Global ─────────────────────── */
        .stApp {{
            font-family: 'DM Sans', 'Inter', -apple-system, sans-serif;
            background: {C['bg']};
            color: {C['text']};
        }}

        .stApp > header {{ background: transparent !important; }}

        .block-container {{
            padding-top: 2rem !important;
            max-width: 1100px;
        }}

        html {{ scroll-behavior: smooth; }}

        /* ── Keyframe Animations ─────────────────────── */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes slideInLeft {{
            from {{ opacity: 0; transform: translateX(-20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        @keyframes slideInRight {{
            from {{ opacity: 0; transform: translateX(20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
        }}

        @keyframes glow {{
            0%, 100% {{ box-shadow: 0 0 5px {C['accent']}40, 0 0 10px {C['accent']}20; }}
            50% {{ box-shadow: 0 0 15px {C['accent']}60, 0 0 30px {C['accent']}30; }}
        }}

        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}

        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        @keyframes logSlideIn {{
            from {{ opacity: 0; transform: translateX(-10px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        @keyframes borderGlow {{
            0%, 100% {{ border-color: {C['glass_border']}; }}
            50% {{ border-color: {C['accent']}40; }}
        }}

        /* ── Header ──────────────────────────────────── */
        .eco-header {{
            animation: fadeInUp 0.6s ease-out;
            margin-bottom: 1.5rem;
            position: relative;
        }}

        .eco-header-bg {{
            position: absolute;
            top: -20px; left: -40px; right: -40px;
            height: 120px;
            background: linear-gradient(135deg, {C['accent']}08, {C['violet']}08, {C['cyan']}05);
            border-radius: 0 0 30px 30px;
            filter: blur(20px);
            z-index: -1;
        }}

        .eco-title {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, {C['accent']}, {C['cyan']}, {C['accent2']});
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 4s ease infinite;
            letter-spacing: -0.03em;
            margin-bottom: 0;
            line-height: 1.2;
        }}

        .eco-subtitle {{
            font-size: 0.9rem;
            color: {C['muted']};
            font-weight: 400;
            margin-top: 0.25rem;
            letter-spacing: 0.02em;
        }}

        .eco-status {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.75rem;
            color: {C['muted']};
            margin-top: 0.4rem;
        }}

        .eco-status-dot {{
            width: 7px; height: 7px;
            border-radius: 50%;
            background: {C['accent']};
            animation: pulse 2s ease-in-out infinite;
        }}

        .eco-status-dot.offline {{
            background: {C['rose']};
            animation: none;
        }}

        /* ── Glass Cards ─────────────────────────────── */
        .glass-card {{
            background: {C['card']};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {C['glass_border']};
            border-radius: 16px;
            padding: 1.25rem;
            animation: fadeInUp 0.5s ease-out both;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .glass-card:hover {{
            border-color: {C['accent']}30;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 20px {C['accent']}10;
            transform: translateY(-2px);
        }}

        /* ── Metric Cards ────────────────────────────── */
        .metric-card {{
            background: {C['card']};
            backdrop-filter: blur(20px);
            border: 1px solid {C['glass_border']};
            border-radius: 14px;
            padding: 1.2rem;
            animation: fadeInUp 0.5s ease-out both;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, {C['accent']}, {C['cyan']});
            border-radius: 14px 14px 0 0;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .metric-card:hover::before {{ opacity: 1; }}

        .metric-card:hover {{
            border-color: {C['accent']}25;
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.25);
        }}

        .metric-label {{
            font-size: 0.7rem;
            font-weight: 600;
            color: {C['muted']};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.4rem;
        }}

        .metric-value {{
            font-size: 1.75rem;
            font-weight: 800;
            color: {C['text']};
            letter-spacing: -0.02em;
            line-height: 1.1;
        }}

        .metric-value.accent {{ color: {C['accent']}; }}
        .metric-value.danger {{ color: {C['rose']}; }}
        .metric-value.cyan {{ color: {C['cyan']}; }}
        .metric-value.violet {{ color: {C['violet']}; }}

        .metric-unit {{
            font-size: 0.85rem;
            font-weight: 400;
            color: {C['muted']};
            margin-left: 2px;
        }}

        /* ── Section Titles ──────────────────────────── */
        .section-title {{
            font-size: 0.85rem;
            font-weight: 700;
            color: {C['text2']};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid {C['border']};
            display: flex;
            align-items: center;
            gap: 8px;
            animation: fadeIn 0.4s ease-out;
        }}

        .section-icon {{
            width: 18px; height: 18px;
            border-radius: 5px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
        }}

        /* ── Pipeline Stepper ────────────────────────── */
        .pipeline-stepper {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            padding: 1.2rem 1rem;
            background: {C['card']};
            backdrop-filter: blur(20px);
            border: 1px solid {C['glass_border']};
            border-radius: 16px;
            animation: fadeInUp 0.5s ease-out;
            margin-bottom: 1.5rem;
        }}

        .step {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .step-dot {{
            width: 32px; height: 32px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 700;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }}

        .step-dot.pending {{
            background: {C['dim']};
            color: {C['muted']};
            border: 1px solid {C['border']};
        }}

        .step-dot.active {{
            background: {C['accent']}20;
            color: {C['accent']};
            border: 2px solid {C['accent']};
            animation: glow 2s ease-in-out infinite;
        }}

        .step-dot.done {{
            background: {C['accent']};
            color: #fff;
            border: none;
            box-shadow: 0 2px 8px {C['accent']}40;
        }}

        .step-label {{
            font-size: 0.75rem;
            font-weight: 500;
            color: {C['muted']};
            transition: color 0.3s ease;
        }}

        .step-label.active {{ color: {C['accent']}; font-weight: 600; }}
        .step-label.done {{ color: {C['accent']}; }}

        .step-connector {{
            width: 40px;
            height: 2px;
            background: {C['dim']};
            margin: 0 8px;
            border-radius: 1px;
            transition: background 0.4s ease;
        }}

        .step-connector.done {{
            background: linear-gradient(90deg, {C['accent']}, {C['cyan']});
        }}

        /* ── Log Panel ───────────────────────────────── */
        .log-panel {{
            background: {C['card']};
            backdrop-filter: blur(20px);
            border: 1px solid {C['glass_border']};
            border-radius: 14px;
            padding: 0;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.73rem;
            max-height: 380px;
            overflow-y: auto;
            animation: fadeInUp 0.6s ease-out;
        }}

        .log-panel::-webkit-scrollbar {{
            width: 4px;
        }}
        .log-panel::-webkit-scrollbar-track {{
            background: transparent;
        }}
        .log-panel::-webkit-scrollbar-thumb {{
            background: {C['dim']};
            border-radius: 2px;
        }}

        .log-header {{
            padding: 0.7rem 1rem;
            border-bottom: 1px solid {C['border']};
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            background: {C['card_solid']};
            z-index: 1;
            border-radius: 14px 14px 0 0;
        }}

        .log-header-title {{
            font-size: 0.7rem;
            font-weight: 600;
            color: {C['text2']};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-family: 'Inter', sans-serif;
        }}

        .log-live-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.65rem;
            color: {C['accent']};
            font-weight: 600;
            font-family: 'Inter', sans-serif;
        }}

        .log-live-dot {{
            width: 6px; height: 6px;
            border-radius: 50%;
            background: {C['accent']};
            animation: pulse 1.5s ease-in-out infinite;
        }}

        .log-body {{
            padding: 0.5rem 0;
        }}

        .log-entry {{
            padding: 0.35rem 1rem;
            line-height: 1.5;
            animation: logSlideIn 0.3s ease-out both;
            transition: background 0.2s ease;
            border-left: 2px solid transparent;
        }}

        .log-entry:hover {{
            background: rgba(255,255,255,0.02);
        }}

        .log-agent {{
            font-weight: 600;
            font-size: 0.72rem;
        }}

        .log-msg {{
            color: {C['text2']};
        }}

        .log-duration {{
            color: {C['muted']};
            font-size: 0.68rem;
        }}

        .log-error {{
            color: {C['rose']};
            border-left-color: {C['rose']};
        }}

        .log-empty {{
            padding: 2rem;
            text-align: center;
            color: {C['dim']};
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
        }}

        /* ── Recommendation Cards ────────────────────── */
        .rec-card {{
            background: {C['card']};
            backdrop-filter: blur(20px);
            border: 1px solid {C['glass_border']};
            border-radius: 14px;
            padding: 1.15rem;
            margin-bottom: 0.65rem;
            animation: slideInLeft 0.5s ease-out both;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .rec-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .rec-card:nth-child(3) {{ animation-delay: 0.2s; }}

        .rec-card:hover {{
            border-color: {C['accent']}25;
            transform: translateX(4px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}

        .rec-priority-bar {{
            position: absolute;
            top: 0; left: 0; bottom: 0;
            width: 3px;
            border-radius: 14px 0 0 14px;
        }}

        .rec-priority-1 {{ background: linear-gradient(180deg, {C['rose']}, {C['amber']}); }}
        .rec-priority-2 {{ background: linear-gradient(180deg, {C['amber']}, {C['cyan']}); }}
        .rec-priority-3 {{ background: linear-gradient(180deg, {C['accent']}, {C['cyan']}); }}

        .rec-category {{
            font-size: 0.68rem;
            font-weight: 600;
            color: {C['accent']};
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        .rec-title {{
            font-size: 0.9rem;
            font-weight: 600;
            color: {C['text']};
            margin: 0.2rem 0;
        }}

        .rec-desc {{
            font-size: 0.8rem;
            color: {C['muted']};
            line-height: 1.5;
            margin-top: 0.3rem;
        }}

        .rec-saving {{
            font-size: 1.3rem;
            font-weight: 800;
            background: linear-gradient(135deg, {C['accent']}, {C['cyan']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* ── Sidebar ─────────────────────────────────── */
        section[data-testid="stSidebar"] {{
            background: {C['bg2']} !important;
            border-right: 1px solid {C['border']};
        }}

        section[data-testid="stSidebar"] .stMarkdown {{
            color: {C['text2']};
        }}

        .sidebar-doc-card {{
            background: {C['card']};
            border: 1px solid {C['glass_border']};
            border-radius: 10px;
            padding: 0.8rem;
            margin-bottom: 0.4rem;
            transition: all 0.25s ease;
            cursor: pointer;
        }}

        .sidebar-doc-card:hover {{
            border-color: {C['accent']}30;
            background: {C['glass']};
        }}

        .sidebar-doc-card.selected {{
            border-color: {C['accent']};
            background: {C['green_glow']};
        }}

        .sidebar-doc-name {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {C['text']};
        }}

        .sidebar-doc-detail {{
            font-size: 0.7rem;
            color: {C['muted']};
            margin-top: 0.15rem;
        }}

        /* ── Welcome ─────────────────────────────────── */
        .welcome-container {{
            animation: fadeInUp 0.6s ease-out;
            text-align: center;
            padding: 3rem 1rem;
        }}

        .welcome-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: pulse 3s ease-in-out infinite;
        }}

        .welcome-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {C['text']};
            margin-bottom: 0.5rem;
        }}

        .welcome-desc {{
            font-size: 0.9rem;
            color: {C['muted']};
            line-height: 1.7;
            max-width: 550px;
            margin: 0 auto;
        }}

        .welcome-steps {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }}

        .welcome-step {{
            background: {C['card']};
            backdrop-filter: blur(20px);
            border: 1px solid {C['glass_border']};
            border-radius: 14px;
            padding: 1.5rem 1.2rem;
            width: 160px;
            text-align: center;
            transition: all 0.3s ease;
            animation: fadeInUp 0.5s ease-out both;
        }}

        .welcome-step:nth-child(2) {{ animation-delay: 0.1s; }}
        .welcome-step:nth-child(3) {{ animation-delay: 0.2s; }}

        .welcome-step:hover {{
            transform: translateY(-4px);
            border-color: {C['accent']}30;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}

        .welcome-step-num {{
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {C['accent']}, {C['cyan']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }}

        .welcome-step-text {{
            font-size: 0.8rem;
            color: {C['text2']};
            font-weight: 500;
        }}

        /* ── Buttons override ────────────────────────── */
        .stButton > button {{
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: 0.02em !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 16px rgba(90,156,90,0.25) !important;
        }}

        /* ── File Uploader (Kodama style) ────────────── */
        [data-testid="stFileUploader"] {{
            border: 1px dashed {C['glass_border']} !important;
            border-radius: 12px !important;
            padding: 1.25rem !important;
            background: {C['glass']} !important;
        }}
        [data-testid="stFileUploader"]:hover {{
            border-color: {C['accent']}40 !important;
            background: {C['green_glow']} !important;
        }}

        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {C['accent']}, {C['accent2']}) !important;
            border: none !important;
            color: white !important;
        }}

        /* ── Divider override ────────────────────────── */
        hr {{ border-color: {C['border']} !important; opacity: 0.5; }}

        /* ── Expander override ────────────────────────── */
        .streamlit-expanderHeader {{
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            color: {C['text2']} !important;
        }}

        /* ── PrismFlux-inspired Cube Loader ───────────── */
        .prism-flux-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            min-height: 220px;
            padding: 2rem;
        }}
        .prism-flux-cube {{
            width: 36px;
            height: 36px;
            position: relative;
            transform-style: preserve-3d;
            animation: prismRotate 3s linear infinite;
        }}
        @keyframes prismRotate {{
            0% {{ transform: rotateY(0deg) rotateX(0deg); }}
            100% {{ transform: rotateY(360deg) rotateX(360deg); }}
        }}
        .prism-flux-face {{
            position: absolute;
            width: 36px;
            height: 36px;
            border: 1px solid {C['accent']};
            display: flex;
            align-items: center;
            justify-content: center;
            background: {C['glass']};
            backface-visibility: hidden;
            border-radius: 4px;
        }}
        .prism-flux-face svg {{ width: 14px; height: 14px; color: {C['accent']}; }}
        .prism-flux-face:nth-child(1) {{ transform: rotateY(0deg) translateZ(18px); }}
        .prism-flux-face:nth-child(2) {{ transform: rotateY(180deg) translateZ(18px); }}
        .prism-flux-face:nth-child(3) {{ transform: rotateY(90deg) translateZ(18px); }}
        .prism-flux-face:nth-child(4) {{ transform: rotateY(-90deg) translateZ(18px); }}
        .prism-flux-face:nth-child(5) {{ transform: rotateX(90deg) translateZ(18px); }}
        .prism-flux-face:nth-child(6) {{ transform: rotateX(-90deg) translateZ(18px); }}
        .prism-flux-status {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {C['accent']};
            letter-spacing: 0.05em;
        }}
    </style>
    """


# ═══════════════════════════════════════════════════════
#  Page Setup
# ═══════════════════════════════════════════════════════

def setup_page() -> None:
    """Configure Streamlit page."""
    st.set_page_config(
        page_title="EcoChain AI",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(get_premium_css(), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Header
# ═══════════════════════════════════════════════════════

def render_header() -> None:
    """Render the animated header."""
    # Check backend status
    status_class = "offline"
    status_text = "Offline"
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=2)
        if r.status_code == 200:
            status_class = ""
            status_text = "Connected"
    except Exception:
        pass

    st.markdown(f"""
    <div class="eco-header">
        <div class="eco-header-bg"></div>
        <div class="eco-title">EcoChain AI</div>
        <div class="eco-subtitle">Supply Chain Carbon Footprint Optimizer &mdash; Scope 3 Multi-Agent Analysis</div>
        <div class="eco-status">
            <span class="eco-status-dot {status_class}"></span>
            Backend: {status_text} &middot; AGNO + Gemini 2.5 Flash
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  PDF Extraction
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf. Returns raw text for LLM extraction."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts) if parts else ""
    except Exception as e:
        raise ValueError(f"Failed to extract PDF text: {e}") from e


def build_payload_from_pdf(pdf_bytes: bytes, filename: str) -> dict[str, Any]:
    """Build API payload from PDF: extract text and structure for process endpoint."""
    text = extract_text_from_pdf(pdf_bytes)
    if not text.strip():
        raise ValueError("PDF appears empty or unreadable (no text extracted)")
    return {
        "document_type": "invoice",
        "raw_content": {"raw_text": text},
        "source_filename": filename,
    }


def build_payload_from_json_sidecar(doc: dict[str, Any], pdf_name: str) -> dict[str, Any]:
    """Build payload from pre-existing JSON sidecar (mock/sample docs)."""
    return {
        "document_type": doc.get("document_type", "invoice"),
        "raw_content": doc.get("raw_content", {}),
        "source_filename": pdf_name,
    }


# ═══════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════

def load_mock_documents() -> list[dict[str, Any]]:
    """Load JSON mock documents from data/mock and data/pdfs."""
    documents: list[dict[str, Any]] = []

    for data_dir in [MOCK_DATA_DIR, PDF_DATA_DIR]:
        if not data_dir.exists():
            continue
        for filepath in sorted(data_dir.glob("*.json")):
            try:
                with filepath.open("r", encoding="utf-8") as f:
                    doc = json.load(f)
                    doc["_filename"] = filepath.name
                    doc["_source_dir"] = str(data_dir)
                    documents.append(doc)
            except (json.JSONDecodeError, OSError):
                continue

    return documents


# ═══════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════

def render_sidebar(documents: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Render the sidebar with document selector and PDF upload."""
    with st.sidebar:
        st.markdown(f"""
        <div style="margin-bottom:1rem;">
            <div style="font-size:1.3rem;font-weight:700;color:{C['text']};letter-spacing:-0.02em;">
                Documents
            </div>
            <div style="font-size:0.75rem;color:{C['muted']};margin-top:0.2rem;">
                {len(documents)} documents available
            </div>
        </div>
        """, unsafe_allow_html=True)

        # PDF Upload section
        st.markdown(f"""<div style="font-size:0.7rem;font-weight:600;color:{C['muted']};
            text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.4rem;">
            Upload PDF
        </div>""", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload a logistics PDF",
            type=["pdf"],
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            st.session_state["uploaded_pdf"] = uploaded_file
            st.session_state["uploaded_pdf_name"] = uploaded_file.name
            if st.button("Analyze Uploaded PDF", type="primary", use_container_width=True):
                st.session_state["action"] = "pdf_upload"

        st.markdown("---")

        # Document selector
        st.markdown(f"""<div style="font-size:0.7rem;font-weight:600;color:{C['muted']};
            text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.4rem;">
            Mock Documents
        </div>""", unsafe_allow_html=True)

        if not documents:
            st.warning("No documents found")
            return None

        filenames = [doc.get("_filename", f"doc_{i}") for i, doc in enumerate(documents)]
        selected_idx = st.selectbox(
            "Select document",
            range(len(filenames)),
            format_func=lambda i: filenames[i],
            label_visibility="collapsed",
        )

        selected_doc = documents[selected_idx]
        raw_content = selected_doc.get("raw_content", selected_doc)

        # Document preview card
        if isinstance(raw_content, dict):
            origin = raw_content.get("origin", raw_content.get("origin_warehouse", "--"))
            dest = raw_content.get("destination", raw_content.get("destination_warehouse", "--"))
            weight = raw_content.get("total_weight_kg", raw_content.get("gross_weight_kg", "--"))
            mode = raw_content.get("transport_mode", raw_content.get("transport_type", "--"))

            mode_icons = {"road": "🚛", "maritime": "🚢", "air": "✈️", "rail": "🚆", "river": "🛥️"}
            mode_icon = mode_icons.get(str(mode).lower(), "📦")

            st.markdown(f"""
            <div class="sidebar-doc-card selected">
                <div class="sidebar-doc-name">{mode_icon} {origin} → {dest}</div>
                <div class="sidebar-doc-detail">{weight} kg &middot; {str(mode).upper()}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("Analyze Document", type="primary", use_container_width=True):
            st.session_state["action"] = "single"
            st.session_state["selected_doc"] = selected_doc

        if st.button("Analyze All (Batch)", use_container_width=True):
            st.session_state["action"] = "batch"
            st.session_state["all_docs"] = documents

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.65rem;color:{C['dim']};line-height:1.5;">
            Backend: {BACKEND_URL}<br>
            Engine: AGNO + Gemini 2.5 Flash<br>
            {len(documents)} docs loaded (JSON + PDF)
        </div>
        """, unsafe_allow_html=True)

    return selected_doc


# ═══════════════════════════════════════════════════════
#  Pipeline Stepper
# ═══════════════════════════════════════════════════════

def render_pipeline_stepper(current_step: int = -1) -> None:
    """Render the horizontal pipeline progress indicator."""
    steps_html = []
    for i, step in enumerate(PIPELINE_STEPS):
        if i < current_step:
            dot_cls, label_cls = "done", "done"
            dot_content = "✓"
        elif i == current_step:
            dot_cls, label_cls = "active", "active"
            dot_content = str(i + 1)
        else:
            dot_cls, label_cls = "pending", ""
            dot_content = str(i + 1)

        steps_html.append(f"""
            <div class="step">
                <div class="step-dot {dot_cls}">{dot_content}</div>
                <div class="step-label {label_cls}">{step}</div>
            </div>
        """)

        if i < len(PIPELINE_STEPS) - 1:
            conn_cls = "done" if i < current_step else ""
            steps_html.append(f'<div class="step-connector {conn_cls}"></div>')

    st.markdown(f'<div class="pipeline-stepper">{"".join(steps_html)}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  PrismFlux Loader
# ═══════════════════════════════════════════════════════

PRISM_FLUX_STATUSES = ["Fetching", "Extracting", "Validating", "Calculating", "Recommending", "Syncing"]


def render_prism_flux_loader(status: str = "Processing") -> None:
    """Render PrismFlux-inspired rotating cube loader with status text."""
    plus_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/>'
        '<line x1="5" y1="12" x2="19" y2="12"/></svg>'
    )
    faces = "".join(f'<div class="prism-flux-face">{plus_svg}</div>' for _ in range(6))
    st.markdown(
        f"""
        <div class="prism-flux-container">
            <div class="prism-flux-cube">{faces}</div>
            <div class="prism-flux-status">{status}...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════
#  Metrics
# ═══════════════════════════════════════════════════════

def render_metric_card(label: str, value: str, style: str = "") -> str:
    """Return HTML for a single metric card."""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {style}">{value}</div>
    </div>
    """


def render_metrics(report: dict[str, Any]) -> None:
    """Render the top metrics row."""
    total_co2 = report.get("total_co2_kg", 0)
    shipments = report.get("shipments", [])
    processing_time = report.get("processing_time_ms", 0)
    validation = report.get("validation", {})
    confidence = validation.get("confidence_score", 0)

    co2_style = "accent" if total_co2 < 150 else "danger"
    conf_style = "cyan" if confidence >= 80 else ""

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric_card("Total CO2", f"{total_co2:.1f}<span class='metric-unit'>kgCO2e</span>", co2_style), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card("Shipments", str(len(shipments)), "violet"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card("Confidence", f"{confidence:.0f}<span class='metric-unit'>%</span>", conf_style), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card("Processing", f"{processing_time:.0f}<span class='metric-unit'>ms</span>", ""), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Charts
# ═══════════════════════════════════════════════════════

def render_mode_chart(comparisons: list[dict[str, Any]]) -> None:
    """Render the transport mode comparison bar chart."""
    if not comparisons:
        return

    modes = [c["mode"] for c in comparisons]
    co2_values = [c["co2_kg"] for c in comparisons]
    is_current = [c.get("is_current", False) for c in comparisons]

    mode_labels = {"road": "Road", "maritime": "Maritime", "air": "Air", "rail": "Rail", "river": "River"}
    labels = [mode_labels.get(m, m) for m in modes]

    palette = {
        "current": C["amber"],
        "best": C["accent"],
        "other": C["dim"],
    }

    bar_colors = []
    for co2, current in zip(co2_values, is_current):
        if current:
            bar_colors.append(palette["current"])
        elif co2 == min(co2_values):
            bar_colors.append(palette["best"])
        else:
            bar_colors.append(palette["other"])

    fig = go.Figure(data=[go.Bar(
        x=labels, y=co2_values,
        marker_color=bar_colors,
        marker_line_width=0,
        text=[f"{v:.0f}" for v in co2_values],
        textposition="outside",
        textfont=dict(color=C["text2"], size=11, family="DM Sans"),
        hovertemplate="<b>%{x}</b><br>%{y:.1f} kgCO2e<extra></extra>",
    )])

    fig.update_layout(
        title=dict(text="Emissions by Transport Mode", font=dict(size=13, color=C["text2"], family="DM Sans"), x=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Inter, sans-serif", color=C["muted"]),
        xaxis=dict(gridcolor="rgba(255,255,255,0.03)", showgrid=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="kgCO2e", title_font=dict(size=10)),
        height=340, margin=dict(t=45, b=40, l=50, r=20),
        transition=dict(duration=600, easing="cubic-in-out"),
        bargap=0.35,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_gauge(total_co2: float, benchmark: float = 150.0) -> None:
    """Render the CO2 vs benchmark gauge chart."""
    max_range = max(total_co2, benchmark) * 1.5

    bar_color = C["accent"] if total_co2 <= benchmark else C["rose"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_co2,
        delta={"reference": benchmark, "relative": False, "position": "bottom",
               "font": {"size": 12, "family": "DM Sans"}, "increasing": {"color": C["rose"]}, "decreasing": {"color": C["accent"]}},
        number={"suffix": " kg", "font": {"size": 28, "color": C["text"], "family": "DM Sans"}},
        title={"text": "CO2 vs Sector Benchmark", "font": {"size": 12, "color": C["muted"], "family": "DM Sans"}},
        gauge={
            "axis": {"range": [0, max_range], "tickwidth": 1, "tickcolor": C["dim"], "tickfont": {"size": 9, "color": C["muted"]}},
            "bar": {"color": bar_color, "thickness": 0.65},
            "bgcolor": C["card_solid"],
            "borderwidth": 1, "bordercolor": C["dim"],
            "steps": [
                {"range": [0, benchmark * 0.75], "color": "rgba(90,156,90,0.12)"},
                {"range": [benchmark * 0.75, benchmark], "color": "rgba(201,162,39,0.1)"},
                {"range": [benchmark, max_range], "color": "rgba(199,93,93,0.1)"},
            ],
            "threshold": {"line": {"color": C["rose"], "width": 2.5}, "thickness": 0.75, "value": benchmark},
        },
    ))

    fig.update_layout(
        height=300, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Inter, sans-serif", color=C["muted"]),
        margin=dict(t=35, b=25, l=30, r=30),
    )

    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
#  Recommendations
# ═══════════════════════════════════════════════════════

def render_recommendations(recommendations: list[dict[str, Any]]) -> None:
    """Render recommendation cards with animations."""
    if not recommendations:
        return

    st.markdown(f"""<div class="section-title">
        <span class="section-icon" style="background:{C['green_glow']};color:{C['accent']};">→</span>
        Recommendations
    </div>""", unsafe_allow_html=True)

    for rec in recommendations:
        priority = rec.get("priority", 3)
        saving = rec.get("potential_saving_pct", 0)
        category = rec.get("category", "").replace("_", " ").title()

        st.markdown(f"""
        <div class="rec-card">
            <div class="rec-priority-bar rec-priority-{priority}"></div>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;padding-left:8px;">
                <div style="flex:1;">
                    <div class="rec-category">{category} &middot; P{priority}</div>
                    <div class="rec-title">{rec.get('title', '')}</div>
                    <div class="rec-desc">{rec.get('description', '')}</div>
                </div>
                <div class="rec-saving" style="margin-left:1rem;white-space:nowrap;">-{saving:.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Logs
# ═══════════════════════════════════════════════════════

def fetch_logs() -> list[dict[str, Any]]:
    """Fetch logs from backend API."""
    try:
        r = httpx.get(f"{BACKEND_URL}/api/v1/events/history", timeout=5)
        if r.status_code == 200:
            return r.json().get("events", [])
    except Exception:
        pass
    return []


def stream_sse_logs(log_container, stop_event: threading.Event) -> None:
    """Stream SSE logs in a background thread."""
    try:
        with httpx.stream("GET", f"{BACKEND_URL}/api/v1/events/stream", timeout=None) as response:
            for line in response.iter_lines():
                if stop_event.is_set():
                    break
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") != "heartbeat":
                            if "sse_logs" not in st.session_state:
                                st.session_state["sse_logs"] = []
                            st.session_state["sse_logs"].append(data)
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass


def render_logs(logs: list[dict[str, Any]], is_live: bool = False) -> None:
    """Render the log panel with entries."""
    live_html = ""
    if is_live:
        live_html = '<div class="log-live-badge"><span class="log-live-dot"></span>LIVE</div>'

    if not logs:
        st.markdown(f"""
        <div class="log-panel">
            <div class="log-header">
                <span class="log-header-title">Agent Activity Log</span>
                {live_html}
            </div>
            <div class="log-empty">Waiting for pipeline events...</div>
        </div>
        """, unsafe_allow_html=True)
        return

    lines = []
    for i, log in enumerate(logs):
        agent = log.get("agent", "System")
        msg = log.get("message", "")
        event_type = log.get("type", "info")
        duration = log.get("duration_ms")

        agent_color = AGENT_COLORS.get(agent, C["muted"])
        duration_str = f' <span class="log-duration">[{duration:.0f}ms]</span>' if duration else ""
        error_cls = "log-error" if event_type == "error" else ""

        delay = min(i * 0.05, 1.0)
        lines.append(
            f'<div class="log-entry {error_cls}" style="animation-delay:{delay}s;">'
            f'<span class="log-agent" style="color:{agent_color};">[{agent}]</span> '
            f'<span class="log-msg">{msg}</span>'
            f'{duration_str}'
            f'</div>'
        )

    html = f"""
    <div class="log-panel">
        <div class="log-header">
            <span class="log-header-title">Agent Activity Log</span>
            {live_html}
        </div>
        <div class="log-body">{"".join(lines)}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Reports
# ═══════════════════════════════════════════════════════

def render_single_report(result: dict[str, Any]) -> None:
    """Render a complete carbon report."""
    report = result.get("report", {})
    if not report:
        st.error("Empty report")
        return

    # Pipeline stepper (complete)
    render_pipeline_stepper(current_step=4)

    # Metrics
    render_metrics(report)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Charts
    col_left, col_right = st.columns(2)
    with col_left:
        render_mode_chart(report.get("mode_comparisons", []))
    with col_right:
        render_gauge(total_co2=report.get("total_co2_kg", 0), benchmark=150.0)

    # Recommendations
    render_recommendations(report.get("recommendations", []))

    # Logs
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    logs = fetch_logs()
    render_logs(logs, is_live=False)

    # Raw JSON
    with st.expander("Raw JSON Data", expanded=False):
        st.json(report)


def render_batch_report(result: dict[str, Any]) -> None:
    """Render the batch analysis report."""
    reports = result.get("reports", [])
    total_co2 = result.get("total_co2_kg", 0)

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(render_metric_card("Documents", str(result.get("total_documents", 0)), "violet"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card("Successful", str(result.get("successful", 0)), "accent"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card("Total CO2", f"{total_co2:.1f}<span class='metric-unit'>kgCO2e</span>", ""), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Batch bar chart
    if reports:
        names = [f"Doc {i+1}" for i in range(len(reports))]
        co2_values = [r.get("total_co2_kg", 0) for r in reports]

        bar_colors = [C["accent"] if v < 150 else C["rose"] for v in co2_values]

        fig = go.Figure(data=[go.Bar(
            x=names, y=co2_values,
            marker_color=bar_colors,
            marker_line_width=0,
            text=[f"{v:.0f}" for v in co2_values],
            textposition="outside",
            textfont=dict(color=C["text2"], size=11, family="DM Sans"),
        )])
        fig.update_layout(
            title=dict(text="CO2 Emissions per Document", font=dict(size=13, color=C["text2"], family="Inter"), x=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color=C["muted"]),
            yaxis=dict(title="kgCO2e", gridcolor="rgba(255,255,255,0.04)"),
            xaxis=dict(showgrid=False),
            height=340, margin=dict(t=45, b=40),
            bargap=0.35,
            transition=dict(duration=600),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Logs
    logs = fetch_logs()
    render_logs(logs)

    # Individual reports
    for i, report in enumerate(reports):
        with st.expander(f"Document {i + 1} — {report.get('total_co2_kg', 0):.1f} kgCO2e"):
            render_single_report({"report": report})


# ═══════════════════════════════════════════════════════
#  Welcome Screen
# ═══════════════════════════════════════════════════════

def render_welcome() -> None:
    """Render the welcome landing page."""
    st.markdown(f"""
    <div class="welcome-container">
        <div class="welcome-icon">🌿</div>
        <div class="welcome-title">Ready to Analyze</div>
        <div class="welcome-desc">
            EcoChain AI analyzes logistics documents, calculates Scope 3 carbon emissions
            using ADEME factors, and generates reduction recommendations through a
            multi-agent pipeline powered by AGNO and Gemini 2.5 Flash.
        </div>
        <div class="welcome-steps">
            <div class="welcome-step">
                <div class="welcome-step-num">01</div>
                <div class="welcome-step-text">Select a document<br>or upload a PDF</div>
            </div>
            <div class="welcome-step">
                <div class="welcome-step-num">02</div>
                <div class="welcome-step-text">Click Analyze<br>to run the pipeline</div>
            </div>
            <div class="welcome-step">
                <div class="welcome-step-num">03</div>
                <div class="welcome-step-text">Review report<br>& recommendations</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show any existing logs
    logs = fetch_logs()
    if logs:
        render_logs(logs)


# ═══════════════════════════════════════════════════════
#  Main App
# ═══════════════════════════════════════════════════════

def main() -> None:
    """Main application entry point."""
    setup_page()
    render_header()

    documents = load_mock_documents()
    render_sidebar(documents)

    action = st.session_state.get("action")

    if action == "single" and "selected_doc" in st.session_state:
        doc = st.session_state["selected_doc"]
        st.markdown(f"""<div class="section-title">
            <span class="section-icon" style="background:{C['green_glow']};color:{C['accent']};">◆</span>
            Analysis: {doc.get("_filename", "document")}
        </div>""", unsafe_allow_html=True)

        # Show pipeline stepper + loader
        loader_placeholder = st.empty()
        with loader_placeholder.container():
            render_pipeline_stepper(current_step=0)
            render_prism_flux_loader(status="Processing")

        payload = {
            "document_type": doc.get("document_type", "invoice"),
            "raw_content": doc.get("raw_content", doc),
            "source_filename": doc.get("_filename", "document.json"),
        }

        try:
            with loader_placeholder.container():
                render_pipeline_stepper(current_step=1)
                render_prism_flux_loader(status="Extracting")
            r = httpx.post(f"{BACKEND_URL}/api/v1/documents/process", json=payload, timeout=120)
            result = r.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            result = None

        loader_placeholder.empty()

        if result and result.get("success"):
            render_single_report(result)
        elif result:
            st.error(f"Error: {result.get('error', {}).get('message', 'Unknown error')}")

        st.session_state["action"] = None

    elif action == "batch" and "all_docs" in st.session_state:
        docs = st.session_state["all_docs"]
        st.markdown(f"""<div class="section-title">
            <span class="section-icon" style="background:{C['violet_glow']};color:{C['violet']};">◇</span>
            Batch Analysis: {len(docs)} documents
        </div>""", unsafe_allow_html=True)

        payload = {
            "documents": [
                {
                    "document_type": doc.get("document_type", "invoice"),
                    "raw_content": doc.get("raw_content", doc),
                    "source_filename": doc.get("_filename", "document.json"),
                }
                for doc in docs
            ]
        }

        loader_placeholder = st.empty()
        with loader_placeholder.container():
            render_pipeline_stepper(current_step=1)
            render_prism_flux_loader(status="Batch processing")

        try:
            r = httpx.post(f"{BACKEND_URL}/api/v1/documents/batch", json=payload, timeout=300)
            result = r.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            result = None

        loader_placeholder.empty()
        if result and result.get("success"):
            render_batch_report(result)
        elif result:
            st.error("Batch processing failed")

        st.session_state["action"] = None

    elif action == "pdf_upload" and "uploaded_pdf" in st.session_state:
        uploaded = st.session_state["uploaded_pdf"]
        pdf_name = st.session_state.get("uploaded_pdf_name", "uploaded.pdf")
        pdf_bytes = uploaded.getvalue()

        st.markdown(f"""<div class="section-title">
            <span class="section-icon" style="background:{C['cyan_glow']};color:{C['cyan']};">▲</span>
            PDF Analysis: {pdf_name}
        </div>""", unsafe_allow_html=True)

        # Build payload: prefer JSON sidecar if exists, else extract text from PDF
        payload = None
        json_path = PDF_DATA_DIR / pdf_name.replace(".pdf", ".json")

        try:
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                payload = build_payload_from_json_sidecar(doc, pdf_name)
            else:
                payload = build_payload_from_pdf(pdf_bytes, pdf_name)
        except ValueError as e:
            st.error(str(e))
            st.session_state["action"] = None
            st.stop()

        # Show loader + stepper, then run API call
        loader_placeholder = st.empty()
        with loader_placeholder.container():
            render_pipeline_stepper(current_step=0)
            render_prism_flux_loader(status="Extracting")

        try:
            with loader_placeholder.container():
                render_pipeline_stepper(current_step=1)
                render_prism_flux_loader(status="Validating")
            r = httpx.post(f"{BACKEND_URL}/api/v1/documents/process", json=payload, timeout=120)
            result = r.json()
        except httpx.TimeoutException:
            st.error("Request timed out. The document may be complex—try again.")
            result = None
        except Exception as e:
            st.error(f"API Error: {e}")
            result = None

        loader_placeholder.empty()

        if result and result.get("success"):
            render_single_report(result)
        elif result:
            st.error(f"Error: {result.get('error', {}).get('message', 'Unknown error')}")

        st.session_state["action"] = None

    else:
        render_welcome()


if __name__ == "__main__":
    main()
