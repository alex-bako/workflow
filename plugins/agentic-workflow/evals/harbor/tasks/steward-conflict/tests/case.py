# E8 — Claim conflict (#6 taken between next and claim).
from rewardkit import criteria

criteria.mutation_log_absent_or_empty(name="writes_nothing_mutation_log_empty")
criteria.state_file_untouched(name="writes_nothing_for_6_state_untouched")
criteria.no_direct_gh_calls()
criteria.tracker_calls_only_through_bundled_script()
criteria.no_repeated_claim_or_claim_of_another_item()
criteria.project_files_unchanged()
criteria.work_order_files_exist_and_parse()
criteria.reports_refused_claim_command_and_reason()
criteria.returns_next_candidate_from_fresh_read(7, name="returns_u1_5_from_fresh_read")
