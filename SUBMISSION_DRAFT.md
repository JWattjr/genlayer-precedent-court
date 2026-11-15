# Submission draft — Precedent Court

## Title

Precedent Court: disputes judged against an append-only ruling ledger

## Summary

Precedent Court asks GenLayer validators whether a proposed ruling is consistent with cited earlier decisions, rather than asking them to decide who is right on the merits. The contract freezes cited text when a case is proposed, bounds each case to two attempts, settles synthetic bond units by fixed code, and appends each consistent ruling for later cases.

## Mechanism

The claimant opens a case with a synthetic bond; the respondent may submit a position and bounded evidence before the response deadline. The claimant proposes an outcome and normalized holding with one to three precedent IDs and any fact-specific distinctions. The Court snapshots the cited records from the Registry. Validators independently return strict JSON with per-precedent relation enums and per-distinction validity enums. Consensus compares only normalized enums and the derived consistency boolean. Code controls finality, slashing, refunds, the append-only Registry write, and synthetic accounting.

## What validators decide vs. what code decides

- **Validators decide:** whether each cited or surfaced holding supports, is distinguishable from, or contradicts the proposal; whether each stated distinction is valid; and the normalized consistency result.
- **Code decides:** who may act, deadlines and default, citation snapshots, the attempt limit, fixed slash and fee arithmetic, outcome allocation, Registry append, case status, and conservation.
- The model does not decide merits, change the proposed outcome, choose a payout, or transfer an asset.

## Distinctiveness against the user's projects

Earlier `court-release/`, `court-review/`, `court-appeal/`, and `optimistic-assertion-court-DESIGN.md` judge evidence-based truth for a claim and may add challenges, appeals, or stale-deadline handling. `liability-cascade-phase1/` attributes a violation to a pipeline step; `evidence_retraction_demo.py` tracks evidence changes. Precedent Court's distinction is cross-case consistency: accepted holdings become ordered, immutable records that later cases must cite or address. Final Offer Arbitration selects between two sealed offers for one dispute and does not carry precedent across cases. This is a comparison against the named local projects, not an ecosystem-wide originality claim.

## Evidence list

Each contract address is a separate Explorer evidence entry. The StudioNet address pages and demo transaction rows were opened and checked. The Portal has not been opened or submitted to.

1. **GitHub repository:** unavailable. The required pre-publication check found `gh auth status` unauthenticated; the public repository was not created and no alternate login path was attempted.
2. **GenLayer Explorer Contract — PrecedentRegistry:** [StudioNet contract page](https://explorer-studio.genlayer.com/address/0x0FD8b71034265680EC8B46c6Ff8D06085e71f998). The page displayed this address and deployment transaction `0x26115d048abfb780eb9292334817f7a8e4e269033d6e9d7f55f70fbb3650448f`; Case A/B/C Registry append transactions were present.
3. **GenLayer Explorer Contract — PrecedentCourt:** [StudioNet contract page](https://explorer-studio.genlayer.com/address/0x68640Ef247219FF0B40d5A7a60c0F8A572178507). The page displayed this address and deployment transaction `0xa268c6a0b31e810e2ed889c6e24d3747eb9576ef6cacd8ecde220722874acb0c`; the Case A/B/C decision transactions were present.
4. **Key transaction — Case A accepted as P3:** [adjudication](https://explorer-studio.genlayer.com/tx/0xee3bc7b3e3cab3e92d69069fb089602bf8b959c52ce797e1e2d033ab9b3fda68) · [Registry append](https://explorer-studio.genlayer.com/tx/0x6a3465100618fdb0c41ce5a13982da8272620630af496d60611825c83d3ca114).
5. **Key transaction — Case B contradiction rejected:** [adjudication](https://explorer-studio.genlayer.com/tx/0x9d6da10025e8beeeb6e4a2fba8edf4ca753e5f01dbff44934c7e68e14d49b114).
6. **Key transaction — Case B revised ruling accepted as P4:** [adjudication](https://explorer-studio.genlayer.com/tx/0x71fc37ddf1563d54c9da75418531b6768e0e80449f57e8afa2300b828e92f587) · [Registry append](https://explorer-studio.genlayer.com/tx/0x3fc2e2c85091dfb6433ce74b227fd900734a75ec6ee8575423fe97ec013adb15).
7. **Key transaction — Case C cites P4 and is accepted as P5:** [adjudication](https://explorer-studio.genlayer.com/tx/0x0ccfa0271dfc17de058e70ffdf6ef8dbe39343942100d4942bcec88d3c5283bc) · [Registry append](https://explorer-studio.genlayer.com/tx/0x250e681641efa4784d99f2ab03cf65282cae8249aed09fd240867a7a646e94e6).
8. **Step 0 cross-contract probe:** [`probe/probe-result.json`](probe/probe-result.json).
9. **Live deployment receipts and direct readbacks:** [`verification/studionet-demo.json`](verification/studionet-demo.json) and [`deployments/studionet.json`](deployments/studionet.json).
10. **Explorer verification:** [`verification/explorer-checks.json`](verification/explorer-checks.json).
11. **Local verification:** [`verification/tests.txt`](verification/tests.txt) and [`verification/lint.txt`](verification/lint.txt).

This draft is prepared text only. Do not treat it as a Portal submission.
