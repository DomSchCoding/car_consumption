"""Central UI state for the Vehicle Consumption Analyzer."""

from __future__ import annotations

SESSION: dict[str, object] = {
    "selected": [],
    "dark": False,
    "ranking_sort": False,
    "current_make": "",
    "ev_checked": True,
    "ice_checked": False,
    "ranking_ev": True,
    "ranking_ice": False,
}
