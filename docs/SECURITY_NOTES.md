# Security notes

Synthetic bookkeeping units only. No GEN or token is locked or transferred.

The Registry trusts its one-time deployer binding and genesis seed. Only the bound Court appends. Original records are immutable; overruling is a separate write-once map. Code validates cited targets and the exact append payload, including the 400-character question bound, before entering a pending append. Settlement waits for the complete finalized Registry record; retries are idempotent. Each party posts its own synthetic bond; rejection slashes only the proposer.

The model compares precedent relations, distinctions and overrule justification through independent leader/validator calls. Code recomputes consistency and uses fixed accounting; the supplied boolean cannot override enums. Reasons are bounded and excluded from consensus comparison.

Keyword overlap plus outcome bonus is not semantic search. The fixed 128-record cap bounds a linear scan but does not establish exhaustive relevance. Historical record labels are snapshots. There is no cancellation for stalled proposals; one pending append serializes finalization.

Evidence and justifications are untrusted user-supplied text, not authenticated facts. Prompts instruct models to treat them as data, but this does not prove resistance to prompt injection. Consensus establishes agreement under the comparison, not objective fairness or factual correctness. Saved local tests mock models; live receipts establish the recorded scenarios only. No independent security audit is claimed.

Encrypted signer material and pending salts stay outside the repository. Ignore rules exclude environment files, encrypted blobs, signer files, virtual environments, caches and secret JSON. Audit exactly the tracked Git payload before every push; classify public transaction hashes separately from credentials. Never print credential-helper output. The Builder Portal is not opened or submitted.
