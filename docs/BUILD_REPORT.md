# Build report

Review date: 2026-11-15. The user's November 11 submission guidance is treated as learned review guidance, not official criteria and not a promise of points.

## Technical readiness

**Live prototype ready for review.** The StudioNet cross-contract probe passed the view read, emitted write, direct Registry readback, and outsider rejection checks. The append became visible 33.158 seconds after the parent finalized. The project uses the two-contract Registry/Court design selected by that probe.

The 13 direct-mode tests pass. GenVM lint passed 3 checks for each of the Court, Registry, ProbeRegistry, and ProbeCaller contracts; ABI validation passed for all four. The probe contracts are throwaway and are excluded from submission evidence. The live release has 25 finalized transaction records. Cases A, B, and C completed, and each deployed contract's source hash matches its local source hash.

- Case A was accepted as P3; 40 synthetic units were allocated to the claimant.
- Case B's contradictory proposal was rejected and 10 units were slashed. The revised proposal was accepted as P4; the remaining 30 units went to the claimant.
- Case C cited P4 and was accepted as P5; 40 synthetic units were allocated to the claimant.

All bond amounts are synthetic bookkeeping units; the contracts do not receive or transfer GEN or tokens. Local tests mock validator outputs and do not establish distributed consensus. The relevant-record lookup is deliberately bounded to five recent records and can miss relevant rulings.

## Distinctiveness

**Local distinction: present, with a clear boundary.** The named assertion-court projects judge evidence-based truth for a claim, appeals, or stale-refund conditions. Liability Cascade attributes a violation to a pipeline step. Precedent Court instead judges whether a proposed holding fits earlier holdings, freezes cited records, and carries each accepted decision into later cases. The meaningful distinction is the compounding precedent state and its consistency check, not the use of an LLM, synthetic bonds, or court terminology. Final Offer Arbitration judges which of two sealed offers is closer to current evidence and pays that amount; it does not carry rulings across cases. These are local comparisons, not ecosystem-wide originality claims.

The optional `overrules` field remains metadata only. The supplied strict consistency rule rejects any cited contradiction, so accepted overruling behavior is not implemented; this limitation is documented rather than silently changing the deployed rule.

## Evidence readiness

**Explorer evidence verified.** The direct Studio Explorer pages displayed the expected addresses and deployment transactions, showed a connected Explorer state, and included the live demo transactions. Registry displayed 6 transactions; Court displayed its deployment and the Case A/B/C decisions and related transactions. See [`verification/explorer-checks.json`](../verification/explorer-checks.json) for the address-by-address record and [`verification/studionet-demo.json`](../verification/studionet-demo.json) for finalized receipts and direct readbacks.

The project is technically and live-demo ready, but public repository evidence is unavailable because `gh auth status` reports no authenticated GitHub CLI session. Per the requested stop rule, no alternate authentication path was attempted. The local repository is initialized, and the staged payload audit passed with zero findings; see [`verification/secret-audit.json`](../verification/secret-audit.json). No public URL can be claimed until publication succeeds.

## Failures, skipped work, and defaults

- The first throwaway ProbeCaller deployment attempt failed because its constructor did not convert the registry string to `Address`. The corrected deployment passed the full probe; the failed probe is not submission evidence.
- GitHub repository creation and push are blocked by the unauthenticated GitHub CLI. No workaround was attempted.
- The overrule field is retained but cannot override the strict contradiction rule. No source changes were made after the live deployment.
- The claimant alone proposes because only the claimant posts the tracked case bond. A split's odd unit goes to the respondent. The proposer slash is one quarter of the original bond, with the documented cap and refund rules.
- The StudioNet Builder Portal was not opened or submitted to. No points or acceptance are promised.
