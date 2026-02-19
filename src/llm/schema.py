from __future__ import annotations

from typing import Any, Dict

NARRATIVE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "page2_exec_snapshot",
        "page3_liveability",
        "page4_market_snapshot",
        "page5_price_trend",
        "page6_nearby_comparison",
        "page7_demand_supply_sale",
        "page8_demand_supply_rent",
        "page9_propertytype_status",
        "page10_top_projects",
        "page11_registrations_developers",
        "page12_reviews_conclusion",
    ],
    "properties": {
        "page2_exec_snapshot": {
            "type": "object",
            "additionalProperties": False,
            "required": ["takeaways"],
            "properties": {
                "takeaways": {"type": "string"},
            },
        },
        "page3_liveability": {
            "type": "object",
            "additionalProperties": False,
            "required": ["summary"],
            "properties": {"summary": {"type": "string"}},
        },
        "page4_market_snapshot": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {
                "narrative": {"type": "string"},
            },
        },
        "page5_price_trend": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {"narrative": {"type": "string"}},
        },
        "page6_nearby_comparison": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {"narrative": {"type": "string"}},
        },
        "page7_demand_supply_sale": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {"narrative": {"type": "string"}},
        },
        "page8_demand_supply_rent": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {"narrative": {"type": "string"}},
        },
        "page9_propertytype_status": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {"narrative": {"type": "string"}},
        },
        "page10_top_projects": {
            "type": "object",
            "additionalProperties": False,
            "required": ["highlights"],
            "properties": {"highlights": {"type": "string"}},
        },
        "page11_registrations_developers": {
            "type": "object",
            "additionalProperties": False,
            "required": ["narrative"],
            "properties": {
                "narrative": {"type": "string"},
            },
        },
        "page12_reviews_conclusion": {
            "type": "object",
            "additionalProperties": False,
            "required": ["conclusion"],
            "properties": {"conclusion": {"type": "string"}},
        },
    },
}