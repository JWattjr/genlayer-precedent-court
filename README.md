# GenLayer Precedent Court

Precedent Court separates dispute adjudication from an append-only precedent Registry. A claimant proposes an outcome and holding with citations; validators judge consistency with the frozen cited rulings and a bounded set of recent relevant records. The Court decides all state changes and synthetic bond arithmetic. Each consistent ruling is appended to the Registry and becomes available to later cases.

## Project state

The StudioNet cross-contract probe passed its view-read, emitted-write, direct readback, and outsider-rejection checks. The released source therefore uses `PrecedentRegistry` and `PrecedentCourt`; a consistent case remains pending until its asynchronous Registry append is visible and `finalize_case` verifies the record.

- **PrecedentRegistry:** [StudioNet Explorer](https://explorer-studio.genlayer.com/address/0x0FD8b71034265680EC8B46c6Ff8D06085e71f998)
- **PrecedentCourt:** [StudioNet Explorer](https://explorer-studio.genlayer.com/address/0x68640Ef247219FF0B40d5A7a60c0F8A572178507)

All three live demos passed: Case A appended P3, Case B rejected and slashed a contradictory proposal before appending revised P4, and Case C cited P4 and appended P5. The source hashes match the deployed source. See [`probe/probe-result.json`](probe/probe-result.json), [`deployments/studionet.json`](deployments/studionet.json), [`verification/studionet-demo.json`](verification/studionet-demo.json), and [`verification/explorer-checks.json`](verification/explorer-checks.json) for probe results, deployment records, readbacks, and browser checks.

The exact tracked payload audit passed with zero findings; see [the audit](verification/secret-audit.json). Public repository: [genlayer-precedent-court](https://github.com/JWattjr/genlayer-precedent-court). No Portal form has been opened or submitted.

## Local checks

The project pins the requested package versions in `requirements.txt`. The source was linted and direct-mode tests were run with the cached GenVM runner `v0.6.0-rc5` in the existing workspace environment. The Court tests use a fake Registry adapter because the local direct VM does not provide a separate deployed contract ledger; the Registry itself is also tested directly for access control and idempotent retry behavior.

See [lint output](verification/lint.txt) and [test output](verification/tests.txt). Local tests mock the model and invoke the validator callback; they do not establish distributed consensus.

## Contracts and sequence

- `contracts/precedent_registry.py` owns genesis seeding, the one-time Court binding, immutable sequence IDs, retry-safe appends, and Registry views.
- `contracts/precedent_court.py` owns cases, deadline handling, citation snapshots, normalized adjudication, synthetic accounting, and append finalization.
- `probe/` contains the throwaway contracts used before selecting the two-contract design. They are not submission evidence.

Deploy the Registry, deploy the Court with the Registry address, bind the Court, seed genesis records, and call `sync_registry_count` before opening a case. After a consistent `adjudicate` transaction, wait for its triggered Registry child transaction and direct readback before calling `finalize_case`.

All bond amounts are synthetic bookkeeping units. The contracts do not accept or transfer GEN or tokens.

## Documentation

- [Design and decisions](docs/DESIGN.md)
- [Distinctiveness review](docs/DISTINCTIVENESS.md)
- [Security notes](docs/SECURITY_NOTES.md)
- [Test matrix](docs/TEST_MATRIX.md)
- [Live demo plan](docs/DEMO_PLAN.md)
- [Build report](docs/BUILD_REPORT.md)
- [Prepared submission draft](SUBMISSION_DRAFT.md)
