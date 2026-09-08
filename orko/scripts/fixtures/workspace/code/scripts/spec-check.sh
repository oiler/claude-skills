#!/usr/bin/env bash
# Specification readiness check.
#
# Usage: scripts/spec-check.sh SPEC-NNN [--docs <path>]
#
# Advisory before implementation begins; required by release-check.sh for
# every spec in the release manifest. Reports structural gaps in a spec and
# its delivery plan. It checks that sections have content, not that the
# content is good; that remains the approver's job.
set -uo pipefail

[[ $# -ge 1 ]] || { sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
spec_id=$1; shift
docs=""
while [[ $# -gt 0 ]]; do
  case $1 in --docs) docs=$2; shift 2 ;; *) echo "unknown argument: $1" >&2; exit 2 ;; esac
done
code="$(cd "$(dirname "$0")/.." && pwd)"
docs="${docs:-$code/../docs}"
docs="$(cd "$docs" 2>/dev/null && pwd)" || { echo "FAIL docs repository not found; pass --docs <path>"; exit 1; }

fail=0
fail() { echo "FAIL $*"; fail=1; }
warn() { echo "warn $*"; }
ok()   { echo "ok   $*"; }
field() { sed -nE "s/^[[:space:]]*$2:[[:space:]]*//p" "$1" | head -1 | sed -E 's/^"(.*)"$/\1/'; }
# Bracketed tokens outside fenced code, inline code, markdown links, checkboxes, and YAML ID lists.
placeholders() {
  awk '/^[[:space:]]*```/ {fence=!fence; next} !fence {gsub(/`[^`]*`/, ""); print NR":"$0}' "$1" \
    | grep -E '\[[^]]+\]' \
    | grep -vE '\]\(|\[ \]|\[x\]|\[[A-Z]+-[0-9]+(, ?[A-Z]+-[0-9]+)*\]' || true
}
# section <file> <heading> -> body lines that are not blank, comments, or sub-headings
section() {
  awk -v h="## $2" '
    $0 == h {on=1; next}
    on && /^## / {exit}
    on {print}
  ' "$1" | grep -vE '^[[:space:]]*$|^<!--|^###' || true
}

spec=$(ls "$docs"/versions/*/specs/"$spec_id"*.md 2>/dev/null | head -1)
[[ -n $spec ]] || { fail "$spec_id: no file matching versions/*/specs/$spec_id*.md"; echo; echo "NOT READY"; exit 1; }
rel=${spec#$docs/}
ok "$rel"

# Frontmatter
dossier=$(echo "$rel" | sed -E 's|versions/([^/]+)/.*|\1|')
pv=$(field "$spec" product_version)
[[ $pv == "$dossier" ]] && ok "product_version $pv matches dossier" || fail "product_version '$pv' but file is in versions/$dossier/"
st=$(field "$spec" status); ap=$(field "$spec" approved_at); owner=$(field "$spec" owner)
[[ -n $owner && $owner != *"["* ]] && ok "owner $owner" || fail "owner not set"
case $st in
  accepted) [[ -n $ap && $ap != null ]] && ok "accepted $ap" || fail "status accepted but approved_at is null" ;;
  *) warn "status is $st; implementation should wait for accepted" ;;
esac

# Placeholders
left=$(placeholders "$spec")
[[ -z $left ]] && ok "no placeholders" || fail "placeholders remain:"$'\n'"$left"

# Requirements
reqs=$(grep -oE '^### R[0-9]+' "$spec" | sed 's/### //' || true)
[[ -n $reqs ]] && ok "requirements: $(echo $reqs | tr '\n' ' ')" || fail "no '### R1' requirement headings"

# Acceptance criteria: Given/when/then lines that are not the template's
ac=$(section "$spec" "Acceptance criteria" | grep -iE '^- given .*when .*then ' || true)
if [[ -z $ac ]]; then
  fail "no Given/when/then acceptance criteria"
else
  ok "$(echo "$ac" | wc -l | tr -d ' ') acceptance criteria"
fi

# Sections that must have content
for h in "Problem and intended outcome" "Users and scenarios" "Evidence and classification" "Scope" "Non-goals" "Failure and recovery behavior" "Data, privacy, security, and accessibility"; do
  [[ -n $(section "$spec" "$h") ]] && ok "section: $h" || fail "empty section: $h"
done

# Delivery plan
plan=$(grep -lE "^[[:space:]]*- $spec_id\$" "$docs"/versions/"$dossier"/plans/PLAN-*.md 2>/dev/null | head -1)
if [[ -z $plan ]]; then
  warn "no PLAN under versions/$dossier/plans/ implements $spec_id"
else
  ok "plan ${plan#$docs/}"
  for r in $reqs; do
    grep -qE "^\|[[:space:]]*$spec_id $r[[:space:]]*\|" "$plan" && ok "plan maps $r" || fail "plan does not map $spec_id $r"
  done
  grep -E "^\|[[:space:]]*$spec_id R[0-9]+" "$plan" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$4); if ($4=="" || $4 ~ /^\[/) bad=1} END {exit bad}' \
    && ok "every mapping row names verification evidence" || fail "a mapping row has empty or placeholder verification evidence"
  left=$(placeholders "$plan")
  [[ -z $left ]] && ok "plan has no placeholders" || fail "plan placeholders remain:"$'\n'"$left"
fi

echo
[[ $fail -eq 0 ]] && echo "READY $spec_id" || echo "NOT READY $spec_id"
exit $fail
