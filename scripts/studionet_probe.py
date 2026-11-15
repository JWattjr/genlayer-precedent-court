"""Run the throwaway cross-contract probe; signer data stays DPAPI-encrypted outside this project."""

from __future__ import annotations

import ctypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from eth_account import Account
from genlayer_py import create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus
import requests


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "precedent-court-live-run"
SECRET_FILE = WORK / "signers.dpapi"
RESULT_FILE = ROOT / "probe" / "probe-result.json"
RPC = "https://studio.genlayer.com/api"
EXPLORER = "https://explorer-studio.genlayer.com"
RUNNER = "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6"
SESSION = requests.Session()
SESSION.trust_env = False


def iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(record: dict) -> None:
    RESULT_FILE.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")


class DataBlob(ctypes.Structure):
    _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def dpapi(payload: bytes, decrypt: bool = False) -> bytes:
    if not hasattr(ctypes, "windll"):
        raise RuntimeError("Windows DPAPI is required for signer storage")
    source_buffer = ctypes.create_string_buffer(payload)
    source = DataBlob(len(payload), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = DataBlob()
    if decrypt:
        ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0,
                                                     ctypes.byref(output))
    else:
        ok = ctypes.windll.crypt32.CryptProtectData(ctypes.byref(source), "precedent-court-live", None,
                                                    None, None, 0, ctypes.byref(output))
    if not ok:
        raise RuntimeError("Windows DPAPI signer storage failed")
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        ctypes.windll.kernel32.LocalFree(output.data)


def load_accounts() -> dict:
    WORK.mkdir(parents=True, exist_ok=True)
    if SECRET_FILE.exists():
        secret = json.loads(dpapi(SECRET_FILE.read_bytes(), decrypt=True))
    else:
        secret = {"keys": {role: Account.create().key.hex()
                           for role in ("owner", "outsider")}}
        SECRET_FILE.write_bytes(dpapi(json.dumps(secret).encode("utf-8")))
    return {role: Account.from_key(key) for role, key in secret["keys"].items()}


def chain_id() -> int:
    response = SESSION.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
                            timeout=(10, 30))
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError("StudioNet returned an RPC error")
    return int(body["result"], 16)


def status_name(value) -> str:
    raw = value.get("status_name") or value.get("status") if isinstance(value, dict) else value
    raw = getattr(raw, "value", raw)
    return str(raw).split(".")[-1].upper()


def tx_summary(details: dict) -> dict:
    leaders = (details.get("consensus_data") or {}).get("leader_receipt") or []
    leader = leaders[0] if leaders else {}
    return {"leader_execution": leader.get("execution_result"),
            "consensus_result": details.get("result_name"),
            "rounds": details.get("num_of_rounds")}


def submit(client, record: dict, label: str, operation, expected_error: str = "") -> dict:
    row = {"operation": label, "stage": "SUBMITTING", "started_at_utc": iso()}
    record["transactions"].append(row)
    save(record)
    try:
        tx_hash = str(operation())
        row.update({"hash": tx_hash, "stage": "SUBMITTED",
                    "explorer_url": EXPLORER + "/tx/" + tx_hash,
                    "submitted_at_utc": iso()})
        save(record)
        accepted = client.wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.ACCEPTED,
            interval=5000, retries=180, full_transaction=True)
        row["acceptance_status"] = status_name(accepted)
        row["accepted_observed_at_utc"] = iso()
        save(record)
        finalized = client.wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.FINALIZED,
            interval=5000, retries=240, full_transaction=True)
        row["finality_status"] = status_name(finalized)
        row["finalized_observed_at_utc"] = iso()
        details = client.get_transaction(transaction_hash=tx_hash)
        row.update(tx_summary(details))
        (WORK / "receipts").mkdir(exist_ok=True)
        (WORK / "receipts" / (label + ".json")).write_text(
            json.dumps(details, indent=2, default=str) + "\n", encoding="utf-8")
        if expected_error:
            row["expected_error"] = expected_error
            row["expected_error_found"] = expected_error.lower() in json.dumps(details, default=str).lower()
        row["stage"] = "FINALIZED"
        save(record)
        return row
    except Exception as error:
        row.update({"stage": "ERROR", "error_type": type(error).__name__, "observed_at_utc": iso()})
        save(record)
        raise


