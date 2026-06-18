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
