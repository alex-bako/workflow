# Step 1, aw-router packet. E12 control — the caller is converted in the diff and tested.
from rewardkit import criteria

criteria.packet_exists_within_150_lines()
criteria.packet_sections_in_order_without_ledger()
criteria.identity_names_exact_base_and_head()
criteria.contract_quotes_caller_acceptance_at_plan_line_10()
criteria.contract_quotes_invariant_at_plan_lines_15_16()
criteria.contract_refs_point_at_real_lines_not_whole_documents()
criteria.change_map_lists_invoice()
criteria.skip_lists_noise_and_must_read_excludes_it()
criteria.packet_states_no_review_verdict()
criteria.workspace_unchanged_except(["review-packet.md"], name="router_changed_no_source_files")
