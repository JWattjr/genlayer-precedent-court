"""Direct-mode coverage for the Registry/Court pair and synthetic settlements."""

import json
from datetime import datetime, timedelta

import pytest


START = "2030-01-01T00:00:00Z"
QUESTION = "Does the written delivery date control this dispute?"
CLAIMANT_POSITION = "The signed schedule sets the delivery date."
RESPONDENT_POSITION = "The parties later agreed to a different date."
GENESIS = [{"question": QUESTION,
            "holding": "A signed schedule controls unless later written assent changes it.",
            "facts_summary": "The parties signed an original schedule.",
            "outcome": "CLAIMANT_WINS",
            "distinguishing_factors": []}]


class FakeRegistry:
    """Local cross-contract adapter; direct VM has no separate contract ledger."""

    def __init__(self):
        self.rows = []
        self.by_case_ref = {}
        self.append({"case_ref": "GENESIS-1", "question": QUESTION,
                     "holding": GENESIS[0]["holding"], "facts_summary": GENESIS[0]["facts_summary"],
                     "outcome": "CLAIMANT_WINS", "distinguishing_factors": [], "overrules": None}, True)

    def append(self, record, genesis=False):
        existing = self.by_case_ref.get(record["case_ref"])
        if existing:
            if any(existing[key] != value for key, value in record.items()):
                raise ValueError("case reference already has a different record")
            return existing
        row = dict(record)
        row.update({"id": "P-" + str(len(self.rows) + 1).zfill(6),
                    "created_at_case_seq": len(self.rows) + 1, "genesis": genesis})
        self.rows.append(row)
        self.by_case_ref[record["case_ref"]] = row
        return row

    def view(self):
        return self

    def count(self):
        return len(self.rows)

    def get_precedent(self, precedent_id):
        for row in self.rows:
            if row["id"] == precedent_id:
                return dict(row)
        raise ValueError("cited precedent does not exist")

    def get_by_case_ref(self, case_ref):
        if case_ref not in self.by_case_ref:
            raise ValueError("case reference does not exist")
        return dict(self.by_case_ref[case_ref])

    def emit(self, *, on):
        assert on == "finalized"
        return self

    def append_precedent(self, raw):
        return self.append(json.loads(raw), False)


