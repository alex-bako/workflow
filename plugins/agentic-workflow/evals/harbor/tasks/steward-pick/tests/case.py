# E7 — Steward picks the right bullet, read-only (mode next, no granted writes).
from rewardkit import criteria

criteria.no_direct_gh_calls()
criteria.tracker_calls_only_through_bundled_script()
criteria.tracker_commands_within(["next", "show", "work-order"], name="tracker_reads_only")
criteria.state_file_untouched()
criteria.mutation_log_absent_or_empty()
criteria.project_files_unchanged()
criteria.work_order_files_exist_and_parse()
criteria.selects_item(6, "U1.4 — Item notes", "https://github.com/acme/shop/issues/6",
                      name="returns_6_u1_4_with_script_url")
criteria.authority_location("ROADMAP.md", "U1.4 — Item notes",
                            name="authority_location_roadmap_u1_4")
criteria.dependency_state(1, "CLOSED", name="dependency_u0_1_reported_closed")
criteria.acceptance_lines_verbatim(
    ["A note of up to 500 characters can be saved on an item.",
     "The note is shown under the item title in the list."],
    name="acceptance_lines_verbatim")
criteria.bullet_first_sibling_out_of_scope("T1", "T2", name="bullet_t1_first_t2_out_of_scope")
criteria.names_a_branch()
criteria.plan_is_none()
criteria.next_step_is_claim()
criteria.reports_no_tracker_writes()
criteria.offers_alternate(7, name="offers_u1_5_as_alternate")
criteria.never_offers([2, 3, 4, 5, 8], name="never_offers_u1_1_u1_2_u1_3_u0_2_or_epic")
criteria.reports_drift_quoting(5, "Waits on owner decision D3",
                               name="reports_u1_3_drift_quoting_d3_line")
