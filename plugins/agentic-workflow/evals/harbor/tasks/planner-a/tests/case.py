# E18 — Planner writes the T1 plan from the work order: verbatim acceptance, fence, checks.
from rewardkit import criteria

criteria.plan_report_exists_and_parses()
criteria.writes_only_the_plan()
criteria.plan_quotes_t1_acceptance_verbatim()
criteria.every_t1_line_mapped_to_a_test_check()
criteria.mapping_excludes_sibling_acceptance()
criteria.fence_names_t2_and_t3_out_of_scope()
criteria.plan_targets_t1_files()
criteria.plan_names_the_existing_expectation_that_breaks()
criteria.reports_complete_without_questions()
