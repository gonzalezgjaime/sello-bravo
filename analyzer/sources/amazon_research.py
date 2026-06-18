"""Amazon Mexico source — research-grade EST placeholder.

There is no free programmatic Amazon-MX product search (PA-API is deprecated;
SP-API needs a seller account). Rather than fabricate numbers, this adapter
returns no measured values and a clear note, so the synthesizer treats Amazon
as unmeasured (EST) and never lets it override real Mercado Libre signals.
Swap this for an ``AmazonSpApiSource`` once a seller account exists.
"""
from analyzer.base import NicheMetrics, Source


class AmazonResearchSource(Source):
    name = "amazon_research"
    provenance = "EST"

    def analyze_niche(self, niche):
        return NicheMetrics(
            niche_id=niche["id"], source=self.name, provenance=self.provenance,
            notes=("Amazon MX estimate pending SP-API (needs a seller account). "
                   "No measured data; does not contribute to the score yet."),
        )