@pytest.fixture
def court(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    direct_vm.warp(START)
    registry = FakeRegistry()

    # Inject the mock only at the cross-contract boundary; contract methods and storage
    # still execute through genlayer-test's direct GenVM runner.
    import gltest.direct.loader as loader
    original_load = loader._load_module

    def load_module(path):
        module = original_load(path)
        if Path(path).name == "precedent_court.py":
            module.gl.get_contract_at = lambda address: registry
        return module

    from pathlib import Path
    monkeypatch.setattr(loader, "_load_module", load_module)

    direct_vm.sender = direct_alice
    contract = direct_deploy("contracts/precedent_court.py", "0x" + "1" * 40, 60,
                             sdk_version="v0.6.0-rc5")
    contract.sync_registry_count()
    return contract, direct_vm, direct_alice, direct_bob, registry


def llm(value):
    return json.dumps(json.dumps(value))


def judgments(ids, relations=None, distinctions=None):
    relations = relations or ["SUPPORTS"] * len(ids)
    distinctions = distinctions or []
    consistent = not any(relation == "CONTRADICTS" for relation in relations) and all(
        item["status"] == "VALID" for item in distinctions
    )
    return {"per_citation": [{"id": precedent_id, "relation": relation,
                              "reason": "The frozen holding and case facts support this classification."}
                             for precedent_id, relation in zip(ids, relations)],
            "per_distinction": distinctions,
            "consistent": consistent}


def create_case(contract, vm, claimant, respondent, bond=40, respond=True, question=QUESTION):
    vm.sender = claimant
    case_id = contract.open_case(question, CLAIMANT_POSITION, respondent,
                                 "The signed schedule lists delivery on 1 May.", bond)
    if respond:
        vm.sender = respondent
        contract.respond(case_id, RESPONDENT_POSITION, "An unsigned email mentions another date.")
        vm.sender = claimant
    return case_id


def propose(contract, vm, claimant, case_id, outcome="CLAIMANT_WINS", ids=None, distinctions=None, holding=None):
    vm.sender = claimant
    return contract.propose_ruling(case_id, outcome,
                                   holding or "A signed schedule controls absent later written assent.",
                                   json.dumps(ids or ["P-000001"]),
                                   json.dumps(distinctions or []))


def adjudicate(contract, vm, case_id, response):
    vm.clear_mocks()
    vm.mock_llm(r".*PRECEDENT CONSISTENCY REVIEW.*", llm(response))
    result = contract.adjudicate(case_id)
    assert vm.run_validator()
    return result


def finalize_if_pending(contract, vm, case_id, result):
    if result["status"] == "PRECEDENT_PENDING":
        # Verify the bond remains held until the append is independently visible.
        assert accounting(contract)["held_units"] >= contract.get_case(case_id)["remaining_bond"]
        vm.sender = "0x" + "f" * 40
        return contract.finalize_case(case_id)
    return result


def run_judgment(contract, vm, case_id, response):
    result = adjudicate(contract, vm, case_id, response)
    return finalize_if_pending(contract, vm, case_id, result)


def accounting(contract):
    row = contract.get_accounting()
    assert row["conserved"]
    assert row["bonds_in"] == (row["paid_claimant_units"] + row["paid_respondent_units"]
                                + row["fee_units"] + row["held_units"])
    return row


def test_registry_rejects_append_from_non_court_address(direct_vm, direct_deploy,
                                                         direct_alice, direct_bob, direct_charlie):
    direct_vm.sender = direct_alice
    registry = direct_deploy("contracts/precedent_registry.py", sdk_version="v0.6.0-rc5")
    court_address = "0x" + direct_charlie.hex() if isinstance(direct_charlie, bytes) else str(direct_charlie)
    registry.bind_court(court_address)
    registry.seed_genesis_precedents(json.dumps(GENESIS))
    direct_vm.sender = direct_bob
    record = {"case_ref": "CASE-000001", "question": QUESTION, "holding": "A bounded rule.",
              "facts_summary": "A case fact summary.", "outcome": "CLAIMANT_WINS",
              "distinguishing_factors": [], "overrules": None}
    with direct_vm.expect_revert("only bound court may append"):
        registry.append_precedent(json.dumps(record))
    assert registry.count() == 1
    assert registry.get_precedent("P-000001")["genesis"] is True


def test_registry_append_is_idempotent_for_the_same_case_record(direct_vm, direct_deploy,
                                                                 direct_alice, direct_charlie):
    direct_vm.sender = direct_alice
    registry = direct_deploy("contracts/precedent_registry.py", sdk_version="v0.6.0-rc5")
    court_address = "0x" + direct_charlie.hex() if isinstance(direct_charlie, bytes) else str(direct_charlie)
    registry.bind_court(court_address)
    record = {"case_ref": "CASE-000001", "question": QUESTION, "holding": "A bounded rule.",
              "facts_summary": "A case fact summary.", "outcome": "CLAIMANT_WINS",
              "distinguishing_factors": [], "overrules": None}
    direct_vm.sender = direct_charlie
    first = registry.append_precedent(json.dumps(record))
    retry = registry.append_precedent(json.dumps(record))
    assert first["id"] == retry["id"] == "P-000001"
    assert registry.count() == 1
    changed = dict(record, holding="A conflicting retry.")
    with direct_vm.expect_revert("case reference already has a different record"):
        registry.append_precedent(json.dumps(changed))
    assert registry.count() == 1


def test_citing_nonexistent_precedent_is_rejected(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    vm.sender = claimant
    with vm.expect_revert("cited precedent does not exist"):
        contract.propose_ruling(case_id, "CLAIMANT_WINS", "A bounded holding.",
                                '["P-999999"]', "[]")
    assert contract.get_case(case_id)["status"] == "READY_TO_PROPOSE"
    assert accounting(contract)["held_units"] == 40


def test_citation_snapshot_is_frozen_when_a_later_precedent_is_appended(court):
    contract, vm, claimant, respondent, registry = court
    first = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, first)
    frozen_holding = contract.get_case_citations(first)["attempts"][0]["attempt"]["cited_precedents"][0]["holding"]

    second = create_case(contract, vm, claimant, respondent, question="Does the written delivery date bind the parties?")
    propose(contract, vm, claimant, second, holding="A written delivery date binds absent later written assent.")
    run_judgment(contract, vm, second, judgments(["P-000001"]))
    assert registry.count() == 2

    result = run_judgment(contract, vm, first, judgments(["P-000001", "P-000002"]))
    assert result["status"] == "FINAL"
    citations = contract.get_case_citations(first)["attempts"][0]
    assert citations["attempt"]["cited_precedents"][0]["holding"] == frozen_holding
    assert citations["attempt"]["cited_precedents"][0]["holding"] != registry.get_precedent("P-000002")["holding"]
    assert citations["surfaced_precedents"][0]["id"] == "P-000002"


def test_consistent_ruling_waits_for_append_then_finalizes_and_settles(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id)
    before = accounting(contract)
    pending = adjudicate(contract, vm, case_id, judgments(["P-000001"]))
    assert pending["status"] == "PRECEDENT_PENDING"
    assert contract.get_case(case_id)["status"] == "PRECEDENT_PENDING"
    assert accounting(contract)["held_units"] == 40
    assert registry.count() == 2

    vm.sender = "0x" + "f" * 40
    result = contract.finalize_case(case_id)
    row = contract.get_case(case_id)
    precedent = registry.get_precedent(row["final_precedent_id"])
    after = accounting(contract)
    assert result["status"] == row["status"] == "FINAL"
    assert precedent["holding"] == "A signed schedule controls absent later written assent."
    assert registry.count() == 2
    assert before["held_units"] == 40 and after["held_units"] == 0
    assert after["paid_claimant_units"] == 40 and after["conserved"]


@pytest.mark.parametrize(("outcome", "claimant_paid", "respondent_paid"), [
    ("CLAIMANT_WINS", 40, 0),
    ("RESPONDENT_WINS", 0, 40),
    ("SPLIT", 20, 20),
])
def test_every_consistent_outcome_has_exact_conserved_settlement(court, outcome, claimant_paid, respondent_paid):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id, outcome=outcome)
    result = run_judgment(contract, vm, case_id, judgments(["P-000001"]))
    ledger = accounting(contract)
    assert result["status"] == "FINAL"
    assert result["settlement"] == {"claimant_paid_units": claimant_paid,
                                    "respondent_paid_units": respondent_paid,
                                    "fee_units": 0, "held_units": 0}
    assert ledger["bonds_in"] == claimant_paid + respondent_paid == 40
    assert ledger["held_units"] == 0


