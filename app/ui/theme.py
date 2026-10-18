"""Centralized theme definitions for the Vehicle Consumption Analyzer.

All CSS, color palettes, and spacing tokens live here.
Import THEME_CSS and inject once via ui.add_css() in layout.

Design direction (2026-10 refresh): modern, calm, icon-driven.
- System font stack (no external fonts: the app must work offline on LAN)
- Slate/indigo palette, soft cool surfaces, one accent color
- Icon chips for brand, sections and stats; pill navigation
- Soft layered shadows, 16px card radius, tabular numerals in tables
"""

from __future__ import annotations

# ── Color Palette ────────────────────────────────────────────────────────────

LIGHT = {
    "bg": "linear-gradient(160deg, #f6f7fb 0%, #eef1f8 100%)",
    "card_bg": "#ffffff",
    "card_border": "rgba(15, 23, 42, 0.07)",
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "text_tertiary": "#94a3b8",
    "accent": "#6366f1",
    "accent_soft": "#eef2ff",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "table_header_bg": "#f8fafc",
    "table_row_alt": "#f8fafc",
    "table_border": "#eef2f6",
    "expansion_bg": "#f8fafc",
    "input_border": "#cbd5e1",
    "shadow": "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.06)",
    "nav_bg": "rgba(255, 255, 255, 0.92)",
    "nav_shadow": "0 1px 0 rgba(15,23,42,0.06), 0 4px 16px rgba(15,23,42,0.05)",
}

DARK = {
    "bg": "linear-gradient(160deg, #0b1020 0%, #10162b 100%)",
    "card_bg": "#141a2e",
    "card_border": "rgba(148, 163, 184, 0.14)",
    "text_primary": "#e5e7eb",
    "text_secondary": "#94a3b8",
    "text_tertiary": "#64748b",
    "accent": "#818cf8",
    "accent_soft": "rgba(129, 140, 248, 0.14)",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#f87171",
    "table_header_bg": "#1a2138",
    "table_row_alt": "#181f36",
    "table_border": "rgba(148, 163, 184, 0.12)",
    "expansion_bg": "#181f36",
    "input_border": "#334155",
    "shadow": "0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.35)",
    "nav_bg": "rgba(20, 26, 46, 0.92)",
    "nav_shadow": "0 1px 0 rgba(148,163,184,0.12), 0 4px 16px rgba(0,0,0,0.25)",
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
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter",
        "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

/* ── Navigation Bar ─────────────────────────────────────────────────────── */
.app-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    border-radius: 0 0 16px 16px;
    box-shadow: 0 1px 0 rgba(15,23,42,0.06), 0 4px 16px rgba(15,23,42,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

.app-nav-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    text-decoration: none;
}

.app-nav-brand-icon {
    width: 32px;
    height: 32px;
    border-radius: 10px;
    display: inline-block;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.35);
    flex-shrink: 0;
}

.app-nav-title {
    font-size: 1.02em;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
    white-space: nowrap;
}

.app-nav-links {
    display: flex;
    gap: 4px;
    align-items: center;
}

.app-nav-link {
    color: #475569;
    text-decoration: none;
    font-size: 0.86em;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 999px;
    transition: background 0.15s, color 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}

.app-nav-link:hover {
    background: rgba(99, 102, 241, 0.08);
    color: #6366f1;
}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.q-card {
    border-radius: 16px !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.06) !important;
    border: 1px solid rgba(15, 23, 42, 0.07) !important;
    background: #ffffff !important;
}

/* ── Stat Strip (dashboard overview) ────────────────────────────────────── */
.app-stat-strip {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.app-stat {
    flex: 1 1 150px;
    display: flex;
    align-items: center;
    gap: 12px;
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.07);
    border-radius: 14px;
    padding: 10px 14px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    min-width: 0;
}

.app-stat-icon {
    width: 36px;
    height: 36px;
    border-radius: 11px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: #eef2ff;
    color: #6366f1;
    flex-shrink: 0;
}

.app-stat-value {
    font-size: 1.05em;
    font-weight: 800;
    letter-spacing: -0.01em;
    font-variant-numeric: tabular-nums;
    color: #0f172a;
    line-height: 1.2;
}

