# Solopreneur Idea Engine + Two-Stream Portfolio — Design Spec

**Date:** 2026-06-17
**Owner:** hgonzalez@arrk.com
**Status:** Approved (brainstorming complete) → ready for implementation planning

---

## 1. Context & Goal

The user is a proven physical-product operator (previously ran an Amazon Seller Central
account selling sublimated mugs in the US and Mexico; hit ~$100k in the first month of the
mug venture before having to forfeit it for unrelated reasons). They are also an expert at
automating with Claude and related tools. They want to use Claude to be **creative**, not
just to automate.

**Goal:** Stand up **at least two extra revenue streams** beside the day job that **run
practically on their own**, with **near-zero upfront investment**, generating
**considerable side income**.

**Approach chosen:** "Engine + Two Assets" — build a reusable idea-generation/scoring engine
first, run it to select two *complementary* streams, then build and automate each so it runs
within a fixed weekly time budget.

---

## 2. Constraints Profile (the inputs that make the engine's output *his*, not generic)

| Field | Value |
|---|---|
| Capital ceiling | **≤ $200 USD** to start (hard gate — anything requiring more is rejected) |
| Build-phase time | **≥ 8 hrs/week**, flexible upward as a stream ramps |
| Steady-state time | **≤ 2–3 hrs/week per stream** ("runs on its own" requirement) |
| Unfair advantage #1 | Proven physical-product / Amazon operator **at scale** |
| Unfair advantage #2 | Expert Claude / automation builder |
| Unfair advantage #3 | **Bilingual EN/ES + proven Mexico-market sales success** (less competition in ES-language niches) |
| Hard no's | Scam-/get-rich-quick-adjacent; anything needing employees; anything needing big paid-ad spend to work |
| Income target | **30,000–50,000 MXN/month to start** (≈ USD $1,600–$2,800/mo, rate-dependent), with room to grow |

**Implication for weighting:** target is reliable and moderate, so the engine optimizes for
*speed-to-target and durability* (base hits) over moonshot ceilings.

---

## 3. System Architecture

Three parts, built in order:

```
PART 1 — THE IDEA ENGINE (reusable Claude Code asset)
   Constraints Profile ─▶ Diverge (generate N ideas across 7 archetypes)
                                     │
                                     ▼
                          Converge (gates + weighted rubric tuned to the user)
                                     │
                                     ▼
                    Ranked shortlist + evidence + "why it fits you" + kill-criteria
                                     │
PART 2 — SELECTION                   ▼
   Pick TWO *complementary* streams (different failure modes):
     • Stream A — "Proven/Safe"  (leans on POD muscle)
     • Stream B — "Compounding"  (digital asset, asymmetric)
                                     │
PART 3 — THE TWO STREAMS, AUTOMATED  ▼
   Build + wire each to run within a fixed weekly "touch budget" (≤2–3 hrs/wk each)
```

**Final deliverables:** (1) the committed Idea Engine prompt, (2) a ranked shortlist doc,
(3) a one-page launch plan per chosen stream.

---

## 4. The Idea Engine (core artifact)

Four moving parts.

### ① Inputs — the Constraints Profile
Section 2 above, supplied to the engine at run time (editable each run).

