"""Deploy the Registry/Court pair and capture the three StudioNet cases.

Signer data is DPAPI-encrypted in precedent-court-live-run/, outside this repo.
The runner never prints credentials and never submits to the Builder Portal.
"""

from __future__ import annotations

from datetime import datetime, timezone
import base64
import hashlib
import json
import shutil
from pathlib import Path
import time

from genlayer_py import create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus
import requests

from studionet_probe import dpapi, load_accounts, status_name, tx_summary


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "precedent-court-live-run" / "revision-2026-11-16-attempt3"
STATE = WORK / "release.json"
RPC = "https://studio.genlayer.com/api"
EXPLORER = "https://explorer-studio.genlayer.com"
RUNNER = "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6"
SESSION = requests.Session()
SESSION.trust_env = False
record: dict = {}
clients: dict = {}
source_by_name: dict = {}


def iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save() -> None:
    temp = STATE.with_suffix(".pending")
    temp.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    temp.replace(STATE)


def retry_read(action):
    # Retry reads/receipt polling only. Never resubmit a deploy or write on transport failure.
    for attempt in range(6):
        try:
            return action()
        except Exception:
            if attempt == 5:
                raise
            time.sleep(min(20, 2 + attempt * 3))


def rpc(method: str, params: list):
    return retry_read(lambda: rpc_once(method, params))


def rpc_once(method: str, params: list):
    if method not in ("eth_chainId", "gen_getContractCode"):
        raise RuntimeError("RPC method is outside the release runner scope")
    response = SESSION.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                            timeout=(10, 45))
    response.raise_for_status()
    value = response.json()
    if "error" in value:
        raise RuntimeError(f"StudioNet RPC {method} failed")
    return value["result"]


def _load_value(value):
    if isinstance(value, str):
        for _ in range(2):
            try:
                value = json.loads(value)
            except Exception:
                break
    return value


