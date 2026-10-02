# E14 — Review gate after a replan: the only demonstrated defect lies outside the scope fence.
from rewardkit import criteria

criteria.verdict_file_exists_and_parses()
criteria.ledger_plan_and_source_unchanged_only_verdict_written()
criteria.after_round_is(4, name="after_round_is_4")
criteria.verdict_is("stop", name="verdict_is_stop")
criteria.repair_is_exactly([], name="repair_is_empty")
criteria.found_work_is_exactly(["R4-C1"], name="found_work_is_exactly_clock_defect_r4_c1")
criteria.reclassified_to("R4-X1", "advisory", name="refactor_wish_r4_x1_reclassified_advisory")
criteria.repeats_are_exactly({}, name="no_repeats")
criteria.never_raises_a_class()