.app-stat-label {
    font-size: 0.7em;
    color: #94a3b8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Icon Chips (section headers) ───────────────────────────────────────── */
.section-icon {
    width: 26px;
    height: 26px;
    border-radius: 8px;
    background: #eef2ff;
    color: #6366f1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    flex-shrink: 0;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: 0.95em;
    color: #0f172a;
    margin-bottom: 8px;
}

/* ── Ranking (medals, rows, type badges) ────────────────────────────────── */
.rank-medal {
    font-weight: 800;
    width: 28px;
    text-align: center;
    font-variant-numeric: tabular-nums;
    font-size: 0.9em;
}

.rank-medal-1 { color: #d97706; }
.rank-medal-2 { color: #64748b; }
.rank-medal-3 { color: #b45309; }

.rank-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-bottom: 1px solid #eef2f6;
    border-radius: 8px;
    margin-bottom: 4px;
    background: #f8fafc;
    flex-wrap: wrap;
}

.rank-value-ev { color: #16a34a; }
.rank-value-ice { color: #dc2626; }

.rank-badge {
    min-width: 28px;
    font-size: 0.7em;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 999px;
    text-align: center;
}

.rank-badge-ev { background: rgba(22, 163, 74, 0.12); color: #16a34a; }
.rank-badge-ice { background: rgba(220, 38, 38, 0.10); color: #dc2626; }

/* ── Table Base ─────────────────────────────────────────────────────────── */
.app-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
    font-variant-numeric: tabular-nums;
    font-family: inherit;
}

.app-table thead th {
    border-bottom: 2px solid #e2e8f0;
    padding: 8px 6px;
    background: #f8fafc;
    color: #475569;
    font-weight: 700;
    text-align: left;
    position: sticky;
    top: 0;
}

.app-table tbody td {
    padding: 6px 8px;
    border-bottom: 1px solid #eef2f6;
}

.app-table tbody tr:nth-child(even) {
    background: #f8fafc;
}

.app-table tbody tr:hover {
    background: rgba(99, 102, 241, 0.05);
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

/* ── Filter Bar (compare tab) ───────────────────────────────────────────── */
.app-filter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 16px;
    margin-bottom: 12px;
    background: #f8fafc;
    border-radius: 14px;
    flex-wrap: wrap;
    border: 1px solid rgba(15, 23, 42, 0.07);
}

/* ── Section Headers ────────────────────────────────────────────────────── */
.app-section-title {
    font-size: 1.1em;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
}

.app-section-subtitle {
    font-size: 0.85em;
    color: #94a3b8;
    margin-bottom: 12px;
}

/* ── Summary Cards (route results) ──────────────────────────────────────── */
.app-summary-card {
    min-width: 120px;
    padding: 8px 12px;
    text-align: center;
    border-radius: 10px;
}

.app-summary-card-title {
    font-size: 0.72em;
    color: #94a3b8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.app-summary-card-value {
    font-size: 0.95em;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    color: #0f172a;
}

/* ── Back Link ──────────────────────────────────────────────────────────── */
.app-back-link {
    color: #6366f1;
    text-decoration: none;
    font-size: 0.9em;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.app-back-link:hover {
    text-decoration: underline;
}

/* ── Responsive Layout Primitives ───────────────────────────────────────── */
.compare-row {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: stretch;
    width: 100%;
}

.compare-selector-card {
    min-width: 280px;
    max-width: 320px;
    flex: 1;
}

.compare-chart-card {
    flex: 3;
    min-width: 400px;
}

.chart-container {
    width: 100%;
    min-height: 420px;
}

.route-map {
    height: 400px;
}

/* ── Vehicle Detail (native) ────────────────────────────────────────────── */
.detail-grid {
    display: flex;
    gap: 16px;
    align-items: stretch;
    flex-wrap: wrap;
}

.detail-col {
    flex: 1 1 340px;
    min-width: 0;
}

.detail-img {
    width: 240px;
    height: 160px;
    border-radius: 10px;
    overflow: hidden;
    flex-shrink: 0;
    background: #f1f5f9;
}

.detail-row {
    padding: 6px 0;
    border-bottom: 1px solid #eef2f6;
}

.detail-label {
    font-weight: 600;
    font-size: 0.88em;
    color: #475569;
}

.detail-value {
    font-size: 0.88em;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    color: #0f172a;
}

.detail-header {
    font-weight: 700;
    font-size: 1em;
    padding-bottom: 6px;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 6px;
    color: #0f172a;
}

.detail-sub {
    font-size: 0.82em;
    color: #64748b;
}

.detail-missing {
    font-size: 0.72em;
    color: #dc2626;
    font-weight: 700;
}

.detail-notes {
    font-size: 0.88em;
    color: #475569;
}

/* Tablet: stack the compare layout vertically, keep other two-column areas */
@media (max-width: 900px) {
    .compare-row {
        flex-direction: column;
    }

    .compare-selector-card {
        min-width: 0;
        max-width: none;
    }

    .compare-chart-card {
        min-width: 0;
    }
}

/* ── Responsive (mobile) ────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .app-page-container {
        padding: 8px;
    }

    .app-nav {
        padding: 8px 10px;
        flex-direction: column;
        gap: 6px;
        align-items: stretch;
    }

    .app-nav-brand {
        justify-content: center;
    }

    .app-nav-title {
        text-align: center;
        font-size: 1em;
    }

    .app-nav-links {
        justify-content: center;
        gap: 4px;
        flex-wrap: wrap;
    }

    .app-nav-link {
        font-size: 0.82em;
        padding: 4px 8px;
    }

    .app-summary-card {
        min-width: 100px;
    }

    .app-stat {
        flex: 1 1 45%;
    }

    .chart-container {
        min-height: 300px;
    }

    .route-map {
        height: 300px;
    }

    /* Vehicle detail: image on top, specs below */
    .detail-card {
        flex-direction: column !important;
        gap: 12px !important;
    }

    .detail-img {
        width: 100% !important;
        height: auto !important;
        aspect-ratio: 3 / 2;
    }
}
"""

# ── Dark Mode CSS Override ─────────────────────────────────────────────────

DARK_MODE_CSS = """
/* ── Dark Mode Overrides ────────────────────────────────────────────────── */
body.dark-mode {
    background: linear-gradient(160deg, #0b1020 0%, #10162b 100%) !important;
    color: #e5e7eb;
}

.dark-mode .app-nav {
    background: rgba(20, 26, 46, 0.92) !important;
    box-shadow: 0 1px 0 rgba(148,163,184,0.12), 0 4px 16px rgba(0,0,0,0.25) !important;
}

.dark-mode .app-nav-title {
    color: #e5e7eb !important;
}

.dark-mode .app-nav-link {
    color: #94a3b8 !important;
    background: transparent !important;
}

.dark-mode .app-nav-link:hover {
    background: rgba(129, 140, 248, 0.12) !important;
    color: #818cf8 !important;
}

.dark-mode .q-card {
    background: #141a2e !important;
    border-color: rgba(148, 163, 184, 0.14) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.35) !important;
}

.dark-mode .app-stat {
    background: #141a2e !important;
    border-color: rgba(148, 163, 184, 0.14) !important;
}

.dark-mode .app-stat-icon {
    background: rgba(129, 140, 248, 0.14) !important;
    color: #818cf8 !important;
}

.dark-mode .app-stat-value {
    color: #e5e7eb !important;
}

.dark-mode .app-stat-label {
    color: #64748b !important;
}

.dark-mode .section-icon {
    background: rgba(129, 140, 248, 0.14) !important;
    color: #818cf8 !important;
}

.dark-mode .section-header {
    color: #e5e7eb !important;
}

.dark-mode .app-table thead th {
    background: #1a2138 !important;
    color: #94a3b8 !important;
    border-bottom-color: rgba(148, 163, 184, 0.14) !important;
}

.dark-mode .app-table tbody td {
    border-bottom-color: rgba(148, 163, 184, 0.12) !important;
}

.dark-mode .app-table tbody tr:nth-child(even) {
    background: #181f36 !important;
}

.dark-mode .app-table tbody tr:hover {
    background: rgba(129, 140, 248, 0.1) !important;
}

.dark-mode .app-section-title {
    color: #e5e7eb !important;
}

.dark-mode .app-filter-bar {
    background: #181f36 !important;
    border-color: rgba(148, 163, 184, 0.14) !important;
}

.dark-mode .app-section-subtitle {
    color: #64748b !important;
}

.dark-mode .app-back-link {
    color: #818cf8 !important;
}

.dark-mode .app-summary-card-value {
    color: #e5e7eb !important;
}

.dark-mode .app-summary-card-title {
    color: #64748b !important;
}

.dark-mode .q-expansion {
    background: #181f36 !important;
}

.dark-mode .detail-row {
    border-bottom-color: rgba(148, 163, 184, 0.12);
}

.dark-mode .detail-header {
    border-bottom-color: rgba(148, 163, 184, 0.14);
    color: #e5e7eb;
}

.dark-mode .detail-img {
    background: #1a2138 !important;
}

.dark-mode .detail-label {
    color: #94a3b8;
}

.dark-mode .detail-value {
    color: #e5e7eb;
}

.dark-mode .detail-sub {
    color: #64748b;
}

.dark-mode .detail-missing {
    color: #f87171;
}

.dark-mode .detail-notes {
    color: #94a3b8;
}

.dark-mode .rank-medal-1 { color: #fbbf24; }
.dark-mode .rank-medal-2 { color: #94a3b8; }
.dark-mode .rank-medal-3 { color: #f59e0b; }

.dark-mode .rank-row {
    background: #181f36 !important;
    border-bottom-color: rgba(148, 163, 184, 0.12) !important;
}

.dark-mode .rank-value-ev { color: #4ade80; }
.dark-mode .rank-value-ice { color: #f87171; }
.dark-mode .rank-badge-ev { background: rgba(74, 222, 128, 0.14); color: #4ade80; }
.dark-mode .rank-badge-ice { background: rgba(248, 113, 113, 0.14); color: #f87171; }

.dark-mode .q-input,
.dark-mode .q-number,
.dark-mode .q-select {
    color: #e5e7eb !important;
}

.dark-mode .q-input fieldset,
.dark-mode .q-number fieldset,
.dark-mode .q-select fieldset {
    color: #475569 !important;
}
"""
