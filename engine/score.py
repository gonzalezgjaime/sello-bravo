"""Idea Engine scorer: validate, gate, weight, rank, render. Stdlib only."""
import json

DIMENSIONS = [
    "runs_on_its_own",
    "leverages_advantage",
    "distribution",
    "demand_evidence",
    "time_to_first_dollar",
    "revenue_ceiling",
    "defensibility",
]


def load_config(path):
    """Load and sanity-check the rubric config."""
    with open(path) as f:
        config = json.load(f)
    required = {"capital_ceiling_usd", "weights", "archetypes"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"Config missing keys: {sorted(missing)}")
    if set(config["weights"]) != set(DIMENSIONS):
        raise ValueError("Config weights must cover exactly the 7 dimensions")
    return config


def score_candidate(candidate, config):
    """Apply gates and compute the weighted total for one candidate."""
    capital_ok = candidate["capital_usd"] <= config["capital_ceiling_usd"]
    scam_safe = bool(candidate["not_scam_legal_safe"])
    reasons = []
    if not capital_ok:
        reasons.append(
            f"capital ${candidate['capital_usd']} > ceiling "
            f"${config['capital_ceiling_usd']}"
        )
    if not scam_safe:
        reasons.append("failed scam/legal/platform-safety gate")
    weighted = sum(
        config["weights"][d] * candidate["scores"][d] for d in DIMENSIONS
    )
    return {
        "id": candidate["id"],
        "name": candidate["name"],
        "archetype": candidate["archetype"],
        "score": weighted,
        "rejected": bool(reasons),
        "reject_reasons": reasons,
    }
