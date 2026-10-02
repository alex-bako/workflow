# E10 — QA catches scope creep (planted variant: T1 + T2's filter + format refactor).
from rewardkit import criteria

criteria.report_files_exist_and_parse()
criteria.qa_made_no_source_edits()
criteria.qa_made_no_git_mutations()
criteria.project_checks_report_actual_node_test_result()
criteria.acceptance_lines_evidenced_by_tests()
criteria.scope_fence_finding_in(["src/filter.mjs", "test/filter.test.mjs"],
                                name="flags_t2_filter_as_scope_fence_finding")
criteria.scope_fence_finding_in(["src/format.mjs"],
                                name="flags_format_refactor_as_scope_fence_finding")
criteria.no_finding_blames_t1_change()
criteria.status_reports_findings()
