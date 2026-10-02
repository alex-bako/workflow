# E21 — An accepted decision record forbids what the roadmap asks (titles kept as typed): one question, nothing flags it.
from rewardkit import criteria

criteria.plan_report_exists_and_parses()
criteria.writes_only_the_plan()
criteria.one_open_question_with_recommendation(r"0004|verbatim|as typed|titles?\b.{0,60}\b(?:intact|unchanged|kept|rewrit\w*|drop\w*)")
