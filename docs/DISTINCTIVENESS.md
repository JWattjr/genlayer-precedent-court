# Distinctiveness review

This is a local comparison against the named projects in this workspace, not an ecosystem-wide originality claim.

## Precedent Court and earlier projects

| Project | What it judges | What Precedent Court judges | State carried forward |
|---|---|---|---|
| `optimistic-assertion-court-DESIGN.md` | Whether one frozen claim is true, false, or undetermined from its evidence; challenge and appeal state controls synthetic bond settlement. | Whether a proposed outcome and normalized holding are consistent with frozen cited rulings and the surfaced prior rulings. It expressly does not decide who is right on the merits. | The assertion court carries one claim's verdict and appeal history. This project carries an append-only sequence of holdings that later cases must cite, distinguish, or face as potential contradictions. |
| `court-release/` | A disputed claim against a frozen evidence document, with a cited passage checked against that document. | Cross-case precedential consistency, including case-specific distinctions. | `court-release` stores evidence and the result for one claim. This project stores each final ruling as a new rule available to later cases. |
| `court-review/` | The same evidence-based claim judgment with matched bonds, a stricter appeal, exact settlement, and stale-dispute refunds. | Whether a new proposal fits the precedent record; the validators are not asked to resolve the underlying evidence on the merits. | `court-review` carries claim, appeal, evidence, and bond state. This project carries ordered prior holdings and their cited text snapshots into later proposals. |
| `court-appeal/` | An additional live appeal over an evidence-based assertion, retaining the original claim and settlement history. | A consistency review whose consequences include an append-only rule for subsequent cases. | `court-appeal` extends one claim's appeal ledger. This project compounds case outcomes into the next case's decision context. |
| `liability-cascade-phase1/` and `liability-review.md` | Whether the earliest pipeline step violated its frozen duty, was faithful, or was unclear; code attributes synthetic liability. | Whether the proposed holding is consistent with prior holdings and whether stated factual distinctions are valid. | Liability Cascade carries a frozen ordered pipeline, observations, and bond outcomes. Precedent Court carries legal-style rules and citation links across independent cases. |
| `evidence_retraction_demo.py` | Whether committed evidence bytes remain present or have changed/retracted under its evidence lifecycle. | Precedent compatibility; the input evidence is frozen into the case and is not fetched or judged for truth. | The retraction demo carries evidence versions and retraction state. Precedent Court carries rulings and their source-case snapshots. |

The closest resemblance is the earlier assertion-court family: both use validator judgment and synthetic bond accounting. The distinction only holds if a final ruling becomes an immutable precedent and later adjudications actually receive that ruling. This implementation stores precedents in a separate Registry contract, snapshots citation text into each case, and keeps the bond pending until the emitted Registry append is finalized and read back. StudioNet evidence is recorded separately from local design claims.

## Relationship to Final Offer Arbitration

Precedent Court judges enum-level consistency between a proposed rule and earlier rulings. Final Offer Arbitration judges which of two sealed settlement offers is closer to the evidence and then pays the chosen amount exactly. Precedent Court carries rules across cases; Final Offer Arbitration carries two committed offers through one dispute. They share bounded evidence, synthetic-unit accounting, strict model output handling, and code-controlled settlement, but their judgment targets and cross-dispute state are different.

## Limits of the claim

Commit/reveal, synthetic accounting, independent validator calls, bounded JSON, and deterministic state transitions are shared building blocks. The claimed distinction is the compounding precedent ledger and the consistency-versus-merits boundary. No ecosystem-wide novelty or award outcome is asserted.
