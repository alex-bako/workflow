# E11 — QA accepts a correct control (exactly T1).
from rewardkit import criteria

criteria.report_files_exist_and_parse()
criteria.qa_made_no_source_edits()
criteria.qa_made_no_git_mutations()
criteria.project_checks_report_actual_node_test_result()
criteria.acceptance_lines_evidenced_by_tests()
criteria.scope_fence_maps_changed_files()
criteria.reports_clean_with_no_invented_findings()
