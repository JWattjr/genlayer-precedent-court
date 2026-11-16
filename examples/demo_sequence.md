# Revised demo sequence

All units are synthetic bookkeeping. No GEN or token is locked or transferred.

1. Deploy PrecedentRegistry with no constructor arguments.
2. Deploy PrecedentCourt with the Registry address and the chosen response-window seconds (the recorded release uses 7200).
3. Bind the Court once through Registry.bind_court, seed the two genesis records, then call Court.sync_registry_count.
4. Open a case with the claimant's bond. Respond through the designated respondent with position, evidence and a matching explicit bond.
5. Either bonded party may propose outcome, holding, cited-ID JSON and distinction JSON. Optional overrules and overrule_reason strings identify a single active cited target.
6. Adjudicate. For a consistent decision, wait for the emitted Registry child transaction and direct finalized record before finalize_case. The Court holds both balances until then.
7. Follow the five scenarios in docs/DEMO_PLAN.md: A/P3, B contradiction then P4, C respondent-proposed P5, D justified overrule/P6, E unjustified rejection.
8. Record the target before/after overruling and the separate get_overruled_by/is_active views. Original records must be unchanged.
9. Save every transaction, execution outcome, finality and readback. Verify the two current Explorer contract pages individually.

Use scripts/studionet_release.py for the exact recorded arguments. Signer data stays encrypted outside this repository. Do not use the superseded addresses as current evidence.
