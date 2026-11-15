# Security notes

## Trust and authority

- A deployer may seed up to three genesis precedents exactly once. Those rules are trusted deployer input and are marked `genesis=true`.
- Only the bonded claimant may propose because the requested `respond` signature has no respondent bond argument. The respondent may answer before the frozen deadline.
- The case outcome is claimant supplied. Validators assess only consistency with the snapshots; they do not decide the merits or payout.
- The Registry has a one-time deployer binding and only its bound Court may append. Genesis seeding is separate and limited to three trusted entries.
- Court settlement waits for a finalized asynchronous Registry append, then verifies the complete record and sequence through Registry views. Repeated appends by the same case reference are idempotent; a conflicting retry is rejected.
- Evidence is supplied as bounded text. It is not fetched, authenticated, or proven true by this contract.

## Model and consensus

- Prompts label all case text as untrusted data and prohibit treating embedded instructions as policy.
- Model JSON has an exact schema, bounded list sizes, enum normalization, exact record IDs, bounded reasons, and a recomputed `consistent` value.
- The validator independently reruns the judgment and compares only ordered relation enums, distinction enums, and the derived boolean. Free-text reasons do not affect state or consensus.
- Malformed output and model errors revert before case or accounting state changes.
- Relevance retrieval uses at most five recent records selected by same outcome or keyword overlap. It can miss relevant precedent; this is not exhaustive legal search.
- The specification's overrule pointer conflicts with its rule that any cited contradiction makes the proposal inconsistent. This version stores the optional field but does not authorize contradictory overrides.

## Accounting and operational limits

- Bond units are synthetic numbers. No real GEN, token, or other asset is held or transferred.
- A consistent ruling distributes the remaining bond by the proposed outcome. `SPLIT` assigns an odd unit to the respondent.
- An inconsistent proposal transfers a fixed quarter of the original bond (at least one unit, capped by the remaining balance) to the respondent. Two failures close UNRESOLVED; a fixed fee is counted and the remainder is returned to the claimant.
- Case count is capped at 64, precedent count at 128, citations at three, surfaced precedents at five, genesis precedents at three, and all user text/JSON is bounded.
- There is no external security audit. See `verification/studionet-demo.json` for the scope of the live source, finality, and readback evidence.

## Secrets and publication

The `.gitignore` excludes `.env`, `*.dpapi`, signer-named files, secret JSON files, virtual environments, caches, and build artifacts. Live signer material is DPAPI-encrypted outside this repository. The exact staged payload listed by `git ls-files` passed the final pre-publication audit with zero findings; see [`secret-audit.json`](../verification/secret-audit.json). The audit classified public deployment, demo, and probe transaction hashes separately from sensitive material.
