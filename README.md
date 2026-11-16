# Precedent Court

**Synthetic units only: no GEN or token is locked or transferred.**

Validators judge whether proposed rulings fit earlier holdings and whether a single cited rule should be overruled. Both bonded parties may propose; accepted rulings compound in an immutable Registry.

Public repository: [genlayer-precedent-court](https://github.com/JWattjr/genlayer-precedent-court).

## Project state

The revised source is freshly deployed on GenLayer StudioNet. All required live scenarios passed, and deployed SHA-256 hashes match local source. Only the addresses below are current evidence; superseded addresses are listed in [DESIGN.md](docs/DESIGN.md).

- **PrecedentRegistry:** [StudioNet contract](https://explorer-studio.genlayer.com/address/0x78a120F66BE45155d639a302880b9d0D96661465)
- **PrecedentCourt:** [StudioNet contract](https://explorer-studio.genlayer.com/address/0xb473bbC3505Ccd102f5817127f137EBBd4141e9A)

A accepted P3; B rejected/slashed the contradiction then accepted distinguished P4; C was proposed by the respondent and created P5 from P4; D created P6 through a justified overrule with old record unchanged; E rejected/slashed an unjustified overrule and remains open with 70 synthetic units held.

See [deployment/source hashes](deployments/studionet.json), [live receipts and direct readbacks](verification/studionet-demo.json), and [browser Explorer checks](verification/explorer-checks.json). Builder Portal was not opened or submitted.

## Run the tests

Saved results used Python 3.14.2 at exactly:

C:\Users\User\Desktop\IC phase 2\final-offer-arbitration\.venv\Scripts\python.exe

Pinned packages: genlayer-test==0.30.0rc2, genlayer-py==0.19.0rc2, genvm-linter==0.11.1rc2, pytest==9.1.1.

From a fresh Windows checkout, install and run the same pinned toolchain in a local environment:

~~~powershell
uv venv .venv --python 3.14
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -X utf8 -m pytest tests -o 'addopts=-p no:cacheprovider' -q
~~~

Result: 26 passing cases locally and 26 from a clean git archive HEAD copy. The archive commit, exact interpreter, versions and command are saved in [tests.txt](verification/tests.txt). The empty studio_devnet configuration entry was removed. Running with the older installed genlayer-test 0.29.2 fails during setup because the loader lacks import_calldata; [the compatibility record](verification/older-toolchain-check.txt) is an intentional expected-failure check, not the saved pinned-suite result.

Lint each source file with .venv/Scripts/genvm-lint.exe check contracts/<file>.py --json. All contract sources retain the concrete pinned runner hash; local direct tests use cached v0.6.0-rc5. Linter results are in [lint.txt](verification/lint.txt). Cached runner use followed a failed remote newest-runner lookup and does not change the requested runner pin.

## Scope and limits

Evidence text is user-supplied and unauthenticated. Consensus does not prove fairness or factual truth. Amounts are conserved bookkeeping only. Retrieval is lexical, can miss semantic relationships, and scans a fixed Registry capped at 128 records. Historical citations and accepted overruling are auditable; no old record is edited.

## Documentation

[Design/decisions](docs/DESIGN.md) · [security](docs/SECURITY_NOTES.md) · [distinctiveness](docs/DISTINCTIVENESS.md) · [test matrix](docs/TEST_MATRIX.md) · [build report](docs/BUILD_REPORT.md) · [submission draft](SUBMISSION_DRAFT.md).