def extract_contract_address(details: dict) -> str:
    return ((details.get("data") or {}).get("contract_address")
            or (details.get("tx_data_decoded") or {}).get("contract_address") or "")


def contains_readback(value, expected: str) -> bool:
    if isinstance(value, dict):
        if value.get("read_value") == expected:
            return True
        return any(contains_readback(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(contains_readback(item, expected) for item in value)
    if isinstance(value, str):
        if expected in value and "read_value" in value:
            return True
        if value.startswith(("{", "[")):
            try:
                return contains_readback(json.loads(value), expected)
            except Exception:
                return False
    return False


def main() -> None:
    prior_attempts = []
    if RESULT_FILE.exists():
        previous = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
        if previous.get("status") == "PASS":
            raise RuntimeError("Probe already passed; refusing a duplicate deployment")
        prior_attempts = previous.get("prior_attempts", [])
        if previous.get("transactions"):
            prior_attempts.append({"attempt": previous.get("attempt", 1),
                                   "status": previous.get("status", "INCOMPLETE"),
                                   "source_sha256": previous.get("source_sha256", {}),
                                   "contracts": previous.get("contracts", {}),
                                   "transactions": previous.get("transactions", []),
                                   "checks": previous.get("checks", {}),
                                   "note": "Earlier probe attempt did not establish all three checks; retained for audit."})
    detected_chain_id = chain_id()
    if detected_chain_id != 61999 or int(studionet.id) != 61999:
        raise RuntimeError("Configured network is not StudioNet chain 61999")

    accounts = load_accounts()
    clients = {role: create_client(chain=studionet, account=account, endpoint=RPC)
               for role, account in accounts.items()}
    owner, outsider = clients["owner"], clients["outsider"]
    registry_source = (ROOT / "probe" / "probe_registry.py").read_bytes()
    caller_source = (ROOT / "probe" / "probe_caller.py").read_bytes()
    for source in (registry_source, caller_source):
        if not source.startswith(("# { \"Depends\": \"" + RUNNER + "\" }").encode("utf-8")):
            raise RuntimeError("Probe source does not use the pinned runner")

    record = {"status": "IN_PROGRESS", "attempt": len(prior_attempts) + 1,
              "prior_attempts": prior_attempts,
              "network_alias": "studionet", "chain_id": detected_chain_id,
              "started_at_utc": iso(), "source_sha256": {
                  "registry": hashlib.sha256(registry_source).hexdigest(),
                  "caller": hashlib.sha256(caller_source).hexdigest()},
              "transactions": [], "contracts": {}, "checks": {}, "readbacks": []}
    save(record)

    registry_deploy = submit(owner, record, "registry_deploy",
                             lambda: owner.deploy_contract(code=registry_source,
                                                          args=["seed", "studio-probe-value"],
                                                          leader_only=False))
    registry_details = owner.get_transaction(transaction_hash=registry_deploy["hash"])
    if registry_deploy.get("leader_execution") != "SUCCESS":
        raise RuntimeError("Registry deployment finalized with an execution error")
    registry_address = extract_contract_address(registry_details)
    if not registry_address:
        raise RuntimeError("Registry deployment receipt omitted its contract address")
    record["contracts"]["registry"] = {"address": registry_address,
                                         "explorer_url": EXPLORER + "/address/" + registry_address}
    save(record)

    caller_deploy = submit(owner, record, "caller_deploy",
                           lambda: owner.deploy_contract(code=caller_source,
                                                        args=[registry_address], leader_only=False))
    caller_details = owner.get_transaction(transaction_hash=caller_deploy["hash"])
    if caller_deploy.get("leader_execution") != "SUCCESS":
        raise RuntimeError("Caller deployment finalized with an execution error")
    caller_address = extract_contract_address(caller_details)
    if not caller_address:
        raise RuntimeError("Caller deployment receipt omitted its contract address")
    record["contracts"]["caller"] = {"address": caller_address,
                                       "explorer_url": EXPLORER + "/address/" + caller_address}
    save(record)

    bind = submit(owner, record, "bind_probe_caller",
                  lambda: owner.write_contract(address=registry_address, function_name="bind_court",
                                               args=[caller_address], leader_only=False))
    if bind.get("leader_execution") != "SUCCESS":
        raise RuntimeError("Registry court binding did not execute successfully")

    parent_finalized_start = time.monotonic()
    write = submit(owner, record, "cross_read_then_emit",
                   lambda: owner.write_contract(address=caller_address, function_name="read_then_emit",
                                                args=["seed", "cross-write", "landed-value"],
                                                leader_only=False))
    parent_finalized_at = time.monotonic()
    read_value = owner.read_contract(address=caller_address, function_name="get_last_read", args=[],
                                     transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    read_matches = read_value == "studio-probe-value"
    record["readbacks"].append({"method": "caller.get_last_read()", "value": read_value,
                                "transaction_hash": write["hash"], "state": "LATEST_FINAL",
                                "checked_at_utc": iso()})
    record["checks"]["a_cross_contract_view_read"] = "PASS" if read_matches else "NOT_CONFIRMED_IN_RECEIPT"
    record["checks"]["parent_finality_seconds"] = round(parent_finalized_at - parent_finalized_start, 3)
    save(record)

    visible = None
    readback_seconds = None
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        try:
            value = owner.read_contract(address=registry_address, function_name="get", args=["cross-write"],
                                        transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
            if isinstance(value, str) and value.startswith("\""):
                value = json.loads(value)
            if value == "landed-value":
                visible = value
                readback_seconds = round(time.monotonic() - parent_finalized_at, 3)
                break
        except Exception:
            pass
        time.sleep(5)
    record["readbacks"].append({"method": "registry.get(cross-write)", "value": visible,
                                "transaction_hash": write["hash"],
                                "state": "LATEST_FINAL",
                                "seconds_after_parent_finality": readback_seconds,
                                "checked_at_utc": iso()})
    record["checks"]["b_emitted_write_visible"] = "PASS" if visible == "landed-value" else "FAIL_TIMEOUT"
    record["checks"]["write_finality_seconds"] = readback_seconds
    save(record)

    before_count = owner.read_contract(address=registry_address, function_name="count", args=[],
                                       transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    rejection = submit(outsider, record, "outsider_append_rejected",
                       lambda: outsider.write_contract(address=registry_address, function_name="append",
                                                       args=["unauthorized", "must-not-land"],
                                                       leader_only=False),
                       expected_error="only bound court may append")
    after_count = owner.read_contract(address=registry_address, function_name="count", args=[],
                                      transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    direct_reject = rejection.get("leader_execution") == "ERROR" and before_count == after_count
    record["checks"]["c_non_court_append_rejected"] = "PASS" if direct_reject else "FAIL"
    record["readbacks"].append({"method": "registry.count()", "before": before_count,
                                "after": after_count, "state": "LATEST_FINAL", "checked_at_utc": iso()})
    all_pass = all(record["checks"].get(key) == "PASS" for key in (
        "a_cross_contract_view_read", "b_emitted_write_visible", "c_non_court_append_rejected"))
    record["status"] = "PASS" if all_pass else "FAIL"
    record["architecture_decision"] = "TWO_CONTRACT" if all_pass else "SINGLE_CONTRACT_FALLBACK"
    record["note"] = "Probe contracts are throwaway and are not submission evidence."
    save(record)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if RESULT_FILE.exists():
            try:
                record = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
                record["status"] = "FAILED"
                record["failure_type"] = type(error).__name__
                record["failed_at_utc"] = iso()
                save(record)
            except Exception:
                pass
        raise
