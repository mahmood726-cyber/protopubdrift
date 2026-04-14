# Proto-Pub-Drift Design

Status: draft
Date: 2026-04-14
Author: Mahmood Ahmad

## Purpose

Quantify protocol-to-publication drift across the set of RCTs included in Cochrane systematic reviews, using six pre-specified drift axes. Produce a per-trial drift card, a sponsor-level league table, a drift heatmap dashboard, a BMJ Analysis manuscript, and an E156 micro-paper.

Complements (does not overlap) existing portfolio tools: `OutcomeSwitchDetector` handles primary-outcome switching in isolation; `HiddennessAtlas` handles CT.gov publication hiddenness; `MetaAudit` handles post-hoc meta-analysis bias. Proto-Pub-Drift is the only tool covering the full six-axis drift surface on the Cochrane-included primary RCT cohort.

## Non-goals

- Not building another NMA/pooling variant.
- Not making a causal claim that drift causes effect-size inflation. A descriptive correlation with MetaAudit's effect deltas is in scope; the adjusted causal analysis belongs to a MetaAudit Phase 2.
- Not a pip-installable tool release. Paper + dashboard + E156 only.
- Not parsing paywalled PDFs. OA-only: AACT + PMC full-text XML + Cochrane CDSR metadata export.

## Cohort

RCTs included as primary studies in Cochrane systematic reviews, as extracted from a pinned dated Cochrane CDSR metadata dump. Excluded: non-RCTs, RCTs without an NCT identifier, RCTs registered after first enrollment with no recoverable pre-enrollment protocol snapshot.

The dated CDSR export version is pinned in the repo (`cohort/cdsr_export_version.txt`) and cited in the paper. Staleness is declared explicitly rather than silently refreshed.

## Protocol-version anchor

- **Primary anchor:** last AACT protocol version timestamped strictly before `start_date` (first-participant-enrolled). Selected via `study_first_submitted_date` and `last_update_submitted_date` from the `studies` table.
- **Sensitivity anchor:** last AACT protocol version timestamped strictly before `primary_completion_date`. Matches the "pre-results" snapshot used by AllTrials/COMPare.

Trials with no pre-enrollment snapshot are routed to the hand-audit queue and cannot enter the main analysis.

## Publication-value extraction

Hybrid strategy:

1. **Primary source:** AACT posted-results (`reported_events`, `outcome_measurements`, `baseline_measurements`, `result_groups`). Structured, no NLP.
2. **Fallback source:** PMC full-text XML for trials without AACT posted-results. Regex + optional LLM extraction per axis, with a `source_flag` recorded on every extracted field.
3. **Hand-audit:** 200-trial stratified random subsample (stratified by sponsor type and TA). Human-verified ground truth for all six axes. Yields an accuracy-per-axis table reported in the paper.

**Publication gate:**
- Per-axis accuracy below 0.80 blocks the headline drift-prevalence figure for that axis.
- If any axis fails the 0.80 bar, the composite "any drift" flag is also blocked from headline use (the composite inherits the weakest-axis accuracy). The extractor must be iterated until all six axes clear 0.80 before any headline drift-prevalence claim — per-axis or composite — is released.

## Drift axes and thresholds (pre-registered SAP)

| # | Axis | Continuous delta | Binary flag rule |
|---|------|------------------|------------------|
| 1 | Primary outcome | n/a | Any definitional change to name, measure, or timepoint |
| 2 | Sample size | ΔN = N_published − N_anchor | \|ΔN\| / N_anchor ≥ 0.15 |
| 3 | Eligibility | Δcriteria = added − removed (net) across inclusion+exclusion | net \|Δ\| ≥ 2 criteria |
| 4 | Analysis plan | Registered vs published primary-analysis method family | Family change (ITT→PP, ANCOVA→logistic, etc.) |
| 5 | Subgroup list | Jaccard(anchor subgroups, published subgroups) | Jaccard < 0.60 |
| 6 | Follow-up duration | Δmonths = FU_published − FU_anchor | \|Δmonths\| / FU_anchor ≥ 0.20 |

**Composite flag:** a trial is "drifted" if any binary flag is set. The per-axis continuous deltas are retained for the descriptive correlation with MetaAudit effect deltas (no causal claim).

Thresholds are frozen in `sap/drift_thresholds.yml` and referenced from the manuscript to forestall reviewer threshold-shopping.

## Module layout

