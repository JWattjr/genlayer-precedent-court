# Precedent Court design

## Mechanism and boundary

A claimant opens a bounded dispute and posts a synthetic case bond. The respondent may file a position and evidence before the frozen response deadline. The claimant proposes a normalized outcome and holding with one to three existing precedent citations. The Court reads the Registry and snapshots each cited record at proposal time. Validators independently judge whether the proposed ruling is consistent with those snapshots and up to five recent relevant uncited records. Code accepts or rejects the proposal and performs the fixed bond arithmetic. A consistent ruling is appended by the Court to the separate Registry and becomes available to later cases.

Validators do not decide the merits, invent an outcome, choose a payout, or write the Registry. The claimant chooses the proposed outcome; validators judge only precedential consistency. The Court owns deadlines, citation snapshots, attempt limits, enum normalization, and synthetic bond accounting. The Registry owns immutable precedent order and access control. Evidence is user-supplied text; it is not authenticated or fetched by either contract.

## Decisions made

- **Two-contract design:** The Step 0 StudioNet probe passed all three checks. The implemented API is `gl.get_contract_at(address).view().get(key)` for reads and `gl.get_contract_at(address).emit(on="finalized").append(key, value)` for emitted writes. The child append became visible 33.158 seconds after the probe parent finalized. Probe contracts are throwaway and are not submission evidence.
- **Asynchronous append safety:** A consistent adjudication enters `PRECEDENT_PENDING`, stores the exact append payload, and emits the Registry write. The Court holds the remaining bond until `finalize_case` reads back the expected case reference, ID, sequence, and complete record. `retry_precedent_append` is allowed after 60 seconds and Registry appends are idempotent by case reference, so a repeated child cannot create a duplicate. Only one Court append may be pending at once.
- **Registry initialization:** The Registry deployer binds one Court address exactly once and may seed up to three genesis precedents exactly once. Genesis rows are marked `genesis=true`; their initial rules are trusted deployer input. The Court deployer synchronizes the Registry count once after binding and seeding, before opening cases.
- **Equivalence:** Each adjudication uses `gl.vm.run_nondet_unsafe` with an independent validator call, following the custom leader/validator pattern used by earlier workspace court and forecast projects. Strict parsing converts relation and distinction labels to enums before comparison. Validators compare only ordered relation enums, distinction enums, and the `consistent` boolean; explanatory text is bounded but excluded from comparison.
- **Outcome enum:** `CLAIMANT_WINS`, `RESPONDENT_WINS`, and `SPLIT`. The claimant proposes the outcome. For a consistent ruling, code allocates the remaining bond to the selected winner, or splits it evenly with any odd unit assigned to the respondent.
- **Bond ownership:** `open_case` records the case bond for the claimant. Since `respond` has no bond argument in the requested interface, only the bonded claimant may propose. This makes the “proposer's bond” explicit and prevents slashing a party that did not post the tracked bond.
- **Failed proposals:** Each inconsistent attempt slashes `max(1, floor(original_bond / 4))` from the remaining bond to the respondent, capped by the remaining amount. After two failed attempts, the remaining amount pays a 10% fee (`max(1, floor(remaining / 10))` when nonzero) and the rest is returned to the claimant. All amounts are synthetic accounting units; no GEN or token is received or transferred.
- **Overrule field:** Registry rows retain an optional `overrules` identifier and validate that it points to an existing record. The requested strict rule says any cited `CONTRADICTS` relation makes a proposal inconsistent; the Court therefore does not treat an overrule pointer as an exception and currently appends `overrules=null`. An accepted contrary override is not implemented under this rule.
- **Relevant-record heuristic:** Up to five latest records are surfaced when their outcome matches the proposal or their normalized keyword set overlaps the case. This bounded retrieval is a relevance hint, not exhaustive precedent search. `# ponytail: same-outcome/keyword-overlap retrieval is capped at five recent records and can miss relevant holdings.`
- **Response default:** A response is accepted strictly before the deadline. Once the deadline is reached, the claimant may propose with the case marked `DEFAULT`; no response is fabricated.
- **Bounds:** Cases and precedents are capped; user text, arrays, JSON, enum values, and reasons are length-bounded. Malformed model output raises an `[LLM_ERROR]` and leaves case and accounting state unchanged.

## State and transitions

`WAITING_RESPONSE -> READY_TO_PROPOSE -> PROPOSED -> PRECEDENT_PENDING -> FINAL`

An inconsistent first proposal moves to `READY_TO_REPROPOSE`. A second inconsistent proposal moves to `UNRESOLVED`. A consistent proposal remains `PRECEDENT_PENDING` until the asynchronous Registry append is visible and independently verified by `finalize_case`; only then does the Court settle the remaining bond and mark the case `FINAL`. The account conservation invariant is `bonds_in = paid_claimant_units + paid_respondent_units + fee_units + held_units` throughout pending and terminal states.

Each case stores the frozen input, response/default marker, citation snapshots, surfaced records, normalized validator result, pending append payload when applicable, and settlement arithmetic. `get_case_citations` returns the exact cited snapshots and surfaced context seen by validators.

## Consistency evaluation

The model must return strict JSON with `per_citation`, `per_distinction`, and `consistent`. Each citation relation normalizes to `SUPPORTS`, `DISTINGUISHABLE`, or `CONTRADICTS`; each requested distinction normalizes to `VALID` or `INVALID`. The contract recomputes `consistent` as true only when no cited or surfaced item contradicts and every supplied distinction is valid. A `DISTINGUISHABLE` result for a cited precedent requires a bounded proposal reason and a corresponding `VALID` judgment. Reasons are retained as leader explanations but are not part of consensus comparison.

## Cross-contract probe sources

The throwaway probe deployed `ProbeRegistry` and `ProbeCaller` to StudioNet. It established an in-transaction cross-contract view read, a finalized emitted write visible by a direct Registry read, and rejection of a direct append from an outsider. The parent and child hashes, finality, readbacks, and latency are recorded in [`probe-result.json`](../probe/probe-result.json). The first caller deployment attempt failed because its constructor did not convert the string to `Address`; the corrected second attempt passed all checks.

- [Interacting with Intelligent Contracts](https://docs.genlayer.com/developers/intelligent-contracts/features/interacting-with-intelligent-contracts)
- [Internal Messages](https://docs.genlayer.com/developers/intelligent-contracts/features/messages)
- [Non-determinism and deterministic side effects](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism)

## Known design tension

An explicit overrule ordinarily permits a later holding to supersede an earlier contrary rule. The prompt also requires a cited contradiction to fail consistency. This implementation follows the strict consistency gate and records the optional field without an exception. This limits accepted overruling behavior; it is surfaced rather than silently changing the supplied rule.
