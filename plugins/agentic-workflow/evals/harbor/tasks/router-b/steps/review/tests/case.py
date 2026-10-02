# Step 2, paired aw-refuter from the packet only. E12 control — the caller is converted in the diff and tested.
from rewardkit import criteria

criteria.review_report_exists_and_parses()
criteria.workspace_unchanged_except(["review-packet.md", "review-report.md", "review-report.json"],
                                    name="reviewer_changed_no_source_files")
criteria.reports_clean_without_invented_findings()
criteria.reviewer_did_no_blame_or_pull_request_archaeology()
