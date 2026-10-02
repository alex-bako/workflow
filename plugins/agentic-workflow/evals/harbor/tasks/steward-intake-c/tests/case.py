# E15 — Found work intake: a vague report without evidence is not filed.
from rewardkit import criteria

criteria.no_direct_gh_calls()
criteria.tracker_calls_only_through_bundled_script()
criteria.runs_no_write_command()
criteria.mutation_log_absent_or_empty()
criteria.state_file_untouched()
criteria.intake_project_files_unchanged()
criteria.intake_work_order_files_exist_and_parse()
criteria.reports_blocked_naming_missing_evidence()
