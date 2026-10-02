# E14 — Review gate, nitpick spiral: round 2 holds only style findings, one recorded P1.
from rewardkit import criteria

criteria.verdict_file_exists_and_parses()
criteria.ledger_plan_and_source_unchanged_only_verdict_written()
criteria.after_round_is(2, name="after_round_is_2")
criteria.verdict_is("stop", name="verdict_is_stop")
criteria.repair_is_exactly([], name="repair_is_empty")
criteria.reclassified_to("R2-X1", "advisory", name="p1_style_finding_r2_x1_reclassified_advisory")
criteria.reclassified_to("R2-X2", "rejected", name="renaming_r2_x2_rejected")
criteria.repeats_are_exactly({"R2-X2": "R1-X1"}, name="r2_x2_is_the_only_repeat_of_answered_r1_x1")
criteria.found_work_is_exactly([], name="found_work_is_empty")
criteria.never_raises_a_class()
