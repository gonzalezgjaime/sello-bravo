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


def rank(data, config):
    """Score all candidates; return (survivors_sorted, rejected)."""
    scored = [score_candidate(c, config) for c in data["candidates"]]
    survivors = [s for s in scored if not s["rejected"]]
    rejected = [s for s in scored if s["rejected"]]
    survivors.sort(key=lambda s: (-s["score"], s["id"]))
    return survivors, rejected


def render_shortlist(survivors, rejected, data, config):
    """Render the ranked shortlist as markdown."""
    by_id = {c["id"]: c for c in data["candidates"]}
    lo, hi = config["target_mxn_monthly"]
    lines = ["# Ranked Shortlist", ""]
    lines.append(
        f"_Scored {len(survivors) + len(rejected)} candidates; "
        f"{len(survivors)} passed gates, {len(rejected)} rejected. "
        f"Target: {lo:,}–{hi:,} MXN/mo._"
    )
    lines += ["", "| Rank | Idea | Archetype | Score |", "|---|---|---|---|"]
    for i, s in enumerate(survivors, 1):
        lines.append(f"| {i} | {s['name']} | {s['archetype']} | {s['score']} |")

    lines += ["", "## Top 5 — detail"]
    for s in survivors[:5]:
        c = by_id[s["id"]]
        lines += [
            "",
            f"### {s['name']}  (score {s['score']})",
            f"- **Why it fits you:** {c['why_fits_you']}",
            f"- **First-dollar path:** {c['first_dollar_path']}",
            f"- **Kill-criteria:** {c['kill_criteria']}",
        ]

    if rejected:
        lines += ["", "## Rejected (failed a gate)"]
        for s in rejected:
            lines.append(f"- **{s['name']}** — {'; '.join(s['reject_reasons'])}")

    return "\n".join(lines) + "\n"
