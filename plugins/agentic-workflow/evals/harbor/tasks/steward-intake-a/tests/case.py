# E15 — Found work intake: a new flaky test with evidence is filed once, ranked urgent.
from rewardkit import criteria

criteria.no_direct_gh_calls()
criteria.tracker_calls_only_through_bundled_script()
criteria.state_changes_explained_by_logged_mutations()
criteria.tracker_commands_within(["file", "show", "rank", "note"], name="writes_only_through_granted_commands")
criteria.files_one_found_issue_ranked("urgent", name="files_one_found_issue_labelled_found_and_urgent")
criteria.writes_only_the_new_issue()
criteria.new_issue_body_has_required_sections()
criteria.new_issue_body_states_artifact_facts(
    "node --test test/storage.test.mjs", "saves and reloads an item", "4f2c9a1", 11, 1,
    name="body_states_command_test_3_of_20_commit_or_pr_and_found_in_1")
criteria.new_issue_invents_no_frequency()
criteria.intake_project_files_unchanged()
criteria.intake_work_order_files_exist_and_parse()
criteria.work_order_reports_issue(0, "filed", "urgent", ["complete"],
                                  name="work_order_reports_filed_issue_urgent_with_reason")