```
C:\Models\ProtoPubDrift\
  cohort/                # CDSR export parsing, NCT list producer
  protocol_anchor/       # AACT version selection (primary + sensitivity)
  publication_values/    # AACT posted-results primary, PMC XML fallback, source_flag
  drift_engine/          # six per-axis detectors; composite flag; SAP-driven thresholds
  validation/            # 200-trial hand-audit harness, accuracy table generator
  analysis/              # prevalence, sponsor league, descriptive correlation with MetaAudit
  dashboard/             # static GitHub Pages: per-trial card, sponsor league, heatmap
  paper/                 # BMJ Analysis manuscript draft
  e156-submission/       # E156 micro-paper body + workbook entry
  sap/                   # pre-registered analysis plan and threshold file
  tests/                 # per-axis unit tests + COMPare integration + schema checks
  data/                  # pinned CDSR export version, hand-audit CSV
  docs/                  # this spec + downstream plan
  LICENSE, README.md, E156-PROTOCOL.md, index.html, PROGRESS.md (gitignored)
```

## Data sources

- AACT PostgreSQL snapshot (https://aact.ctti-clinicaltrials.org) — local candidate roots on C: or D:, path resolved via config.
- Cochrane CDSR metadata export (dated, pinned).
- PMC full-text XML bulk archive.
- MetaAudit effect-delta CSV (consumed read-only).

All sources OA. No proprietary access, no paywalled content.

## Testing

- Unit tests per axis detector on synthetic anchor/publication pairs covering boundary thresholds and null cases.
- Integration test against 20 trials with published drift analyses from the COMPare Trials project; detector output must match published drift classifications within axis scope.
- Schema check on AACT load: every column referenced in `publication_values/` and `protocol_anchor/` is verified against `information_schema`; fail-closed on drift.
- Numerical baselines pinned for the three Python-computable axes (ΔN, Δmonths, Jaccard) against hand-verified fixtures.
- Edge cases explicitly covered: k=1 subgroup lists (Jaccard undefined → null, not zero), zero anchor sample size (flag and skip), missing PMCID (route to hand-audit queue), AACT posted-results fields present but empty (treat as missing, not as match).

Regression coverage preserved for: division-by-zero in threshold ratios, Windows `cp1252` encoding of extracted subgroup strings, European decimal handling in PMC XML, silent-failure sentinel prevention in `drift_engine/` (raise `KeyError` with expected-vs-received diff on schema mismatch, never return "unknown_ratio").

## Failure-mode guards

- **AACT column rename** between snapshots → schema check fails closed with column diff.
- **Missing PMCID for a cohort trial** → flag, route to hand-audit queue, do not invent values.
- **CDSR export staleness** → pinned version cited in paper; new export requires a fresh pre-registration amendment.
- **Hand-audit accuracy < 0.80 per axis** → blocks publication of that axis's headline figure until extractor iterates.
- **TruthCert discipline:** all pooled claims (drift prevalence, sponsor league, correlation ρ) are TruthCert-bundled. No naked numbers. HMAC key sourced from `TRUTHCERT_HMAC_KEY` env var, never from the bundle itself, never from a placeholder string.
- **Memory ≠ evidence:** the CDSR export version and hand-audit accuracy table are version-controlled artifacts, not remembered state.

## Shipping artifacts

- BMJ Analysis manuscript (`paper/bmj-analysis.md`).
- E156 micro-paper body + `e156-submission/` folder + workbook entry (`CURRENT BODY` only; `YOUR REWRITE` empty; `SUBMITTED: [ ]`).
- Static GitHub Pages dashboard at `index.html` (per-trial card, sponsor league, 6-axis drift heatmap). Offline-first, no CDN, no hardcoded local paths.
- TruthCert bundle covering all pooled claims.
- CSV of per-trial drift cards (`data/drift_cards.csv`), columns: `nct_id, anchor_version, pub_source_flag, delta_*, flag_*, composite_flag, cdsr_review_id, sponsor_class, ta`.
- `INDEX.md` entry under `C:\ProjectIndex\`.
- `C:\E156\rewrite-workbook.txt` entry (count incremented).

## Timeline

~6 weeks (standard E156+dashboard+paper output scope per earlier decision B).

## Dependencies / prereqs (must verify before implementation plan)

- `python C:\ProjectIndex\reconcile_counts.py` exits 0 (registry sane).
- AACT snapshot path resolves on disk (C: or D: candidate roots).
- Dated CDSR export present under `data/`.
- PMC full-text XML archive path resolves.
- MetaAudit effect-delta CSV exists (for the correlation step only; optional for main drift analysis).
- `TRUTHCERT_HMAC_KEY` env var set for signing.

A Task 0 in the implementation plan will script these checks and fail closed with a specific user-action list if any prereq is missing (lesson from Evidence Forecast Phase-1).

## Out of scope for this spec

- Causal adjustment for drift → effect-inflation (belongs to MetaAudit Phase 2).
- PDF parsing of paywalled trial publications.
- Retraction-aware filtering (that lives in the sibling `RetractRipple` spec).
- Non-Cochrane systematic-review cohorts.
- Phase-2 RCTs or observational studies.
