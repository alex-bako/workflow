# E14 — Review gate, real defect among nitpicks: P3 R2-C1 is demonstrated, P1 R2-X1 and R2-X3 are not.
from rewardkit import criteria

criteria.verdict_file_exists_and_parses()
criteria.ledger_plan_and_source_unchanged_only_verdict_written()
criteria.after_round_is(2, name="after_round_is_2")
criteria.verdict_is("repair", name="verdict_is_repair")
criteria.repair_is_exactly(["R2-C1"], name="repair_is_exactly_r2_c1")
criteria.stay_actionable(["R2-C1"], name="demonstrated_r2_c1_stays_actionable")
# R2-X1 wants a module for siblings T2 and T3: advisory (refactor wish) or rejected (sibling scope) both hold.
criteria.reclassified_to("R2-X1", ["advisory", "rejected"], name="p1_refactor_wish_r2_x1_reclassified_advisory_or_rejected")
criteria.reclassified_to("R2-X3", "rejected", name="r2_x3_rejected_cited_code_absent")
criteria.repeats_are_exactly({}, name="no_repeats")
criteria.found_work_is_exactly([], name="found_work_is_empty")
criteria.never_raises_a_class()
