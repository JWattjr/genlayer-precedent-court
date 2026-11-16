# Fresh StudioNet demonstration

Deploy revised Registry and Court; bind Court; seed two genesis records; then sync Registry count. Source hashes must match before demo transactions.

- A: both parties post 40-unit synthetic bonds; consistent claimant proposal appends P3; finalize only after the Registry child write is finalized and directly readable.
- B: both post 40; contradictory proposal rejected with 10 units paid to respondent; revised proposal distinguishes P3, appends P4, then settles the remaining 70 units.
- C: both post 40; respondent proposes a P4-citing rule; accepted append creates P5. Record proposer_role and settlement.
- D: both post 40; justified overrule of the categorical oral-amendment prohibition creates P6. Record the original target before/after, separate overruled_by mapping and inactive flag. Assert the original record is unchanged.
- E: both post 40; unjustified overrule rejected and slashed 10. Stop this demo at READY_TO_REPROPOSE with 70 units held.

Capture every transaction and triggered append, execution success, finality and direct readbacks. Only new deployment addresses and transactions are submission evidence. Verify both new address pages in the Studio Explorer browser.
