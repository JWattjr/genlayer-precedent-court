# StudioNet demo plan

The live runner is `scripts/studionet_release.py`. It deploys the Registry and Court, binds them, seeds two trusted genesis precedents, synchronizes the Court's expected Registry count, and executes Cases A/B/C. It uses the DPAPI signer file outside this repository. All bonds are synthetic accounting units.

## Release and append sequence

1. Deploy `PrecedentRegistry` and `PrecedentCourt(registry_address, respond_window_seconds)`.
2. Bind the Court in the Registry, seed two genesis records, and call `sync_registry_count`.
3. For each consistent adjudication, capture the parent receipt's emitted child hash, wait for the Registry append to finalize, poll the direct Registry views, then call `finalize_case`. The Court must still show the case bond held before this last step.
4. Compare deployed contract source bytes against the local release files and retain the direct readbacks with the transaction receipts.
5. Open both direct GenLayer Explorer contract pages on StudioNet and verify the deployed contract and demo transactions before recording Explorer evidence.

## Case A — consistent ruling creates P3

The seller misses a signed May 1 delivery date and there is no later written extension. The buyer's proposed holding cites P1. A consistent result should create P3 and settle the 40-unit synthetic bond to the claimant.

## Case B — contradiction slashes; a distinguishing revision creates P4

The parties later sign an extension to May 4 and the seller delivers by that date. The first proposal says the original date controls despite the signed extension, contradicting P3. That attempt should slash 10 units and return the case to `READY_TO_REPROPOSE`. The second proposal explains how the signed amendment distinguishes P1/P2/P3; if consistent, it creates P4 and settles the remaining 30 units.

## Case C — later case cites P4

A new dispute has a signed extension and delivery by the amended date. The claimant cites P4. A consistent result creates P5 and demonstrates that the Registry entry created by Case B is available to a later dispute.

## Evidence capture

The release record contains every write hash, acceptance/finality status, receipt outcome, child transaction, direct Registry/Court readback, and settlement arithmetic. `verification/studionet-demo.json` and `deployments/studionet.json` are populated from the final source-matched run. `verification/explorer-checks.json` is completed only after direct browser checks; probe contracts are never used as submission evidence. The Builder Portal is not used.
