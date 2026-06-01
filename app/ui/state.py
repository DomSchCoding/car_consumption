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
    # Vehicle filter state (None = inactive)
    "filter_length_min": None,
    "filter_length_max": None,
    "filter_weight_min": None,
    "filter_weight_max": None,
    "filter_clearance_min": None,
    "filter_clearance_max": None,
    "filter_drivetrain": [],  # empty = all pass
    "filter_price_min": None,
    "filter_price_max": None,
    "filter_trunk_min": None,
    "filter_trunk_max": None,
}
