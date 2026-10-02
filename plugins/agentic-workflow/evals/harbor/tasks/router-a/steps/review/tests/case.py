# Step 2, paired aw-refuter from the packet only. E12 — planted: the unchanged caller src/invoice.mjs prints cents as dollars.
from rewardkit import criteria

criteria.review_report_exists_and_parses()
criteria.workspace_unchanged_except(["review-packet.md", "review-report.md", "review-report.json"],
                                    name="reviewer_changed_no_source_files")
criteria.reports_invoice_prints_cents_as_dollars()
criteria.reviewer_did_no_blame_or_pull_request_archaeology()