def test_contradiction_slashes_and_allows_a_second_distinguishing_proposal(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id)
    failed = run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    row = contract.get_case(case_id)
    assert failed["status"] == "READY_TO_REPROPOSE"
    assert row["attempts"][0]["settlement"]["respondent_slash_units"] == 10
    assert row["remaining_bond"] == 30
    assert accounting(contract)["held_units"] == 30

    distinction = [{"id": "P-000001", "reason": "This case has a later signed amendment, unlike the cited facts."}]
    propose(contract, vm, claimant, case_id, distinctions=distinction,
            holding="A later signed amendment controls the delivery date.")
    accepted = run_judgment(contract, vm, case_id,
                            judgments(["P-000001"], ["DISTINGUISHABLE"],
                                      [{"id": "P-000001", "status": "VALID"}]))
    assert accepted["status"] == "FINAL"
    row = contract.get_case(case_id)
    assert row["attempts"][0]["judgment"]["consistent"] is False
    assert row["attempts"][1]["judgment"]["consistent"] is True
    assert accounting(contract)["bonds_in"] == 40


def test_two_failed_attempts_close_unresolved_with_exact_refund_arithmetic(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    for _ in range(2):
        propose(contract, vm, claimant, case_id)
        run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    row = contract.get_case(case_id)
    ledger = accounting(contract)
    assert row["status"] == "UNRESOLVED"
    assert row["terminal_result"]["settlement"] == {
        "claimant_refund_units": 18, "respondent_slash_units": 10,
        "fee_units": 2, "held_units": 0,
    }
    assert ledger == {"bonds_in": 40, "paid_claimant_units": 18,
                      "paid_respondent_units": 20, "fee_units": 2,
                      "held_units": 0, "conserved": True}


def test_case_two_cites_case_ones_new_precedent(court):
    contract, vm, claimant, respondent, registry = court
    first = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, first)
    run_judgment(contract, vm, first, judgments(["P-000001"]))
    assert contract.get_case(first)["final_precedent_id"] == "P-000002"

    second = create_case(contract, vm, claimant, respondent, question="Does the signed schedule set the written delivery date?")
    propose(contract, vm, claimant, second, ids=["P-000002"],
            holding="A signed schedule sets the written delivery date absent amendment.")
    result = run_judgment(contract, vm, second, judgments(["P-000002", "P-000001"]))
    assert result["status"] == "FINAL"
    assert contract.get_case_citations(second)["attempts"][0]["attempt"]["cited_precedents"][0]["id"] == "P-000002"
    assert registry.get_precedent("P-000003")["created_at_case_seq"] == 3
    assert accounting(contract)["conserved"]


def test_default_proceeds_after_response_window(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent, respond=False)
    vm.warp((datetime.fromisoformat(START.replace("Z", "+00:00")) + timedelta(seconds=60)).isoformat())
    propose(contract, vm, claimant, case_id)
    assert contract.get_case(case_id)["response_status"] == "DEFAULT"
    assert contract.get_case(case_id)["respondent_position"] == "No response before the frozen deadline."


def test_oversized_inputs_and_malformed_model_json_are_rejected_without_state_change(court):
    contract, vm, claimant, respondent, registry = court
    vm.sender = claimant
    with vm.expect_revert("question length is invalid"):
        contract.open_case("q" * 1900, CLAIMANT_POSITION, respondent, "Evidence", 40)
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id)
    before = (contract.get_case(case_id), accounting(contract))
    vm.clear_mocks()
    vm.mock_llm(r".*PRECEDENT CONSISTENCY REVIEW.*", llm({"unexpected": True}))
    with vm.expect_revert("judgment schema"):
        contract.adjudicate(case_id)
    assert (contract.get_case(case_id), accounting(contract)) == before
