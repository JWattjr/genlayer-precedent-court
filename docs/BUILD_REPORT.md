# Build report — Precedent Court

Review date: November 16, 2026 (Africa/Lagos). The user's November 11 guidance is learned review guidance, not official scoring criteria. No points or maximum score are promised.

## Technical readiness

The revised source passed full GenVM lint and ABI validation before deployment. 26 direct cases passed in the pinned isolated environment; 26 also passed from a clean git archive HEAD copy. The exact archive commit, interpreter and versions are in verification/tests.txt. Local models are mocked and validator callbacks are explicitly checked; real consensus evidence is the separately recorded live run.

Registry and Court each passed 3 lint checks; both preserved probe contracts also passed 3 each (12 total). The 400-character cross-contract bound, balanced facts summary, real overrule mapping, proposer-specific bonds, two-attempt cap and ranked retrieval have regression coverage.

All fresh deployed source hashes equal local source SHA-256. A accepted P3; B rejected/slashed the contradiction then accepted distinguished P4; C was proposed by the respondent and created P5 from P4; D created P6 through a justified overrule with old record unchanged; E rejected/slashed an unjustified overrule and remains open with 70 synthetic units held.

## Distinctiveness

The meaningful distinction is immutable rule compounding and justified supersession across independent cases, with proposals and rejection costs attributable to either bonded party. This strengthens the comparison against the user's earlier single-claim court/appeal mechanisms, liability attribution and evidence retraction. It is not merely adding a list to an appeal.

These are local comparisons only. Actual custody, authenticated evidence, external adoption and ecosystem-wide novelty have not been established. Consensus does not prove fairness.

## Evidence readiness

Public repository: https://github.com/JWattjr/genlayer-precedent-court. Current contract entries:

- **PrecedentRegistry:** [StudioNet contract](https://explorer-studio.genlayer.com/address/0x78a120F66BE45155d639a302880b9d0D96661465)
- **PrecedentCourt:** [StudioNet contract](https://explorer-studio.genlayer.com/address/0xb473bbC3505Ccd102f5817127f137EBBd4141e9A)

Fresh transactions, finality, execution results, direct readbacks and settlement arithmetic are in verification/studionet-demo.json. Source hashes are in deployments/studionet.json. Direct contract pages and demo rows are checked in verification/explorer-checks.json. Only fresh addresses are current evidence. Historical addresses remain in DESIGN.md. The final indexed-payload secret audit is in verification/secret-audit.json.

## Failures, defaults and limits

- The first package-install attempt hit sandbox cache permissions. The explicit project cache/network retry installed every requested pin successfully.
- Remote latest-runner lookup failed DNS inside the sandbox; lint and ABI checks succeeded with the cached pinned runner.
- The older installed genlayer-test 0.29.2 failed during setup as expected; the requested 0.30.0rc2 passed, including the clean archive check.
- Initial adapted test assertions expected old error text/accounting; they were corrected to the deliberate new rules before the full passing runs.
- The Registry is capped at 128 records. Ranked keyword retrieval can miss semantic relationships. Case E remains open with 70 held units after the required first rejected attempt. A stale overrule target fails rather than silently being changed.
- Synthetic units only; evidence is user-supplied and unauthenticated. No real collateral, fairness guarantee or independent security audit is claimed.
- Builder Portal was not opened or submitted. No source revisions reuse old deployment evidence.

The first revised Court release failed Case A with [LLM_ERROR] citation judgment count and no accepted ruling. The required judgment IDs/counts were made explicit in the source prompt; lint, all tests and the clean Git archive test were rerun before another fresh Registry/Court deployment. The failed pair is separately listed as superseded in DESIGN.md. Its receipt is preserved in the external first-revision run state; it is not claimed as successful evidence.

The clean-archive byte check caught Git's line-ending conversion on an unchanged file. Contract-source attributes and index handling were corrected; the final clean archive contains the same contract bytes as the local/deployed SHA-256 evidence.

On the superseded second-revision pair, Case B twice finalized with MAJORITY_DISAGREE, including a source-unchanged retry, and left the frozen case PROPOSED. Failed-consensus transactions and receipts are retained; the runner now requires both execution SUCCESS and MAJORITY_AGREE before trusting a transaction, followed by a direct state readback. A transient StudioNet HTTP 502 before retry submission was resolved by retrying. These are recorded failures, not successful transitions.

Before the final deployment, an additional canonical-JSON Unicode boundary was found and fixed. The 26th regression checks that the complete encoded append payload is rejected before any model call or pending mutation. All 26 tests, full lint/ABI checks and the clean Git archive run were repeated before deployment. The final negative Case B input is an explicit logical contradiction of P3.

In the final release, the first Case E adjudication finalized with MAJORITY_DISAGREE and left the case PROPOSED, with no slash. Its receipt is retained separately. The unchanged frozen proposal was retried; only a subsequent MAJORITY_AGREE transaction and exact readback may establish the required rejection/slash. A gateway error during C receipt polling was resumed from its saved hash, with no duplicate write.
