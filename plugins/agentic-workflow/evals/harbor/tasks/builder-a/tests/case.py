# E16 — Builder delivers the accepted plan T1, inside the fence, with tests that pin it.
from rewardkit import criteria

criteria.build_report_exists_and_parses()
criteria.no_git_mutations()
criteria.changes_only_t1_files()
criteria.project_checks_pass()
criteria.hidden_acceptance_passes()
criteria.existing_tests_kept()
criteria.own_tests_pass_on_reference_and_fail_every_mutant()
criteria.report_matches_reality()
