"""Core data model + the Source interface for the MX market analyzer.

Stdlib only. A ``Source`` measures one niche and returns ``NicheMetrics`` with
whatever it could measure (unmeasured fields stay ``None``). The synthesizer
merges metrics across sources into ranked ``OpportunityScore`` objects.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NicheMetrics:
    """What one Source measured for one niche. Unmeasured fields stay None."""

    niche_id: str
    source: str
    provenance: str  # "REAL" | "EST"
    listing_count: Optional[int] = None        # competition proxy (total live listings)
    total_sold: Optional[int] = None           # demand proxy (sum sold_quantity, sampled)
    price_median_mxn: Optional[float] = None
    price_min_mxn: Optional[float] = None
    price_max_mxn: Optional[float] = None
    top_seller_share: Optional[float] = None   # 0..1 sampled-listing concentration
    seasonality_fit: Optional[float] = None    # 0..1 (1 = peak month now)
    notes: str = ""


@dataclass
class OpportunityScore:
    """A niche's ranked opportunity, with normalized components for the report."""

    niche_id: str
    niche_name: str
    score: float            # 0..100
    provenance: str         # "REAL" if real demand/competition/price drove it, else "EST"
    demand_n: float         # normalized 0..1 components (for the report)
    competition_n: float
    margin_n: float
    seasonality: float
    margin_mxn: Optional[float]   # raw estimated unit margin (MXN)
    detail: dict = field(default_factory=dict)  # raw measured numbers


class Source(ABC):
    """A marketplace/data adapter. Implementations set ``name`` and ``provenance``."""

    name: str = "source"
    provenance: str = "EST"

    @abstractmethod
    def analyze_niche(self, niche: dict) -> NicheMetrics:
        """Measure one niche dict ({id, name, query, product_type, ...})."""
        raise NotImplementedError
