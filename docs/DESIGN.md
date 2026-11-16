# Precedent Court design

Synthetic units only: no GEN or token is locked or transferred.

## Mechanism

The Court freezes case inputs and cited Registry records. Either party that posts its matching synthetic bond may propose an outcome, holding, 1–3 citations, fact-specific distinctions, and an optional justified overrule. Independent validators classify precedent relations, distinctions, and overruling. Code computes consistency from normalized enums, controls the two-attempt limit, and settles all bookkeeping. An accepted ruling enters PRECEDENT_PENDING, emits a Registry append, and waits for a direct finalized readback before finalize_case releases the held units.

The Registry owns immutable ordered records and a separate append-only overruled_by mapping. Only its bound Court may append. Genesis seeding is trusted deployer input, once, up to three records. Initialization is deploy Registry, deploy Court, bind Court, seed genesis, then sync count. Sync must follow seeding so the expected count is correct.

## Decisions made

This revision was explicitly confirmed by the user on November 16, 2026, following the review. The changes are new deployments, not upgrades to the old contracts.

- **Rule conflict:** the old deployed rule rejected every CONTRADICTS on a cited or surfaced precedent. The user requested a new rule: a contradiction is tolerated only for the single cited overrule target when its enum is JUSTIFIED. Every other contradiction and any UNJUSTIFIED overrule fails.
- **Consensus schema:** per_citation contains id/relation/reason; per_distinction contains id/status; per_overrule is empty or one id/status with JUSTIFIED or UNJUSTIFIED. The consistent field must be boolean but its supplied value is ignored. Code derives consistency. Validators independently rerun the task using gl.vm.run_nondet_unsafe and compare only normalized enum sequences; prose is bounded and excluded.
- **Overrules API:** propose_ruling appends optional overrules and overrule_reason string fields; empty strings represent absence. The target must exist, be cited, and be active. Reasons are required for an overrule and bounded at 240 characters. Genesis may be overruled. A target that becomes overruled before adjudication is rejected instead of silently replaced.
- **Append-only history:** no original record is edited. A separate write-once target-to-replacement mapping supports get_overruled_by and is_active. Exact case-reference retries are idempotent, including repeated overruling appends; a different replacement of an already-overruled target fails.
- **Bonds:** respond takes a matching explicit bond. Either bonded party may propose. Only the claimant may propose after response default. Two attempts are shared per case. Each rejection slashes max(1, original_bond // 4), capped by the proposer's remaining bond, to the other party.
- **Settlement:** a consistent winner receives both remaining bonds. SPLIT divides their total with the odd unit to the respondent. After two rejections, each party separately pays max(1, remaining // 10), capped at its remaining balance when nonzero, and receives the rest. Already paid slashes stay paid. Held balances are zero on terminal paths.
- **Retrieval:** score each active uncited Registry record by distinct keyword overlap plus same-outcome bonus 2. Sort descending score then descending immutable sequence; take up to five positive-score rows. Each row includes retrieval_score. The scan is bounded by MAX_PRECEDENTS=128. Keyword lookup can miss semantic relationships and its cost grows linearly.
- **Historical citations:** snapshot overruled_by with the cited record. Overruled records are excluded from uncited retrieval. Explicit cited distinctions require proposal reasons; automatically surfaced uncited records may be classified factually distinguishable from their supplied record because the proposer did not select them.
- **Length fix:** questions are bounded to the Registry's 400 characters. The complete append payload is built and checked before model adjudication or pending-state mutation. Facts summaries reserve space for question, each position, and each evidence source, avoiding claimant-first truncation.
- **Async safety:** hold bonds until the exact complete Registry record is visible and finalize_case checks ID, sequence, case reference, and fields. One append may be pending at a time. Retry after 60 seconds sends the identical payload. No cancellation that might double-settle is added.
- **Live Case E:** the requested demonstration stops after its first rejection; it remains READY_TO_REPROPOSE with 70 synthetic units held. It is not reported as a terminal payout.
- **Toolchain:** remove the empty studio_devnet entry; pinned direct tests use the cached v0.6.0-rc5 runner. A clean git archive copy is tested with exactly the four requested package versions. Live signing uses the working 0.18.0 client environment separately; this does not change the pinned contract runner or test dependency requirements.
- **Fresh evidence:** revision run state is isolated under the external encrypted live-run folder. The historical probe folder is preserved and is not submission contract evidence.

## Bounds and limitations

64 cases; 128 Registry records; three citations; five surfaced records; two shared proposal attempts; three genesis records; bounded user/model text. Evidence is user-supplied and unauthenticated. Consensus establishes agreement, not factual truth or fairness. Retrieval is lexical, not semantic or exhaustive. There is no real asset custody. Unsubmitted cases can remain open; a stale overrule proposal may require a new case. One pending append serializes acceptance. No ecosystem-wide originality or points are promised.

## Superseded deployments

| Contract | Superseded StudioNet address | Reason |
|---|---|---|
| PrecedentRegistry | 0x0FD8b71034265680EC8B46c6Ff8D06085e71f998 | Replaced by real append-only overruling and new views. |
| PrecedentCourt | 0x68640Ef247219FF0B40d5A7a60c0F8A572178507 | Replaced by overruling, two-party bonds, ranked retrieval and QA corrections. |

These addresses are historical only. New source requires fresh deployment, live readbacks and Explorer checks.

## Revision deployment retry

The first revised Court failed Case A with [LLM_ERROR] citation judgment count: model output omitted required cited/surfaced entries. No ruling was accepted. The prompt now explicitly enumerates all required judgment IDs and exact array lengths/order, while parsers remain strict. This documented reliability correction requires another fresh deployment and new live evidence.

Additional superseded first-revision addresses:
- PrecedentRegistry: 0xD55463770A7c7936eb33B6B862540f650A32ceA9.
- PrecedentCourt: 0x6c1C865D0d37c26Afc484559333E0036a271164C.

The failed receipt remains preserved in the external first-revision run state and is not successful new-source evidence.

## Probe

The preserved throwaway probe established cross-contract view access, emitted writes and outsider rejection. The final readback was visible 33.158 seconds after parent finality. See ../probe/probe-result.json. The revised release separately proves actual Registry/Court interactions again.

Contract source files are exempt from Git line-ending conversion so the published bytes, local bytes and deployed SHA-256 can agree exactly on Windows. This changes Git handling, not deployed program behavior.

A finalized transaction is not an accepted state transition when consensus reports MAJORITY_DISAGREE. The release runner now requires MAJORITY_AGREE plus leader execution SUCCESS, checks direct state, preserves failed-consensus receipts, and permits bounded retries of the exact unchanged frozen proposal. This changes evidence collection, not contract source or the consensus comparison.

The append validation also checks the total canonical JSON length before any model work or pending mutation. This covers Unicode expansion even when individual fields fit. A regression proves an oversized encoded record leaves the case PROPOSED and bonds unchanged. This guard and clearer relation definitions require a final fresh Registry/Court pair. The Case B negative demo now uses a direct logical negation of P3 rather than an ambiguous rule about an extended date; this changes demo input only.

Additional superseded second-revision pair:
- Registry: 0xeB2f1fD8829088d54Bb10b564a5a20ff41F97fE4.
- Court: 0x0275c538405e0FaD5D4a66078BED01C7200fe9dE.

The second pair's Case A completed, but Case B twice finalized without consensus and did not change state. Failed receipts are retained; no such receipt is successful evidence for the final source.

The final release encountered a transient gateway response during receipt polling after C's response hash was saved. Read-only RPC and receipt calls now have bounded transport retries. Deploy/write submission calls are deliberately never blindly retried; resumed runs use recorded hashes, preserving duplicate-submission safety. Contract source is unchanged by this runner correction.
