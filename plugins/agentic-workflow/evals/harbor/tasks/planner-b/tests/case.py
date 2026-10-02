# E19 — The authority file leaves a T1 behavior to the owner: one open question, no guess.
from rewardkit import criteria

criteria.plan_report_exists_and_parses()
criteria.writes_only_the_plan()
criteria.one_open_question_with_recommendation(r"punctuation|#work[,.]")
