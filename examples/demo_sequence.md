# Demo sequence

The live sequence requires a deployed contract address and working StudioNet access. Use the exact contract source in `contracts/precedent_court.py`.

1. Deploy `PrecedentCourt(180)` and record the receipt and source hash.
2. Call `seed_genesis_precedents` with the bounded JSON in `genesis_precedents.json`. Read P1 and P2 back directly.
3. Open Case A, receive/respond or let the response window close, propose a holding citing P1, then adjudicate it consistently. Read the new P3 and verify the exact holding and accounting.
4. Open Case B and propose a direct contradiction of P3. Record the 25% slash and unchanged remaining proposal count. Submit a second proposal with a fact-specific distinction and read the accepted P4.
5. Open Case C, cite P4, adjudicate consistently, and read back P5. Verify the later case actually consumed the earlier case's precedent.
6. Save each transaction hash, lifecycle observations, finalized receipt, case/citation/precedent views, Explorer transaction URL, and final accounting.

All units are synthetic. Do not describe these results as a real escrow or token payout.
