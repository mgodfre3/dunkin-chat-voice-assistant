"""Pydantic models for Dunkin' CRM data."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

__all__ = [
    "CustomerFavoriteItem",
    "CustomerSuggestion",
    "CustomerProfile",
]


class CustomerFavoriteItem(BaseModel):
    """Represents a frequent item for a known customer."""

    item: str
    size: Optional[str] = None
    quantity: int = 1
    price: Optional[float] = None


class CustomerSuggestion(BaseModel):
    """Suggested upsell or personalized bundle."""

    headline: str
    description: Optional[str] = None
    items: List[CustomerFavoriteItem] = Field(default_factory=list)


class CustomerProfile(BaseModel):
    """Full CRM profile surfaced to the voice and dashboard experiences."""

    id: str
    name: str
    rewards_status: str
    loyalty_score: int = 0
    loyalty_goal: int = 1000
    curbside_preferred: bool = False
    bluetooth_devices: List[str] = Field(default_factory=list, description="Known Bluetooth MAC addresses")
    favorite_items: List[CustomerFavoriteItem] = Field(default_factory=list)
    usual_order: List[CustomerFavoriteItem] = Field(default_factory=list)
    suggested_sales: List[str] = Field(default_factory=list)
    suggestions: List[CustomerSuggestion] = Field(default_factory=list)
    last_visit_iso: Optional[str] = None

    @property
    def loyalty_progress_pct(self) -> float:
        if self.loyalty_goal <= 0:
            return 0.0
        return max(0.0, min(1.0, self.loyalty_score / self.loyalty_goal))
