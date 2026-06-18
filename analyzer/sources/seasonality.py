"""MX seasonality source (EST) — maps a niche to relevant Mexican demand peaks.

Returns ``seasonality_fit`` in 0..1 (1.0 = a peak month is the current month,
decaying with circular month-distance to the nearest peak). The current month is
injected so the scoring stays deterministic in tests; the CLI passes the real
month at runtime.
"""
from analyzer.base import NicheMetrics, Source

# Month numbers (1-12) of MX demand peaks, keyed by a theme substring.
PEAKS = {
    "madres": [4, 5],            # Dia de las Madres (May 10) + run-up
    "muertos": [10, 11],         # Dia de Muertos
    "navidad": [11, 12],         # Navidad / Buen Fin
    "reyes": [12, 1],            # Reyes (Jan 6)
    "quince": [3, 4, 5, 6, 7],   # quinceanera season (spring-summer)
    "xv": [3, 4, 5, 6, 7],
    "maestr": [5],               # Dia del Maestro (May 15)
    "enfermer": [1],             # Dia de la Enfermera (Jan 6, MX)
    "graduacion": [6, 7],
    "graduac": [6, 7],
}
EVERGREEN_FIT = 0.5  # no clear peak -> neutral mid score


def _circular_distance(a, b):
    """Shortest month gap between months a and b on a 12-month circle."""
    return min((a - b) % 12, (b - a) % 12)


class SeasonalitySource(Source):
    name = "seasonality"
    provenance = "EST"

    def __init__(self, month):
        self.month = month  # 1..12, injected

    def analyze_niche(self, niche):
        text = " ".join(str(niche.get(k, "")) for k in ("id", "name", "query")).lower()
        peak_months = set()
        for keyword, months in PEAKS.items():
            if keyword in text:
                peak_months.update(months)
        if not peak_months:
            fit, note = EVERGREEN_FIT, "No strong MX seasonal peak; treated as evergreen."
        elif self.month in peak_months:
            fit, note = 1.0, f"In-season now (month {self.month})."
        else:
            dist = min(_circular_distance(self.month, p) for p in peak_months)
            fit = max(0.0, 1.0 - dist / 6.0)
            note = f"Off-season; nearest peak {dist} month(s) away."
        return NicheMetrics(
            niche_id=niche["id"], source=self.name, provenance=self.provenance,
            seasonality_fit=round(fit, 3), notes=note)
