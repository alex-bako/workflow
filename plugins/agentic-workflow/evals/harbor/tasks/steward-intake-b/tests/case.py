# E15 — Found work intake: the same flaky test is already open (#9, later); extend and raise it.
from rewardkit import criteria

criteria.no_direct_gh_calls()
criteria.tracker_calls_only_through_bundled_script()
criteria.state_changes_explained_by_logged_mutations()
criteria.tracker_commands_within(["file", "show", "rank", "note"], name="writes_only_through_granted_commands")
criteria.files_no_new_issue()
criteria.file_never_run_with_new()
criteria.notes_new_evidence_once(9, "4f2c9a1", 11, name="notes_3_of_20_on_4f2c9a1_or_pr_once_on_9")
criteria.ranks_found_issue(9, "urgent", name="raises_9_to_urgent")
criteria.writes_only_issue(9, name="no_issue_but_9_changed")
criteria.intake_project_files_unchanged()
criteria.intake_work_order_files_exist_and_parse()
criteria.work_order_reports_issue(9, "extended", "urgent", ["complete", "partial"],
                                  name="work_order_reports_9_extended_urgent_with_reason")
