# E14 — Review gate, not converging: the third local round still raises demonstrated defects.
from rewardkit import criteria

criteria.verdict_file_exists_and_parses()
criteria.ledger_plan_and_source_unchanged_only_verdict_written()
criteria.after_round_is(3, name="after_round_is_3")
criteria.verdict_is("replan", name="verdict_is_replan")
criteria.repair_is_exactly(["R3-C1", "R3-X1"], name="repair_is_exactly_r3_c1_r3_x1")
criteria.stay_actionable(["R3-C1", "R3-X1"], name="r3_c1_r3_x1_stay_actionable")
criteria.repeats_are_exactly({}, name="no_repeats")
criteria.found_work_is_exactly([], name="found_work_is_empty")
criteria.never_raises_a_class()
