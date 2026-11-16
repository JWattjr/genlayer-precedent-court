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
        self.overruled = {}
        self.append({"case_ref": "GENESIS-1", "question": QUESTION,
                     "holding": GENESIS[0]["holding"], "facts_summary": GENESIS[0]["facts_summary"],
                     "outcome": "CLAIMANT_WINS", "distinguishing_factors": [], "overrules": None}, True)

    def append(self, record, genesis=False):
        existing = self.by_case_ref.get(record["case_ref"])
        if existing:
            if any(existing[key] != value for key, value in record.items()):
                raise ValueError("case reference already has a different record")
            return existing
        assert len(record["question"]) <= 400
        if record["overrules"]:
            assert record["overrules"] not in self.overruled
        row = dict(record)
        row.update({"id": "P-" + str(len(self.rows) + 1).zfill(6),
                    "created_at_case_seq": len(self.rows) + 1, "genesis": genesis})
        self.rows.append(row)
        self.by_case_ref[record["case_ref"]] = row
        if record["overrules"]:
            self.overruled[record["overrules"]] = row["id"]
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

    def get_overruled_by(self, precedent_id):
        self.get_precedent(precedent_id)
        return self.overruled.get(precedent_id, "")

    def is_active(self, precedent_id):
        return not self.get_overruled_by(precedent_id)

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


def judgments(ids, relations=None, distinctions=None, overrules=None):
    relations = relations or ["SUPPORTS"] * len(ids)
    distinctions = distinctions or []
    consistent = not any(relation == "CONTRADICTS" for relation in relations) and all(
        item["status"] == "VALID" for item in distinctions
    )
    return {"per_citation": [{"id": precedent_id, "relation": relation,
                              "reason": "The frozen holding and case facts support this classification."}
                             for precedent_id, relation in zip(ids, relations)],
            "per_distinction": distinctions, "per_overrule": overrules or [],
            "consistent": consistent}


def create_case(contract, vm, claimant, respondent, bond=40, respond=True, question=QUESTION):
    vm.sender = claimant
    case_id = contract.open_case(question, CLAIMANT_POSITION, respondent,
                                 "The signed schedule lists delivery on 1 May.", bond)
    if respond:
        vm.sender = respondent
        contract.respond(case_id, RESPONDENT_POSITION, "An unsigned email mentions another date.", bond)
        vm.sender = claimant
    return case_id


def propose(contract, vm, claimant, case_id, outcome="CLAIMANT_WINS", ids=None, distinctions=None, holding=None, overrules="", overrule_reason=""):
    vm.sender = claimant
    return contract.propose_ruling(case_id, outcome,
                                   holding or "A signed schedule controls absent later written assent.",
                                   json.dumps(ids or ["P-000001"]),
                                   json.dumps(distinctions or []), overrules, overrule_reason)


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
    assert accounting(contract)["held_units"] == 80


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
    assert accounting(contract)["held_units"] == 80
    assert registry.count() == 2

    vm.sender = "0x" + "f" * 40
    result = contract.finalize_case(case_id)
    row = contract.get_case(case_id)
    precedent = registry.get_precedent(row["final_precedent_id"])
    after = accounting(contract)
    assert result["status"] == row["status"] == "FINAL"
    assert precedent["holding"] == "A signed schedule controls absent later written assent."
    assert registry.count() == 2
    assert before["held_units"] == 80 and after["held_units"] == 0
    assert after["paid_claimant_units"] == 80 and after["conserved"]