### ② Diverge — forced-diversity generation
The engine generates candidates across **7 archetypes** so it doesn't return ten variants of
one idea:
1. Productized service (Claude executes the work)
2. Micro-SaaS / micro-tool
3. Digital products (templates, prompt packs, datasets, info-products)
4. **POD / physical** (the user's proven lane)
5. Content / audience asset (niche site, newsletter, faceless media)
6. Marketplace / arbitrage
7. Automation / agent products

### ③ Converge — gates + weighted rubric
**Gates (pass/fail — instantly kills the idea):**
- Capital required ≤ ceiling ($200)
- Not scam-adjacent; legal and platform-safe

**Weighted dimensions (score 1–5 each):**

| Dimension | Weight |
|---|---|
| Runs on its own (low steady-state touch) | ×3 |
| Leverages the user's unfair advantage | ×3 |
| Distribution (believable path to buyers) | ×3 |
| Demand evidence (proof people pay *now*) | ×2 |
| Time-to-first-dollar | ×2 |
| Revenue ceiling (can it reach "considerable"?) | ×1 |
| Defensibility (not copyable in a weekend) | ×1 |

The three ×3 dimensions encode the user's real priorities: hands-off, plays to strengths, and
reachable buyers. **Distribution is triple-weighted on purpose** — it is the #1 killer of
solo digital ventures (~70% of micro-SaaS dies on distribution, not on the build).

### ④ Output
A ranked table of all scored candidates, and for the **top 5**:
- a paragraph on *why it fits this user specifically*,
- the *first-dollar path*,
- **kill-criteria** ("drop this if X hasn't happened by week N") to force fail-fast.

### Design principle — surface-portable with graceful degradation
The engine prompt has a **core ideate-and-score section that runs in any Claude chat**
(no tools → no live research or file output, reasons from training knowledge), plus
**tool-powered steps that auto-activate in Claude Code** (live demand research via web search,
writing the ranked shortlist to a file). Lets the user rough-think on mobile and run the full
engine at the desk.

---

## 5. Surface-to-Job Mapping

Each Claude surface is assigned the job it is best at (not one prompt everywhere):

| Surface | Its job in this venture |
|---|---|
| **Claude Code** | The Idea Engine (research, scoring, file output) + building the micro-tool/SaaS + wiring automations |
| **Claude Design** (launched 2026-04-17; visual tool — decks, one-pagers, prototypes, mockups; exports PDF/PPTX/Canva) | Visual production: POD mug/merch designs, product mockups, landing-page & marketing one-pagers, pitch decks |
| **Claude.ai (chat)** | Quick portable ideation away from the terminal |

Note: pasting the Idea Engine prompt into Claude Design will *not* run the engine — Claude
Design will try to render a *picture of* an idea list. Right tool, different job.

---

## 6. Selection Rule (Part 2)

Don't just take the top two — enforce **complementarity** so the two streams can't die from the
same shock.

| Axis | Stream A | Stream B |
|---|---|---|
| Role | Proven / safe | Compounding / asymmetric |
| Distribution | Marketplace (built-in buyers) | Search / community / audience |
| Time-to-money | Fast (weeks) | Slow but compounding (months) |
| Failure mode | Platform policy change | Build / distribution risk |

**Rule:** Stream A = highest-scoring idea that leans on the user's proven muscle.
Stream B = highest-scoring *digital/compounding* idea whose **distribution channel differs
from A's**. Different channels is the diversification lesson from the forced Amazon exit,
encoded as a rule.

### Warm-start candidates (preview — the engine makes the final call)
*Stream A (proven lane):*
- **Spanish-language POD mugs/merch** on Amazon MX + Mercado Libre + Etsy. Near-zero touch
  once wired, leans on the proven Mexico playbook + bilingual edge; the marketplaces are the
  distribution. ES designs face far less competition than the saturated English POD market.
  Claude mass-generates designs/listings/keywords.

*Stream B (compounding/digital):*
- **Micro-tool for POD/Amazon sellers** (listing/keyword/design-prompt generator) — sell to a
  world the user already knows; he is his own first customer.
- **Spanish-language digital products** (prompt packs / templates / mini info-products for
  LATAM creators & small businesses) — purest compounding, lowest touch.
- **Faceless Spanish-language content asset** (niche newsletter / short-form) — highest
  ceiling but more ongoing touch; engine may dock it on hands-off.

Most likely winning pair: **ES-language POD (A)** + a **digital asset (B)** — different
channels, speeds, and failure modes.

---

## 7. Operating Model (Part 3) — how each stream runs itself

"Runs on its own" = a loop where automation does the repetitive work and the human supplies
only taste/judgment.

```
   PRODUCE ───▶ DISTRIBUTE ───▶ FULFILL ───▶ LEARN
   (Claude)      (Claude)       (100% auto)   (human, ~30 min/wk)
      ▲                                          │
      └──────────  human picks winners  ◀────────┘
```

**Stream A (ES-language POD), concretely:**
- Produce: Claude Code generates design concepts + niches → Claude Design renders the art → batch upload
- Distribute: Claude writes EN/ES listings + keywords per marketplace
- Fulfill: 100% hands-off — Printify/Printful prints & ships on order
- Learn: ~30 min/wk — read what sold, kill duds, clone winners
- **Touch budget: ≤ 2 hrs/wk** once wired

**Stream B (digital asset):**
- Built once in Claude Code; sells via automated checkout (Stripe/Gumroad/marketplace);
  delivery automatic. Weekly job = short content/marketing push (Claude drafts, human
  approves) + reading analytics.
- **Touch budget: ≤ 2–3 hrs/wk**

**Sequencing:** Build **A first** (faster to first dollar, proven lane → early confidence +
cash), then build B while A coasts on its 2-hr budget. Not both at once.

---

## 8. Risk Guardrails

Lessons from the forced Amazon exit + the 2025–26 FTC crackdown on AI "passive income" scams:
- **No single point of failure** — A and B use different channels by rule; within A, list on
  2+ marketplaces, never one.
- **Scam-test every idea** — the engine's gate rejects get-rich-quick / "passive income course"
  territory. Sell *real products to real buyers* only.
- **Kill-criteria on every stream** — predefined "drop it if X hasn't happened by week N," so a
  dud costs weeks, not months.
- **Capital discipline** — start ≤ $200; reinvest *profit* only, never out-of-pocket scaling.

---

## 9. Success Metrics

- **Proof:** first sale within ~4 weeks of a stream launching.
- **Traction:** $1k/mo combined within ~6 months.
- **Target:** 30,000–50,000 MXN/month combined (≈ USD $1,600–$2,800/mo), with room to grow.

These numbers give the kill-criteria teeth.

---

## 10. Deliverables (what implementation produces)

1. **`idea-engine.md`** — the reusable, surface-portable Claude Code prompt (the engine).
2. **`shortlist.md`** — the ranked output from running the engine, with top-5 detail + kill-criteria.
3. **`stream-A-launch.md`** and **`stream-B-launch.md`** — one-page launch plans for the two
   selected streams.

---

## 11. Open Questions / Next Step

- Exact two streams are decided by *running* the engine (Part 2), not pre-chosen here.
- Whether to track this project in git (the folder lives in Google Drive; not currently a git repo).

**Next step:** invoke the `writing-plans` skill to turn this spec into a step-by-step
implementation plan (build engine → run engine → select streams → build & automate Stream A → Stream B).
