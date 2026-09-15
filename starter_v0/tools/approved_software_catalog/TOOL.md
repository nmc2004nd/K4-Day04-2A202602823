---
name: approved_software_catalog
track: team-built
kind: local_catalog
provider: mock_software_catalog
requires_env: []
inputs: [team, os_family, category, software_name]
outputs: [results, snapshot_at]
side_effect: false
---
# approved_software_catalog

Looks up fictional Northstar Labs approved software by team, operating-system
family, and optional category or software name. It is read-only and returns
support-safe catalog metadata only.

Use this tool for software approval, allowed software, install eligibility, or
standard software list questions. It requires a specific team and OS family.
If either is missing or ambiguous, ask for clarification first.
