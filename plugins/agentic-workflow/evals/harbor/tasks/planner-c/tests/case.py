# E20 — A larger T1: tags must also reach saved lists, through the project's migration convention.
from rewardkit import criteria

criteria.plan_report_exists_and_parses()
criteria.writes_only_the_plan()
criteria.plan_quotes_t1_acceptance_verbatim()
criteria.every_t1_line_mapped_to_a_test_check()
criteria.mapping_excludes_sibling_acceptance()
criteria.fence_names_t2_and_t3_out_of_scope()
criteria.plan_targets_t1_files()
criteria.plan_names_the_existing_expectation_that_breaks()
criteria.plan_adds_a_migration_step_and_bumps_the_version()
criteria.plan_tests_a_list_saved_at_version_2()
criteria.reports_complete_without_questions()