@pytest.mark.parametrize(("outcome", "claimant_paid", "respondent_paid"), [
    ("CLAIMANT_WINS", 80, 0),
    ("RESPONDENT_WINS", 0, 80),
    ("SPLIT", 40, 40),
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
    assert ledger["bonds_in"] == claimant_paid + respondent_paid == 80
    assert ledger["held_units"] == 0


def test_contradiction_slashes_and_allows_a_second_distinguishing_proposal(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id)
    failed = run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    row = contract.get_case(case_id)
    assert failed["status"] == "READY_TO_REPROPOSE"
    assert row["attempts"][0]["settlement"]["proposer_slash_units"] == 10
    assert row["remaining_bond"] == 70
    assert accounting(contract)["held_units"] == 70

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
    assert accounting(contract)["bonds_in"] == 80


def test_two_failed_attempts_close_unresolved_with_exact_refund_arithmetic(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    for _ in range(2):
        propose(contract, vm, claimant, case_id)
        run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    row = contract.get_case(case_id)
    ledger = accounting(contract)
    assert row["status"] == "UNRESOLVED"
    settlement = row["terminal_result"]["settlement"]
    assert settlement["claimant_refund_units"] == 18
    assert settlement["respondent_refund_units"] == 36
    assert settlement["fee_units"] == 6
    assert ledger == {"bonds_in": 80, "paid_claimant_units": 18,
                      "paid_respondent_units": 56, "fee_units": 6,
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
        contract.open_case("q" * 401, CLAIMANT_POSITION, respondent, "Evidence", 40)
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id)
    before = (contract.get_case(case_id), accounting(contract))
    vm.clear_mocks()
    vm.mock_llm(r".*PRECEDENT CONSISTENCY REVIEW.*", llm({"unexpected": True}))
    with vm.expect_revert("judgment schema"):
        contract.adjudicate(case_id)
    assert (contract.get_case(case_id), accounting(contract)) == before


def test_justified_overrule_and_untrusted_boolean(court):
    contract, vm, claimant, respondent, registry = court
    original = registry.get_precedent("P-000001")
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id, overrules="P-000001", overrule_reason="The earlier rule wrongly treated unsigned schedules as binding.")
    verdict = judgments(["P-000001"], ["CONTRADICTS"], overrules=[{"id": "P-000001", "status": "JUSTIFIED"}])
    verdict["consistent"] = False
    result = run_judgment(contract, vm, case_id, verdict)
    assert result["status"] == "FINAL"
    assert registry.get_precedent("P-000002")["overrules"] == "P-000001"
    assert registry.get_overruled_by("P-000001") == "P-000002"
    assert registry.get_precedent("P-000001") == original
    assert not registry.is_active("P-000001")


def test_unjustified_overrule_slashes_even_if_model_says_consistent(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id, overrules="P-000001", overrule_reason="I dislike the result.")
    verdict = judgments(["P-000001"], overrules=[{"id": "P-000001", "status": "UNJUSTIFIED"}])
    verdict["consistent"] = True
    result = run_judgment(contract, vm, case_id, verdict)
    assert result["consistent"] is False
    assert result["settlement"]["proposer_slash_units"] == 10
    assert registry.count() == 1
    assert accounting(contract)["paid_respondent_units"] == 10


@pytest.mark.parametrize("target,citations,error", [("P-000002", ["P-000001"], "must also be cited"),
                                                  ("P-999999", ["P-999999"], "does not exist")])
def test_overrule_target_validation(court, target, citations, error):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    with vm.expect_revert(error):
        propose(contract, vm, claimant, case_id, ids=citations, overrules=target, overrule_reason="Changed circumstances.")
    assert accounting(contract)["held_units"] == 80


def test_other_contradiction_is_not_excused_by_overrule(court):
    contract, vm, claimant, respondent, registry = court
    row = dict(registry.get_precedent("P-000001"))
    row = {k: v for k, v in row.items() if k not in ("id", "genesis", "created_at_case_seq")}
    row["case_ref"] = "EARLIER"
    registry.append(row)
    contract.expected_registry_count = 2
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, case_id, ids=["P-000001", "P-000002"], overrules="P-000001", overrule_reason="A wrong earlier rule.")
    verdict = judgments(["P-000001", "P-000002"], ["CONTRADICTS", "CONTRADICTS"],
                       overrules=[{"id": "P-000001", "status": "JUSTIFIED"}])
    result = run_judgment(contract, vm, case_id, verdict)
    assert not result["consistent"]


def test_historical_citation_label_and_no_duplicate_overrule(court):
    contract, vm, claimant, respondent, registry = court
    first = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, first, overrules="P-000001", overrule_reason="A superseding signed rule controls.")
    run_judgment(contract, vm, first, judgments(["P-000001"], ["CONTRADICTS"], overrules=[{"id": "P-000001", "status": "JUSTIFIED"}]))
    second = create_case(contract, vm, claimant, respondent)
    with vm.expect_revert("already overruled"):
        propose(contract, vm, claimant, second, overrules="P-000001", overrule_reason="Again.")
    propose(contract, vm, claimant, second, ids=["P-000001"])
    cited = contract.get_case_citations(second)["attempts"][0]["attempt"]["cited_precedents"]
    assert cited[0]["overruled_by"] == "P-000002"
    run_judgment(contract, vm, second, judgments(["P-000001", "P-000002"]))
    third = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, claimant, third, ids=["P-000002", "P-000003"])
    run_judgment(contract, vm, third, judgments(["P-000002", "P-000003"]))
    surfaced = contract.get_case_citations(third)["attempts"][0]["surfaced_precedents"]
    assert not surfaced


def test_respondent_proposes_and_mixed_attempts_conserve(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent)
    propose(contract, vm, respondent, case_id)
    rejected = run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    assert rejected["settlement"]["slash_recipient"] == "CLAIMANT"
    assert accounting(contract)["paid_claimant_units"] == 10
    propose(contract, vm, claimant, case_id)
    run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    ledger = accounting(contract)
    assert ledger == {"bonds_in": 80, "paid_claimant_units": 37, "paid_respondent_units": 37,
                      "fee_units": 6, "held_units": 0, "conserved": True}
    with vm.expect_revert("matching bond"):
        propose(contract, vm, respondent, case_id)


