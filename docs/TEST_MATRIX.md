# Test matrix

Saved pinned direct suite: 26 passing cases. Clean git archive run: 26 passing cases. See ../verification/tests.txt for exact interpreter, package versions, archive commit and command. Local tests mock LLM responses and explicitly exercise validator callbacks; they do not reproduce network consensus.

| Area | Coverage |
|---|---|
| Registry | Outsider rejection, idempotent exact append, conflicting retry rejection, actual immutable genesis overrule mapping and active status, duplicate overrule rejection. |
| Citations | Nonexistent cited ID rejection, frozen citation text, compounding later-case citation, historical overruled_by label. |
| Overrules | Justified contradiction accepted; unjustified overrule rejected/slashed; target must be cited and exist; already-overruled target rejected; another contradiction still fails; model boolean cannot override computed result. |
| Parties and accounting | Respondent proposal and respondent slash paid to claimant; mixed parties share two attempts; both consistent winners and split; odd split after slash; per-party fee/refund at unresolved; default with claimant bond only; global conservation. |
| Retrieval | Actual ranked helper finds an older high-overlap record beyond five recent rows; deterministic scores and recency tie-break; overruled records excluded; surfaced scores retained. |
| Safety | 401-character question rejected before state entry; 400-character boundary remains appendable; summary preserves each party's evidence field; oversized/malformed inputs fail without state change. |
| Async behavior | Consistent adjudication holds bonds pending Registry append; finalized readback permits settlement. Direct tests use an adapter for cross-contract messages; real emitted child writes and finality are separately established by live evidence. |

Required live scenarios: A accepted P3; B contradiction rejected then distinction accepted P4; C respondent proposal cites P4 and creates P5; D justified overrule creates P6 with old record unchanged; E unjustified overrule rejected/slashed. E intentionally leaves one attempt and held units.

The 26th regression rejects an oversized canonical Unicode append payload before model execution or pending-state mutation, while retaining the original proposed case and conserved bonds.
