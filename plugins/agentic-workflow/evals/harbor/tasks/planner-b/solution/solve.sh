#!/bin/bash
# Oracle for E19: the owner's undecided rule goes back as one question.
set -euo pipefail
cat > /app/plan-report.json <<'EOF'
{
  "status": "blocked",
  "plan": null,
  "acceptance_mapping": [],
  "required_checks": [],
  "open_questions": [{"question": "The roadmap leaves undecided whether `#work,` or `#work.` is the tag `work` or no tag. Which?",
                      "recommendation": "Strip trailing punctuation: `#work,` is the tag `work`; the comma stays out of the title."}]
}
EOF
