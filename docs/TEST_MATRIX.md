# Test matrix

Lint ran before the direct suite. Full outputs are saved in `verification/lint.txt` and `verification/tests.txt`.

**13 direct tests passed.** The suite uses the pinned workspace environment (`genlayer-test==0.30.0rc2`, `genlayer-py==0.19.0rc2`, `genvm-linter==0.11.1rc2`, `pytest==9.1.1`) and cached GenVM bundle `v0.6.0-rc5`.

| Requirement | Coverage |
|---|---|
| Registry rejects append from a non-Court address | `test_registry_rejects_append_from_non_court_address` |
| Retried identical Registry append is idempotent; changed duplicate is rejected | `test_registry_append_is_idempotent_for_the_same_case_record` |
| Nonexistent citations reject without changing escrow | `test_citing_nonexistent_precedent_is_rejected` |
| Proposal freezes citation text while a later precedent is appended | `test_citation_snapshot_is_frozen_when_a_later_precedent_is_appended` |
| Consistent ruling waits for append and settles only after finalization | `test_consistent_ruling_waits_for_append_then_finalizes_and_settles` |
| All three final outcome distributions conserve the bond | `test_every_consistent_outcome_has_exact_conserved_settlement` (3 parameter cases) |
| Contradiction rejects, slashes a fixed amount, and permits a second distinguished proposal | `test_contradiction_slashes_and_allows_a_second_distinguishing_proposal` |
| Two failures close UNRESOLVED with exact refund, slash, fee, and conservation | `test_two_failed_attempts_close_unresolved_with_exact_refund_arithmetic` |
| A later case cites the earlier case's new Registry record | `test_case_two_cites_case_ones_new_precedent` |
| No response proceeds on default after the response deadline | `test_default_proceeds_after_response_window` |
| Oversized input and malformed model JSON reject without state changes | `test_oversized_inputs_and_malformed_model_json_are_rejected_without_state_change` |

Court tests use a fake Registry adapter at the cross-contract boundary because the local direct VM does not provide a separate deployed contract ledger. The Registry contract itself runs in direct mode for access-control and idempotency tests. The separate StudioNet probe establishes the real cross-contract read, emitted child write, child finality, direct readback, and outsider rejection. The project contracts' own live deployment and three-case demo are recorded separately in `verification/studionet-demo.json`.