def test_odd_split_after_one_slash(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent, bond=5)
    propose(contract, vm, respondent, case_id)
    run_judgment(contract, vm, case_id, judgments(["P-000001"], ["CONTRADICTS"]))
    propose(contract, vm, claimant, case_id, outcome="SPLIT")
    settled = run_judgment(contract, vm, case_id, judgments(["P-000001"]))["settlement"]
    assert settled["claimant_paid_units"] == 4 and settled["respondent_paid_units"] == 5
    assert accounting(contract)["conserved"]


def test_default_single_bond_terminal_path(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent, respond=False)
    vm.warp("2030-01-01T00:01:00Z")
    with vm.expect_revert("matching bond"):
        propose(contract, vm, respondent, case_id)
    propose(contract, vm, claimant, case_id)
    result = run_judgment(contract, vm, case_id, judgments(["P-000001"]))
    assert result["settlement"]["claimant_paid_units"] == 40
    assert accounting(contract)["bonds_in"] == 40


def test_registry_overrule_is_append_only_and_retry_safe(direct_vm, direct_deploy, direct_alice, direct_charlie):
    direct_vm.sender = direct_alice
    registry = direct_deploy("contracts/precedent_registry.py", sdk_version="v0.6.0-rc5")
    address = "0x" + direct_charlie.hex() if isinstance(direct_charlie, bytes) else str(direct_charlie)
    registry.bind_court(address)
    registry.seed_genesis_precedents(json.dumps(GENESIS))
    before = registry.get_precedent("P-000001")
    direct_vm.sender = direct_charlie
    record = {"case_ref": "CASE-overrule", "question": QUESTION, "holding": "The superseding rule applies.",
              "facts_summary": "A changed rule.", "outcome": "CLAIMANT_WINS", "distinguishing_factors": [], "overrules": "P-000001"}
    result = registry.append_precedent(json.dumps(record))
    assert registry.append_precedent(json.dumps(record)) == result
    assert registry.get_precedent("P-000001") == before
    assert registry.get_overruled_by("P-000001") == result["id"]
    assert not registry.is_active("P-000001") and registry.is_active(result["id"])
    with direct_vm.expect_revert("already overruled"):
        registry.append_precedent(json.dumps(dict(record, case_ref="CASE-again")))


def test_ranked_retrieval_finds_older_match_and_excludes_overruled():
    import ast
    import re
    from pathlib import Path
    from types import SimpleNamespace, MethodType
    tree = ast.parse(Path("contracts/precedent_court.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_keywords"]
    nodes += [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_relevant_precedents"]
    namespace = {"re": re, "SAME_OUTCOME_BONUS": 2}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), "<actual-retrieval>", "exec"), namespace)
    rows = {"P-" + str(i).zfill(6): {"id": "P-" + str(i).zfill(6), "question": "delivery schedule signed amendment" if i == 1 else "schedule",
            "holding": "delivery signed amendment" if i == 1 else "schedule", "facts_summary": "schedule",
            "outcome": "CLAIMANT_WINS", "created_at_case_seq": i, "overruled_by": ""} for i in range(1, 10)}
    rows["P-000009"]["overruled_by"] = "P-000008"
    obj = SimpleNamespace(_registry_precedent=lambda key: dict(rows[key]))
    case = {"question": "delivery schedule signed amendment", "claimant_position": "", "respondent_position": ""}
    proposal = {"holding": "delivery signed amendment", "outcome": "CLAIMANT_WINS", "cited_precedents": []}
    result = namespace["_relevant_precedents"](obj, case, proposal, 9)
    assert [r["id"] for r in result] == ["P-000001", "P-000008", "P-000007", "P-000006", "P-000005"]
    assert [r["retrieval_score"] for r in result] == [6, 3, 3, 3, 3]
    assert result == namespace["_relevant_precedents"](obj, case, proposal, 9)


def test_longest_question_is_appendable_and_preserves_both_evidence_summaries(court):
    contract, vm, claimant, respondent, registry = court
    case_id = create_case(contract, vm, claimant, respondent, question="q" * 400)
    propose(contract, vm, claimant, case_id)
    result = run_judgment(contract, vm, case_id, judgments(["P-000001"]))
    precedent = registry.get_precedent(result["precedent_id"])
    assert len(precedent["question"]) == 400
    assert "CE:" in precedent["facts_summary"] and "RE:" in precedent["facts_summary"]
    assert "unsigned email" in precedent["facts_summary"]
