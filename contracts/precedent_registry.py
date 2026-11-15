# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""Court-bound append-only store for precedent records."""

import json

from genlayer import *


OUTCOMES = ("CLAIMANT_WINS", "RESPONDENT_WINS", "SPLIT")
MAX_PRECEDENTS = 128
MAX_JSON = 6000
MAX_REASON = 240


def _address_text(value) -> str:
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    if hasattr(value, "as_bytes"):
        raw = value.as_bytes
        if isinstance(raw, (bytes, bytearray)):
            return "0x" + bytes(raw).hex()
    return str(value).lower()


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _text(value: str, label: str, maximum: int, minimum: int = 1) -> str:
    if not isinstance(value, str):
        raise gl.vm.UserError(f"[EXPECTED] {label} must be text")
    try:
        if len(value.encode("utf-8", errors="strict")) > maximum * 4:
            raise gl.vm.UserError(f"[EXPECTED] {label} is too large")
    except UnicodeError:
        raise gl.vm.UserError(f"[EXPECTED] {label} must be valid UTF-8")
    normalized = " ".join(value.split())
    if not minimum <= len(normalized) <= maximum:
        raise gl.vm.UserError(f"[EXPECTED] {label} length is invalid")
    return normalized


def _enum(value, options, label):
    if not isinstance(value, str) or len(value) > 40:
        raise gl.vm.UserError(f"[EXPECTED] {label} must be a bounded enum")
    normalized = value.strip().upper()
    if normalized not in options:
        raise gl.vm.UserError(f"[EXPECTED] invalid {label}")
    return normalized


def _record_input(value: str, *, genesis: bool) -> dict:
    if not isinstance(value, str) or len(value) > MAX_JSON:
        raise gl.vm.UserError("[EXPECTED] precedent must be bounded JSON text")
    try:
        raw = json.loads(value)
    except Exception:
        raise gl.vm.UserError("[EXPECTED] invalid precedent JSON")
    required = {"case_ref", "question", "holding", "facts_summary", "outcome",
                "distinguishing_factors", "overrules"}
    if not isinstance(raw, dict) or set(raw) != required:
        raise gl.vm.UserError("[EXPECTED] precedent schema is invalid")
    case_ref = _text(raw["case_ref"], "case reference", 80)
    question = _text(raw["question"], "question", 400)
    holding = _text(raw["holding"], "holding", 400)
    facts = _text(raw["facts_summary"], "facts summary", 500)
    outcome = _enum(raw["outcome"], OUTCOMES, "outcome")
    factors = raw["distinguishing_factors"]
    if not isinstance(factors, list) or len(factors) > 5:
        raise gl.vm.UserError("[EXPECTED] factors must be a list of at most five")
    factors = [_text(item, "distinguishing factor", MAX_REASON) for item in factors]
    overrules = raw["overrules"]
    if overrules is not None:
        overrules = _text(overrules, "overruled precedent ID", 16)
        if not overrules.startswith("P-"):
            raise gl.vm.UserError("[EXPECTED] overruled precedent ID is invalid")
    if genesis and not case_ref.startswith("GENESIS-"):
        raise gl.vm.UserError("[EXPECTED] genesis case reference is invalid")
    if not genesis and case_ref.startswith("GENESIS-"):
        raise gl.vm.UserError("[EXPECTED] court cannot append genesis records")
    return {"case_ref": case_ref, "question": question, "holding": holding,
            "facts_summary": facts, "outcome": outcome,
            "distinguishing_factors": factors, "overrules": overrules}


