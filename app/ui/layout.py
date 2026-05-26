"""Shared page layout with navigation bar and page container.

Usage:
    with page_layout("Dashboard"):
        ui.label("Page content here")

The layout provides:
- Sticky top navigation bar with app title and page links
- Dark mode toggle in the nav bar
- Consistent max-width container
- Breadcrumb / page title
- Global CSS injection (once per app lifecycle)
"""

from __future__ import annotations

from nicegui import app as nicegui_app
from nicegui import ui

from app.ui.state import SESSION
from app.ui.theme import DARK_MODE_CSS, THEME_CSS

# Track whether CSS has been injected globally
_css_injected = False


def _inject_css() -> None:
    """Inject shared theme CSS once per app lifecycle."""
    global _css_injected
    if not _css_injected:
        ui.add_css(THEME_CSS)
        ui.add_css(DARK_MODE_CSS)
        _css_injected = True


def _apply_dark_mode() -> None:
    """Apply or remove dark mode class on body."""
    is_dark = SESSION.get("dark", False)
    mode = "dark" if is_dark else "light"
    ui.run_javascript(f"document.body.classList.toggle('dark-mode', {is_dark})")


def _toggle_dark_mode() -> None:
    """Toggle dark mode in session and apply."""
    SESSION["dark"] = not SESSION.get("dark", False)
    _apply_dark_mode()


def nav_bar() -> None:
    """Render the shared navigation bar."""
    _inject_css()

    with ui.element("div").classes("app-nav"):
        # Title - links to dashboard
        ui.link("🚗 Vehicle Consumption Analyzer", "/").classes(
            "app-nav-title"
        ).style("cursor:pointer;")

        # Nav links
        with ui.element("div").classes("app-nav-links"):
            ui.link("Dashboard", "/").classes("app-nav-link")
            ui.link("Route Planner", "/route").classes("app-nav-link")
            ui.link("Manual Route", "/route/manual").classes("app-nav-link")

            # Dark mode toggle
            ui.button(
                on_click=_toggle_dark_mode,
            ).props(
                "flat icon='dark_mode' color=primary"
                if not SESSION.get("dark", False)
                else "flat icon='light_mode' color=warning"
            ).style("font-size:1.1em;")


def page_layout(title: str, show_back: bool = False, back_url: str = "/") -> ui.element:
    """Context manager for page content with consistent layout.

    Args:
        title: Page title shown in the header.
        show_back: Whether to show a back link.
        back_url: URL for the back link.

    Usage:
        @ui.page('/')
        def dashboard():
            nav_bar()
            with page_layout("Dashboard"):
                ui.label("Content here")
    """
    _inject_css()

    # Apply dark mode on page load
    ui.timer(0.05, _apply_dark_mode, once=True)

    with ui.element("div").classes("app-page-container"):
        # Back link if requested
        if show_back:
            ui.link(f"← Back", back_url).classes("app-back-link").style("margin-bottom:12px;")

        # Page title
        ui.label(title).classes("app-section-title").style("font-size:1.5em;")

        # Content container
        return ui.column().style("gap:16px; width:100%;")
