"""Centralized theme definitions for the Vehicle Consumption Analyzer.

All CSS, color palettes, and spacing tokens live here.
Import THEME_CSS and inject once via ui.add_css() in layout.
"""

from __future__ import annotations

# ── Color Palette ────────────────────────────────────────────────────────────

LIGHT = {
    "bg": "linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%)",
    "card_bg": "#ffffff",
    "card_border": "#e0e0e0",
    "text_primary": "#1a1a2e",
    "text_secondary": "#555555",
    "text_tertiary": "#888888",
    "accent": "#636EFA",
    "table_header_bg": "#fafafa",
    "table_row_alt": "#fafafa",
    "table_border": "#f0f0f0",
    "expansion_bg": "#f8f9fa",
    "input_border": "#ccc",
    "shadow": "0 2px 12px rgba(0,0,0,0.08)",
    "nav_bg": "#ffffff",
    "nav_shadow": "0 1px 4px rgba(0,0,0,0.08)",
}

DARK = {
    "bg": "linear-gradient(135deg, #121220 0%, #1a1a2e 100%)",
    "card_bg": "#1e1e30",
    "card_border": "#333348",
    "text_primary": "#e0e0e0",
    "text_secondary": "#aaaaaa",
    "text_tertiary": "#777777",
    "accent": "#828cfa",
    "table_header_bg": "#252540",
    "table_row_alt": "#222238",
    "table_border": "#333348",
    "expansion_bg": "#1a1a30",
    "input_border": "#555",
    "shadow": "0 2px 12px rgba(0,0,0,0.3)",
    "nav_bg": "#1e1e30",
    "nav_shadow": "0 1px 4px rgba(0,0,0,0.3)",
}

# ── Spacing Tokens ──────────────────────────────────────────────────────────

SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
}

# ── Shared CSS ───────────────────────────────────────────────────────────────

THEME_CSS = """
/* ── Global ─────────────────────────────────────────────────────────────── */
body {
    min-height: 100vh;
    margin: 0;
    padding: 0;
}

/* ── Navigation Bar ─────────────────────────────────────────────────────── */
.app-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    border-radius: 0 0 12px 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    position: sticky;
    top: 0;
    z-index: 100;
}

.app-nav-title {
    font-size: 1.15em;
    font-weight: 700;
    color: #1a1a2e;
    cursor: pointer;
}

.app-nav-links {
    display: flex;
    gap: 16px;
    align-items: center;
}

.app-nav-link {
    color: #636EFA;
    text-decoration: none;
    font-size: 0.9em;
    font-weight: 500;
    padding: 4px 8px;
    border-radius: 6px;
    transition: background 0.15s;
}

.app-nav-link:hover {
    background: rgba(99, 110, 250, 0.1);
}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.q-card {
    border-radius: 12px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
}

/* ── Table Base ─────────────────────────────────────────────────────────── */
.app-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
    font-family: system-ui, -apple-system, sans-serif;
}

.app-table thead th {
    border-bottom: 2px solid #e0e0e0;
    padding: 8px 6px;
    background: #fafafa;
    color: #555;
    font-weight: 600;
    text-align: left;
    position: sticky;
    top: 0;
}

.app-table tbody td {
    padding: 6px 8px;
    border-bottom: 1px solid #f0f0f0;
}

.app-table tbody tr:nth-child(even) {
    background: #fafafa;
}

.app-table tbody tr:hover {
    background: rgba(99, 110, 250, 0.05);
}

.app-table-vehicle-name {
    font-weight: 600;
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ── Page Container ─────────────────────────────────────────────────────── */
.app-page-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    width: 100%;
}

/* ── Section Headers ────────────────────────────────────────────────────── */
.app-section-title {
    font-size: 1.1em;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 8px;
}

.app-section-subtitle {
    font-size: 0.85em;
    color: #888;
    margin-bottom: 12px;
}

/* ── Summary Cards ──────────────────────────────────────────────────────── */
.app-summary-card {
    min-width: 120px;
    padding: 8px 12px;
    text-align: center;
    border-radius: 8px;
}

.app-summary-card-title {
    font-size: 0.75em;
    color: #888;
    font-weight: 600;
    text-transform: uppercase;
}

.app-summary-card-value {
    font-size: 0.95em;
    font-weight: 700;
}

/* ── Back Link ──────────────────────────────────────────────────────────── */
.app-back-link {
    color: #636EFA;
    text-decoration: none;
    font-size: 0.9em;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.app-back-link:hover {
    text-decoration: underline;
}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .app-page-container {
        padding: 12px;
    }

    .app-nav {
        padding: 8px 12px;
        flex-wrap: wrap;
        gap: 8px;
    }

    .app-nav-links {
        gap: 8px;
    }

    .app-summary-card {
        min-width: 100px;
    }
}
"""

# ── Dark Mode CSS Override ─────────────────────────────────────────────────

DARK_MODE_CSS = """
/* ── Dark Mode Overrides ────────────────────────────────────────────────── */
body.dark-mode {
    background: linear-gradient(135deg, #121220 0%, #1a1a2e 100%) !important;
    color: #e0e0e0;
}

.dark-mode .app-nav {
    background: #1e1e30 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3) !important;
}

.dark-mode .app-nav-title {
    color: #e0e0e0 !important;
}

.dark-mode .q-card {
    background: #1e1e30 !important;
    border-color: #333348 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
}

.dark-mode .app-table thead th {
    background: #252540 !important;
    color: #aaa !important;
    border-bottom-color: #333348 !important;
}

.dark-mode .app-table tbody td {
    border-bottom-color: #333348 !important;
}

.dark-mode .app-table tbody tr:nth-child(even) {
    background: #222238 !important;
}

.dark-mode .app-table tbody tr:hover {
    background: rgba(130, 140, 250, 0.1) !important;
}

.dark-mode .app-section-title {
    color: #e0e0e0 !important;
}

.dark-mode .app-section-subtitle {
    color: #777 !important;
}

.dark-mode .app-back-link {
    color: #828cfa !important;
}

.dark-mode .app-nav-link {
    color: #828cfa !important;
}

.dark-mode .app-nav-link:hover {
    background: rgba(130, 140, 250, 0.15) !important;
}

.dark-mode .app-summary-card-title {
    color: #777 !important;
}

.dark-mode .app-summary-card-value {
    color: #e0e0e0 !important;
}

.dark-mode .q-expansion {
    background: #1a1a30 !important;
}

.dark-mode .q-input,
.dark-mode .q-number,
.dark-mode .q-select {
    color: #e0e0e0 !important;
}

.dark-mode .q-input fieldset,
.dark-mode .q-number fieldset,
.dark-mode .q-select fieldset {
    color: #555 !important;
}
"""