class PrecedentRegistry(gl.Contract):
    owner: Address
    bound_court: str
    court_bound: bool
    genesis_seeded: bool
    precedents: TreeMap[str, str]
    precedent_order: DynArray[str]
    case_ref_to_id: TreeMap[str, str]

    def __init__(self):
        self.owner = gl.message.sender_address
        self.bound_court = ""
        self.court_bound = False
        self.genesis_seeded = False

    def _append_normalized(self, record: dict, genesis: bool) -> dict:
        case_ref = record["case_ref"]
        if case_ref in self.case_ref_to_id:
            existing = self._load_precedent(self.case_ref_to_id[case_ref])
            expected = {key: existing[key] for key in record}
            if expected != record or existing["genesis"] is not genesis:
                raise gl.vm.UserError("[EXPECTED] case reference already has a different record")
            return existing
        if len(self.precedent_order) >= MAX_PRECEDENTS:
            raise gl.vm.UserError("[EXPECTED] precedent registry is full")
        sequence = len(self.precedent_order) + 1
        precedent_id = "P-" + str(sequence).zfill(6)
        precedent = dict(record)
        precedent.update({"id": precedent_id, "created_at_case_seq": sequence, "genesis": genesis})
        self.precedents[precedent_id] = _canonical(precedent)
        self.precedent_order.append(precedent_id)
        self.case_ref_to_id[case_ref] = precedent_id
        return precedent

    def _load_precedent(self, precedent_id: str) -> dict:
        if not isinstance(precedent_id, str) or precedent_id not in self.precedents:
            raise gl.vm.UserError("[EXPECTED] cited precedent does not exist")
        return json.loads(self.precedents[precedent_id])

    @gl.public.write
    def bind_court(self, court_address: str) -> str:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("[EXPECTED] only deployer may bind court")
        if self.court_bound:
            raise gl.vm.UserError("[EXPECTED] court is already bound")
        if not isinstance(court_address, str) or not 1 <= len(court_address) <= 80:
            raise gl.vm.UserError("[EXPECTED] court address is invalid")
        normalized = _address_text(Address(court_address))
        if normalized == "0x" + "0" * 40:
            raise gl.vm.UserError("[EXPECTED] court address cannot be zero")
        self.bound_court = normalized
        self.court_bound = True
        return normalized

    @gl.public.write
    def seed_genesis_precedents(self, genesis_json: str) -> list:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("[EXPECTED] only deployer may seed genesis precedents")
        if self.genesis_seeded:
            raise gl.vm.UserError("[EXPECTED] genesis precedents may be seeded once")
        if not self.court_bound:
            raise gl.vm.UserError("[EXPECTED] bind court before genesis seeding")
        if not isinstance(genesis_json, str) or len(genesis_json) > 5000:
            raise gl.vm.UserError("[EXPECTED] genesis precedents must be bounded JSON")
        try:
            values = json.loads(genesis_json)
        except Exception:
            raise gl.vm.UserError("[EXPECTED] invalid genesis JSON")
        if not isinstance(values, list) or len(values) > 3:
            raise gl.vm.UserError("[EXPECTED] at most three genesis precedents are allowed")
        created = []
        for index, value in enumerate(values, 1):
            if not isinstance(value, dict) or set(value) != {
                    "question", "holding", "facts_summary", "outcome", "distinguishing_factors"}:
                raise gl.vm.UserError("[EXPECTED] genesis precedent schema is invalid")
            record = {"case_ref": "GENESIS-" + str(index),
                      "question": value["question"], "holding": value["holding"],
                      "facts_summary": value["facts_summary"], "outcome": value["outcome"],
                      "distinguishing_factors": value["distinguishing_factors"], "overrules": None}
            created.append(self._append_normalized(_record_input(_canonical(record), genesis=True), True))
        self.genesis_seeded = True
        return created

    @gl.public.write
    def append_precedent(self, precedent_json: str) -> dict:
        if not self.court_bound or _address_text(gl.message.sender_address) != self.bound_court:
            raise gl.vm.UserError("[EXPECTED] only bound court may append")
        record = _record_input(precedent_json, genesis=False)
        if record["overrules"] is not None and record["overrules"] not in self.precedents:
            raise gl.vm.UserError("[EXPECTED] overruled precedent does not exist")
        return self._append_normalized(record, False)

    @gl.public.view
    def get_precedent(self, precedent_id: str) -> dict:
        return self._load_precedent(precedent_id)

    @gl.public.view
    def get_by_case_ref(self, case_ref: str) -> dict:
        if not isinstance(case_ref, str) or case_ref not in self.case_ref_to_id:
            raise gl.vm.UserError("[EXPECTED] case reference does not exist")
        return self._load_precedent(self.case_ref_to_id[case_ref])

    @gl.public.view
    def list_precedents(self, offset: u256, limit: u256) -> list:
        if type(offset) is bool or type(limit) is bool or not isinstance(offset, int) or not isinstance(limit, int):
            raise gl.vm.UserError("[EXPECTED] pagination must be integer values")
        if int(offset) < 0 or not 1 <= int(limit) <= 50:
            raise gl.vm.UserError("[EXPECTED] pagination is outside its bounds")
        return [self._load_precedent(self.precedent_order[index])
                for index in range(int(offset), min(len(self.precedent_order), int(offset) + int(limit)))]

    @gl.public.view
    def count(self) -> int:
        return len(self.precedent_order)
