# E13 — One pass of the loop, local boundary. Programmatic criteria only; see the
# README evaluator section for the parts that stay judge-only.
from rewardkit import criteria

criteria.no_direct_gh_calls()
criteria.tracker_calls_only_through_bundled_script()
criteria.state_changes_explained_by_logged_mutations()
criteria.log_orders_claim_card_bullets_claim_t1_plan()
criteria.plan_fences_t2_filter_and_t3_summary_out_of_scope()
criteria.plan_in_t1_issue_matches_plan_file()
criteria.changes_limited_to_t1_files_and_plan()
criteria.node_test_passes()
criteria.parse_item_examples_hold()
criteria.default_branch_untouched_and_no_merge_or_remote()
criteria.no_sync_to_in_review_or_done()
criteria.t2_not_started()
criteria.stops_with_in_flight_state_or_blocked_question()
