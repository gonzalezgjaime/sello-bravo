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


class ValidationError(ValueError):
    """Raised when a candidates payload violates the engine schema."""


_REQUIRED_FIELDS = (
    "id", "name", "archetype", "capital_usd", "not_scam_legal_safe",
    "scores", "evidence", "why_fits_you", "first_dollar_path", "kill_criteria",
)


def validate_candidates(data, config):
    """Validate a candidates payload against the engine schema. Returns True or raises."""
    if not isinstance(data.get("candidates"), list):
        raise ValidationError("Top-level 'candidates' list is required")
    archetypes = set(config["archetypes"])
    counts = {}
    for i, c in enumerate(data["candidates"]):
        where = f"candidate[{i}] ({c.get('id', '?')})"
        for field in _REQUIRED_FIELDS:
            if field not in c:
                raise ValidationError(f"{where}: missing '{field}'")
        if c["archetype"] not in archetypes:
            raise ValidationError(f"{where}: unknown archetype '{c['archetype']}'")
        if not isinstance(c["capital_usd"], (int, float)) or isinstance(c["capital_usd"], bool) or c["capital_usd"] < 0:
            raise ValidationError(f"{where}: capital_usd must be a non-negative number")
        if not isinstance(c["not_scam_legal_safe"], bool):
            raise ValidationError(f"{where}: not_scam_legal_safe must be boolean")
        scores = c["scores"]
        if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
            raise ValidationError(f"{where}: scores must cover exactly the 7 dimensions")
        for dim, val in scores.items():
            if isinstance(val, bool) or not isinstance(val, int) or not (1 <= val <= 5):
                raise ValidationError(f"{where}: score '{dim}' must be int 1-5")
        counts[c["archetype"]] = counts.get(c["archetype"], 0) + 1
    min_per = config.get("min_candidates_per_archetype", 1)
    short = sorted(a for a in archetypes if counts.get(a, 0) < min_per)
    if short:
        raise ValidationError(
            f"Need >= {min_per} candidate(s) per archetype; missing: {short}")
    return True


def main(argv=None):
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(
        description="Score and rank solopreneur idea candidates.")
    parser.add_argument("candidates", help="Path to candidates.json")
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "config.json"))
    parser.add_argument("--out", default="shortlist.md")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    with open(args.candidates) as f:
        data = json.load(f)
    try:
        validate_candidates(data, config)
    except ValidationError as exc:
        print(f"Invalid candidates payload: {exc}", file=sys.stderr)
        return 2

    survivors, rejected = rank(data, config)
    with open(args.out, "w") as f:
        f.write(render_shortlist(survivors, rejected, data, config))
    print(f"Wrote {args.out}: {len(survivors)} ranked, {len(rejected)} rejected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