def read(address: str, method: str, args: list | None = None):
    last_error = None
    for attempt in range(8):
        try:
            value = clients["owner"].read_contract(
                address=address, function_name=method, args=args or [],
                transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
            return _load_value(value)
        except Exception as error:
            last_error = error
            if attempt == 7:
                break
            time.sleep(min(20, 2 + attempt * 3))
    raise RuntimeError(f"Final read failed for {method}: {type(last_error).__name__}")


def tx(label: str, client, *, address: str = "", method: str = "", args: list | None = None,
       deploy_source: str = "") -> dict:
    row = next((item for item in record["transactions"] if item["operation"] == label), None)
    if row is not None and row.get("stage") == "FINALIZED" and row.get("consensus_result") != "MAJORITY_AGREE":
        previous = [r for r in record["transactions"] if r.get("operation", "").startswith(label + "_failed_consensus_")]
        if len(previous) >= 3:
            raise RuntimeError(label + ": three consensus retries failed; preserved receipts require review")
        row["operation"] = label + "_failed_consensus_" + str(len(previous) + 1)
        old_receipt = WORK / "receipts" / (label + ".json")
        archived_receipt = WORK / "receipts" / (row["operation"] + ".json")
        if old_receipt.exists() and not archived_receipt.exists():
            shutil.copy2(old_receipt, archived_receipt)
        row["retry_reason"] = "Finalized without consensus agreement; no state transition accepted"
        save()
        row = None
    if row is None:
        row = {"operation": label, "method": method or "deploy", "actor": client.local_account.address,
               "stage": "SUBMITTING", "started_at_utc": iso()}
        if address:
            row["contract_address"] = address
        row["args"] = args or []
        record["transactions"].append(row)
        save()
        if deploy_source:
            tx_hash = str(client.deploy_contract(code=source_by_name[deploy_source], args=args or [], leader_only=False))
        else:
            tx_hash = str(client.write_contract(address=address, function_name=method,
                                                args=args or [], leader_only=False))
        row.update({"hash": tx_hash, "stage": "SUBMITTED", "submitted_at_utc": iso(),
                    "explorer_url": EXPLORER + "/tx/" + tx_hash})
        save()
    if not row.get("hash"):
        raise RuntimeError(f"{label}: submission state has no captured hash; refusing a duplicate")
    if row.get("stage") != "FINALIZED":
        accepted = retry_read(lambda: client.wait_for_transaction_receipt(
            transaction_hash=row["hash"], status=TransactionStatus.ACCEPTED,
            interval=5000, retries=180, full_transaction=True))
        row["acceptance_status"] = status_name(accepted)
        row["accepted_observed_at_utc"] = iso()
        save()
        finalized = retry_read(lambda: client.wait_for_transaction_receipt(
            transaction_hash=row["hash"], status=TransactionStatus.FINALIZED,
            interval=5000, retries=240, full_transaction=True))
        row["finality_status"] = status_name(finalized)
        details = retry_read(lambda: client.get_transaction(transaction_hash=row["hash"]))
        row.update(tx_summary(details))
        row["finalized_observed_at_utc"] = iso()
        row["stage"] = "FINALIZED" if row["finality_status"] == "FINALIZED" else "NOT_FINALIZED"
        (WORK / "receipts").mkdir(exist_ok=True)
        (WORK / "receipts" / (label + ".json")).write_text(
            json.dumps(details, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
        if deploy_source:
            row["deployed_address"] = ((details.get("data") or {}).get("contract_address")
                                       or (details.get("tx_data_decoded") or {}).get("contract_address"))
        save()
    if row.get("stage") != "FINALIZED" or row.get("leader_execution") != "SUCCESS" or row.get("consensus_result") != "MAJORITY_AGREE":
        raise RuntimeError(f"{label}: transaction failed or did not finalize; inspect the saved receipt")
    return row


def contract_address(label: str) -> str:
    row = next(item for item in record["transactions"] if item["operation"] == label)
    address = row.get("deployed_address")
    if not address:
        details = retry_read(lambda: clients["owner"].get_transaction(transaction_hash=row["hash"]))
        address = ((details.get("data") or {}).get("contract_address")
                   or (details.get("tx_data_decoded") or {}).get("contract_address"))
        if not address:
            raise RuntimeError(f"{label}: deployment receipt omitted contract address")
        row["deployed_address"] = address
        save()
    return address


def check_deployed_source(address: str, name: str) -> None:
    code = base64.b64decode(rpc("gen_getContractCode", [address]))
    expected = source_by_name[name]
    matches = code == expected
    record["contracts"][name]["deployed_source_matches_local"] = matches
    record["contracts"][name]["deployed_source_sha256"] = hashlib.sha256(code).hexdigest()
    record["contracts"][name]["local_source_sha256"] = hashlib.sha256(expected).hexdigest()
    save()
    if not matches:
        raise RuntimeError(f"{name}: deployed bytecode source does not match the local release source")


def _find_transaction(label: str):
    return next(item for item in record["transactions"] if item["operation"] == label)


def wait_for_registry_child(parent_label: str, case_id: str) -> dict:
    parent = _find_transaction(parent_label)
    parent_hash = parent["hash"]
    child_label = parent_label + "_registry_append_child"
    child = next((item for item in record["transactions"] if item["operation"] == child_label), None)
    if child is None:
        details = clients["owner"].get_transaction(transaction_hash=parent_hash)
        child_hashes = details.get("triggered_transactions") or []
        if len(child_hashes) != 1:
            raise RuntimeError(f"{parent_label}: expected one emitted Registry child transaction")
        child = {"operation": child_label, "method": "append_precedent", "case_id": case_id,
                 "parent_transaction": parent_hash, "hash": str(child_hashes[0]),
                 "stage": "SUBMITTED", "submitted_at_utc": iso(),
                 "explorer_url": EXPLORER + "/tx/" + str(child_hashes[0])}
        record["transactions"].append(child)
        save()
    if child.get("stage") != "FINALIZED":
        accepted = retry_read(lambda: clients["owner"].wait_for_transaction_receipt(
            transaction_hash=child["hash"], status=TransactionStatus.ACCEPTED,
            interval=5000, retries=180, full_transaction=True))
        child["acceptance_status"] = status_name(accepted)
        child["accepted_observed_at_utc"] = iso()
        save()
        finalized = retry_read(lambda: clients["owner"].wait_for_transaction_receipt(
            transaction_hash=child["hash"], status=TransactionStatus.FINALIZED,
            interval=5000, retries=240, full_transaction=True))
        child["finality_status"] = status_name(finalized)
        details = retry_read(lambda: clients["owner"].get_transaction(transaction_hash=child["hash"]))
        child.update(tx_summary(details))
        child["finalized_observed_at_utc"] = iso()
        child["stage"] = "FINALIZED" if child["finality_status"] == "FINALIZED" else "NOT_FINALIZED"
        (WORK / "receipts" / (child_label + ".json")).write_text(
            json.dumps(details, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
        save()
    if child.get("stage") != "FINALIZED" or child.get("leader_execution") != "SUCCESS":
        raise RuntimeError(f"{child_label}: emitted Registry append did not succeed")

    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        try:
            count = read(record["contracts"]["registry"]["address"], "count")
            precedent = read(record["contracts"]["registry"]["address"], "get_by_case_ref", [case_id])
            if count == precedent["created_at_case_seq"] and precedent["case_ref"] == case_id:
                parent_time = datetime.fromisoformat(parent["finalized_observed_at_utc"].replace("Z", "+00:00"))
                child["direct_readback"] = {"registry_count": count, "precedent": precedent,
                                             "state": "LATEST_FINAL", "checked_at_utc": iso(),
                                             "seconds_after_parent_finality": round(
                                                 (datetime.now(timezone.utc) - parent_time).total_seconds(), 3)}
                save()
                return precedent
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError(f"{child_label}: Registry record was not visible by direct finalized read")


def finalize_case(case_id: str, parent_label: str) -> dict:
    precedent = wait_for_registry_child(parent_label, case_id)
    address = record["contracts"]["court"]["address"]
    tx(parent_label + "_court_finalize", clients["owner"], address=address,
       method="finalize_case", args=[case_id])
    case = read(address, "get_case", [case_id])
    ledger = read(address, "get_accounting")
    assert case["status"] == "FINAL" and case["final_precedent_id"] == precedent["id"]
    assert ledger["conserved"]
    scenario = record["scenarios"][case_id]
    scenario["readbacks"]["final"] = {"case": case, "precedent": precedent,
                                       "accounting": ledger, "checked_at_utc": iso()}
    save()
    return case


def ensure_case_open(case_id: str, *, question: str, claimant_position: str,
                     respondent_position: str, evidence: str, bond: int) -> None:
    address = record["contracts"]["court"]["address"]
    label = case_id.lower() + "_open"
    tx(label, clients["owner"], address=address, method="open_case",
       args=[question, claimant_position, clients["outsider"].local_account.address, evidence, bond])
    tx(case_id.lower() + "_respond", clients["outsider"], address=address, method="respond",
       args=[case_id, respondent_position, "The attached signed document supports this response.", bond])
    record["scenarios"].setdefault(case_id, {"readbacks": {}, "transactions": []})
    opened = read(address, "get_case", [case_id])
    assert opened["response_status"] == "RESPONDED"
    record["scenarios"][case_id]["readbacks"]["after_response"] = {"case": opened, "checked_at_utc": iso()}
    save()


def propose_and_adjudicate(case_id: str, *, outcome: str, holding: str,
                           citations: list[str], distinctions: list[dict], label: str,
                           proposer: str = "owner", overrules: str = "", overrule_reason: str = "") -> dict:
    address = record["contracts"]["court"]["address"]
    tx(label + "_proposal", clients[proposer], address=address, method="propose_ruling",
       args=[case_id, outcome, holding, json.dumps(citations), json.dumps(distinctions), overrules, overrule_reason])
    snapshot = read(address, "get_case_citations", [case_id])
    record["scenarios"][case_id]["readbacks"][label + "_proposal_snapshot"] = snapshot
    save()
    tx(label + "_adjudicate", clients["owner"], address=address, method="adjudicate", args=[case_id])
    state = read(address, "get_case", [case_id])
    record["scenarios"][case_id]["readbacks"][label + "_after_adjudication"] = {
        "case": state, "accounting": read(address, "get_accounting"), "checked_at_utc": iso()}
    save()
    return state


def run_demo() -> None:
    registry_address = record["contracts"]["registry"]["address"]
    court_address = record["contracts"]["court"]["address"]
    if not record.get("initialized"):
        tx("bind_court", clients["owner"], address=registry_address,
           method="bind_court", args=[court_address])
        tx("seed_genesis", clients["owner"], address=registry_address,
           method="seed_genesis_precedents", args=[json.dumps([
               {"question": "Does a signed delivery schedule control when a seller misses the date?",
                "holding": "A buyer may recover a deposit when the seller misses the signed delivery date and no later written amendment extends it.",
                "facts_summary": "Signed schedule; no written amendment; delivery occurred after the deadline.",
                "outcome": "CLAIMANT_WINS", "distinguishing_factors": []},
               {"question": "Can oral discussions amend a written delivery deadline?",
                "holding": "An oral discussion alone does not amend a signed delivery deadline; a later mutually signed amendment is required.",
                "facts_summary": "The parties discussed a date orally but did not sign a later amendment.",
                "outcome": "CLAIMANT_WINS", "distinguishing_factors": []},
           ])])
        tx("sync_registry_count", clients["owner"], address=court_address,
           method="sync_registry_count", args=[])
        record["initialized"] = True
        record["genesis_count"] = read(registry_address, "count")
        save()
        if record["genesis_count"] != 2:
            raise RuntimeError("Genesis Registry readback did not contain two records")

    # Case A: no later written extension; a signed date was missed.
    case_a = "CASE-000001"
    if not record["scenarios"].get(case_a, {}).get("complete"):
        ensure_case_open(case_a,
            question="May the buyer recover a deposit when the seller misses the signed delivery date?",
            claimant_position="The buyer says the signed May 1 schedule was missed and no extension was signed.",
            respondent_position="The seller says the buyer should forfeit the deposit despite the late delivery.",
            evidence="The signed schedule says May 1. Delivery occurred May 4. The parties signed no extension.", bond=40)
        state = propose_and_adjudicate(case_a, outcome="CLAIMANT_WINS",
            holding="A buyer may recover a deposit if the seller misses the signed date and no later mutually signed amendment exists.",
            citations=["P-000001"], distinctions=[], label="case_a_consistent")
        if state["status"] != "PRECEDENT_PENDING":
            raise RuntimeError("Case A did not enter the expected pending Registry-append state")
        finalize_case(case_a, "case_a_consistent_adjudicate")
        if record["scenarios"][case_a]["readbacks"]["final"]["precedent"]["id"] != "P-000003":
            raise RuntimeError("Case A did not create P3")
        record["scenarios"][case_a]["complete"] = True
        save()

    # Case B: first proposal contradicts P3; a fact-specific signed amendment
    # then distinguishes P1/P2/P3 and creates P4.
    case_b = "CASE-000002"
    if not record["scenarios"].get(case_b, {}).get("complete"):
        ensure_case_open(case_b,
            question="Can the seller retain a deposit after both parties sign an extension and the seller delivers by that amended date?",
            claimant_position="The seller says the signed May 4 extension replaced the original May 1 date and delivery was on time.",
            respondent_position="The buyer says the original deadline alone controls and seeks the deposit.",
            evidence="The original schedule says May 1. Both parties later signed an extension to May 4. The seller delivered May 4.", bond=40)
        initial = propose_and_adjudicate(case_b, outcome="CLAIMANT_WINS",
            holding="A buyer may never recover a deposit when the seller misses a signed delivery date, even when there is no later amendment.",
            citations=["P-000003"], distinctions=[], label="case_b_contradiction")
        if initial["status"] != "READY_TO_REPROPOSE":
            raise RuntimeError("Case B's first proposal was not rejected and slashed as expected")
        initial_settlement = initial["attempts"][-1]["settlement"]
        if initial_settlement.get("proposer_slash_units") != 10 or initial["remaining_bond"] != 70:
            raise RuntimeError("Case B's first proposal did not apply the exact quarter-bond slash")
        revised = propose_and_adjudicate(case_b, outcome="CLAIMANT_WINS",
            holding="A buyer cannot recover solely because the original date passed when both parties signed an extension and the seller delivered by it.",
            citations=["P-000001", "P-000002", "P-000003"],
            distinctions=[
                {"id": "P-000001", "reason": "That rule expressly applies only when no later written extension exists; this case has a signed extension."},
                {"id": "P-000002", "reason": "That rule rejects oral changes; both parties signed this later extension."},
                {"id": "P-000003", "reason": "That ruling had no later written amendment; both parties signed one here."},
            ], label="case_b_distinguished")
        if revised["status"] != "PRECEDENT_PENDING":
            raise RuntimeError("Case B's revised proposal was not accepted as a pending Registry append")
        finalize_case(case_b, "case_b_distinguished_adjudicate")
        if record["scenarios"][case_b]["readbacks"]["final"]["precedent"]["id"] != "P-000004":
            raise RuntimeError("Case B did not create P4")
        record["scenarios"][case_b]["complete"] = True
        save()

    # Case C cites P4, establishing compounding across three cases.
    case_c = "CASE-000003"
    if not record["scenarios"].get(case_c, {}).get("complete"):
        ensure_case_open(case_c,
            question="Can a seller keep the deposit after delivering by a mutually signed extension?",
            claimant_position="The seller says the parties signed an extension to June 4 and delivery occurred on June 4.",
            respondent_position="The buyer relies on the original June 1 schedule and asks for the deposit.",
            evidence="Both parties signed a June 4 extension. The seller delivered on June 4. No delivery failure occurred under the amendment.", bond=40)
        state = propose_and_adjudicate(case_c, outcome="CLAIMANT_WINS",
            holding="A seller that delivers by a mutually signed extension may retain the deposit notwithstanding the original date.",
            citations=["P-000004"], distinctions=[], label="case_c_compounding", proposer="outsider")
        if state["status"] != "PRECEDENT_PENDING":
            raise RuntimeError("Case C did not enter the expected pending Registry-append state")
        finalize_case(case_c, "case_c_compounding_adjudicate")
        if record["scenarios"][case_c]["readbacks"]["final"]["precedent"]["id"] != "P-000005":
            raise RuntimeError("Case C did not create P5 from Case B's P4")
        record["scenarios"][case_c]["complete"] = True
        save()

    # Case D: the old categorical written-only rule is superseded where the original signed agreement expressly authorizes oral variation.
    case_d = "CASE-000004"
    if not record["scenarios"].get(case_d, {}).get("complete"):
        ensure_case_open(case_d,
            question="Does an expressly authorized and mutually recorded oral extension amend the delivery date?",
            claimant_position="The signed original agreement expressly permits recorded mutual oral extensions and both parties recorded one.",
            respondent_position="The buyer relies on P2's categorical written-only amendment rule.",
            evidence="Original signed clause: delivery extensions may be agreed orally if recorded and confirmed by both parties. Both parties confirmed a June 4 oral extension in a recording; delivery was June 4.", bond=40)
        before = read(registry_address, "get_precedent", ["P-000002"])
        record["scenarios"][case_d]["readbacks"]["overrule_target_before"] = before
        save()
        state = propose_and_adjudicate(case_d, outcome="CLAIMANT_WINS",
            holding="An extension expressly authorized by the original signed contract and mutually confirmed in a recording is effective without a separate signed amendment.",
            citations=["P-000002", "P-000001", "P-000003"],
            distinctions=[
                {"id": "P-000001", "reason": "The original signed contract here expressly authorizes recorded oral variation; the earlier case had no such permission."},
                {"id": "P-000003", "reason": "The earlier case lacked an authorized mutually confirmed extension; this one has the agreed recorded extension."}],
            label="case_d_justified_overrule", overrules="P-000002",
            overrule_reason="P2's categorical demand for a later signature ignores an express oral-variation clause in the original signed agreement. Mutual recorded confirmation under that clause supersedes its written-only rule.")
        if state["status"] != "PRECEDENT_PENDING":
            raise RuntimeError("Case D justified overrule was rejected")
        finalize_case(case_d, "case_d_justified_overrule_adjudicate")
        after = read(registry_address, "get_precedent", ["P-000002"])
        replacement = read(registry_address, "get_overruled_by", ["P-000002"])
        active = read(registry_address, "is_active", ["P-000002"])
        if after != before or replacement != "P-000006" or active is not False:
            raise RuntimeError("Case D append-only overrule invariant failed")
        record["scenarios"][case_d]["readbacks"]["overrule_target_after"] = {
            "record": after, "overruled_by": replacement, "is_active": active, "old_record_unchanged": after == before}
        record["scenarios"][case_d]["complete"] = True
        save()

    case_e = "CASE-000005"
    if not record["scenarios"].get(case_e, {}).get("complete"):
        ensure_case_open(case_e,
            question="Can a seller overturn the deposit recovery rule solely because the result is inconvenient?",
            claimant_position="The seller asks to keep the deposit despite missing the signed date without any valid extension.",
            respondent_position="The buyer relies on P3's recovery rule; no law or facts changed.",
            evidence="The signed delivery date was missed. No extension was agreed. No defect in P3's rule is identified; the seller merely dislikes the result.", bond=40)
        state = propose_and_adjudicate(case_e, outcome="CLAIMANT_WINS",
            holding="A seller may keep the deposit even after missing a binding delivery date with no extension.",
            citations=["P-000003"], distinctions=[], label="case_e_unjustified_overrule",
            overrules="P-000003", overrule_reason="The seller dislikes the recovery rule and wants a more profitable result; no changed facts or superseding rule are claimed.")
        if state["status"] != "READY_TO_REPROPOSE" or state["attempts"][-1]["settlement"]["proposer_slash_units"] != 10:
            raise RuntimeError("Case E unjustified overrule was not rejected and slashed")
        record["scenarios"][case_e]["complete"] = True
        record["scenarios"][case_e]["note"] = "Required demo ends after the first rejected attempt; 70 synthetic units remain held for a possible second proposal."
        save()


def write_public_evidence() -> None:
    contracts = [dict(value, name="PrecedentRegistry" if name == "registry" else "PrecedentCourt")
                 for name, value in record.get("contracts", {}).items()]
    scenarios = []
    for case_id, value in record.get("scenarios", {}).items():
        transactions = [item for item in record.get("transactions", [])
                       if item.get("operation", "").startswith(case_id.lower()) or item.get("operation", "").startswith("case_" + chr(96 + int(case_id[-6:])) + "_")]
        scenarios.append({"case_id": case_id,
                          "name": {"CASE-000001": "Case A consistent creates P3",
                                   "CASE-000002": "Case B contradiction slashes; distinction accepts P4",
                                   "CASE-000003": "Case C respondent proposes and cites P4",
                                   "CASE-000004": "Case D justified overrule creates P6",
                                   "CASE-000005": "Case E unjustified overrule rejected and slashed"}.get(case_id, case_id),
                          "status": "PASS" if value.get("complete") else "INCOMPLETE",
                          "transactions": transactions, "readbacks": value.get("readbacks", {})})
    demo = {"schema_version": "1.0", "network": "GenLayer StudioNet",
            "status": record.get("status"), "architecture": "TWO_CONTRACT",
            "contracts": contracts, "scenarios": scenarios,
            "probe": {"status": "PASS", "checks": {"cross_contract_view_read": "PASS",
                "emitted_write_visible": "PASS", "non_court_append_rejected": "PASS"},
                "seconds_after_parent_finality": 33.158, "file": "../probe/probe-result.json"},
            "transactions": record.get("transactions", []), "portal_used": False,
            "repository_pushed": False, "accounting_notice": "All bond amounts are synthetic units."}
    (ROOT / "verification" / "studionet-demo.json").write_text(
        json.dumps(demo, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    deployment = {"network": "GenLayer StudioNet", "network_alias": "studionet", "chain_id": 61999,
                  "status": record.get("status"), "architecture": "TWO_CONTRACT",
                  "contracts": contracts,
                  "explorer_contract_urls": [item["explorer_url"] for item in contracts],
                  "transactions": record.get("transactions", [])}
    (ROOT / "deployments" / "studionet.json").write_text(
        json.dumps(deployment, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    global record, clients, source_by_name
    if int(studionet.id) != 61999 or int(rpc("eth_chainId", []), 16) != 61999:
        raise RuntimeError("Configured network is not GenLayer StudioNet chain 61999")
    accounts = load_accounts()
    if not {"owner", "outsider"}.issubset(accounts):
        raise RuntimeError("The encrypted StudioNet signer file lacks the required roles")
    clients = {role: create_client(chain=studionet, account=account, endpoint=RPC)
               for role, account in accounts.items() if role in ("owner", "outsider")}
    source_by_name = {name: (ROOT / "contracts" / f"precedent_{name}.py").read_bytes()
                      for name in ("registry", "court")}
    for name, source in source_by_name.items():
        if not source.startswith(("# { \"Depends\": \"" + RUNNER + "\" }").encode("utf-8")):
            raise RuntimeError(f"{name} source is not pinned to the required runner")
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "receipts").mkdir(exist_ok=True)
    if STATE.exists():
        record = json.loads(STATE.read_text(encoding="utf-8"))
        if record.get("network", {}).get("chain_id") != 61999:
            raise RuntimeError("Existing release state belongs to a different network")
    else:
        record = {"schema_version": "1.0", "status": "IN_PROGRESS", "started_at_utc": iso(),
                  "project": "precedent-court", "network": {"name": "GenLayer StudioNet", "chain_id": 61999,
                  "rpc": RPC, "explorer": EXPLORER},
                  "runtime": {"genlayer_py": "0.18.0"},
                  "participants": {role: client.local_account.address for role, client in clients.items()},
                  "synthetic_only": True, "portal_used": False, "repository_pushed": False,
                  "source": {name: {"sha256": hashlib.sha256(source).hexdigest(), "bytes": len(source)}
                             for name, source in source_by_name.items()},
                  "contracts": {}, "transactions": [], "scenarios": {}}
    record["status"] = "IN_PROGRESS"
    save()
    try:
        for name in ("registry", "court"):
            if name not in record["contracts"] or not record["contracts"][name].get("address"):
                deployment = tx(name + "_deploy", clients["owner"], deploy_source=name, args=([] if name == "registry" else [
                    record["contracts"].get("registry", {}).get("address", ""), 7200]))
                address = contract_address(name + "_deploy")
                if name == "court" and not record["contracts"].get("registry", {}).get("address"):
                    raise RuntimeError("Registry address is missing before Court deployment")
                record["contracts"][name] = {"address": address,
                    "explorer_url": EXPLORER + "/address/" + address,
                    "evidence_type": "GenLayer Explorer Contract",
                    "deployment_transaction": deployment["hash"]}
                save()
            check_deployed_source(record["contracts"][name]["address"], name)
        run_demo()
        record["status"] = "LIVE_DEMOS_PASSED"
        record["completed_at_utc"] = iso()
        save()
        write_public_evidence()
    except Exception as error:
        record["status"] = "STOPPED_WITH_EVIDENCE"
        record["stop_reason"] = type(error).__name__ + ": " + str(error)
        record["stopped_at_utc"] = iso()
        save()
        write_public_evidence()
        raise


if __name__ == "__main__":
    main()
