# Submission draft — Precedent Court

## Title

Precedent Court

## Summary

Validators judge whether proposed rulings fit earlier holdings and whether a single cited rule should be overruled. Both bonded parties may propose; accepted rulings compound in an immutable Registry. **Synthetic bookkeeping units only; no GEN or token is locked or transferred.**

## Mechanism and division of responsibility

The model independently classifies cited/surfaced relations, supplied distinctions and overrule justification. Code ignores the supplied consistency boolean and computes consistency from normalized enums, accepting a contradiction only on the single justified overrule target. Code enforces party bonds, proposer-specific slashing, two total attempts, outcome settlement, append-only history and asynchronous append finalization.

## Distinctiveness

Unlike court-release, court-review, court-appeal and the optimistic assertion court's single-claim truth/appeal judgments, this project carries holdings into independent future cases and permits explicitly justified supersession without changing old records. Two-sided proposals strengthen that cross-case distinction. Liability Cascade and evidence retraction track pipeline liability or changing evidence rather than active rule evolution. The companion Arbitration chooses a current-dispute amount and has no precedent history.

These are comparisons with the user's named local projects, not an ecosystem-wide originality claim. Evidence is unauthenticated; consensus does not establish fairness. No points are promised.

## Live outcomes

A accepted P3; B rejected/slashed the contradiction then accepted distinguished P4; C was proposed by the respondent and created P5 from P4; D created P6 through a justified overrule with old record unchanged; E rejected/slashed an unjustified overrule and remains open with 70 synthetic units held.

## Separate evidence entries

Each current contract has its own direct Explorer entry. Superseded deployment addresses and transactions are excluded from this submission evidence.

1. **GitHub repository:** [genlayer-precedent-court](https://github.com/JWattjr/genlayer-precedent-court).
2. **GenLayer Explorer Contract — PrecedentRegistry:** [Verified StudioNet contract](https://explorer-studio.genlayer.com/address/0x78a120F66BE45155d639a302880b9d0D96661465). Evidence type: GenLayer Explorer Contract.
3. **GenLayer Explorer Contract — PrecedentCourt:** [Verified StudioNet contract](https://explorer-studio.genlayer.com/address/0xb473bbC3505Ccd102f5817127f137EBBd4141e9A). Evidence type: GenLayer Explorer Contract.
4. **Key transaction — Case A accepted P3:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0x59dac8545dc14d0f144ae786f3b1243b39d5a7a86b08b661d3b280cbc1b0416b).
5. **Key transaction — Case B contradiction rejected/slashed:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0x40e5e0e73a409d8acb183dda835a735b1f29aff3cac62b58c805b355546c9896).
6. **Key transaction — Case B distinguished P4:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0xca133fbe5943f114816e7a36601a666a4927ddc5ba3f47eac854949aa04b9a76).
7. **Key transaction — Case C respondent proposal cites P4:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0x0ed3554f08228b69804d2d7b5bb6ce02bdb847338a31e66393e323916f6193eb).
8. **Key transaction — Case C accepted P5:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0x86a77f25acaaa9e4d795dfbd04ee129f43c82c9fbce0f21bd0bb6e5ce4c37a45).
9. **Key transaction — Case D justified overrule P6:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0xfea058c8b41dbed2c252d93bb3cd4721359243a2b9b4b337e7f9277ad9912f7d).
10. **Key transaction — Case E unjustified overrule rejected:** [Finalized transaction](https://explorer-studio.genlayer.com/tx/0xd38503b8dc65288fced96958205b8fb5ee5d8951d45e115fffe8f6935ba33d2d).
11. **Deployment and source hashes:** [deployments/studionet.json](deployments/studionet.json).
12. **Receipts and direct readbacks:** [verification/studionet-demo.json](verification/studionet-demo.json).
13. **Browser Explorer checks:** [verification/explorer-checks.json](verification/explorer-checks.json).
14. **Tests including clean archive run:** [verification/tests.txt](verification/tests.txt).
15. **Lint and ABI validation:** [verification/lint.txt](verification/lint.txt).
16. **Publication audit:** [verification/secret-audit.json](verification/secret-audit.json).

17. **Live revision assertions:** [verification/revision-qa.json](verification/revision-qa.json).

Prepared text only. The Builder Portal has not been opened, filled or submitted.
