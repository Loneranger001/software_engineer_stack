#!/bin/sh
# scan-integrations.sh — evidence scan for integration mechanisms across repos.
#
# Usage: scan-integrations.sh [--max N] <repo> [repo...]
#   repo    repo root to scan (get the list from list-repos.sh <repos-folder>)
#   --max N cap hits shown per category per repo (default 15; the full count is
#           still reported)
#
# Prints a Markdown report: one section per integration category, each with the
# exact pattern used and every hit as <repo>:<file>:<line>. A category with no
# hits ANYWHERE prints an explicit "no matches" line — that negative result is
# the point. /estate-profile turns hits into `in-use` capability rows and
# no-match categories into evidenced absences, so a design can never propose a
# mechanism the estate does not have (see templates/platform-capabilities.md).
#
# This scan proves a mechanism is PRESENT IN CODE. It cannot prove a mechanism
# is permitted, supported, or safe for new use — those statuses come from the
# user at the confirmation step of /estate-profile, never from this output.
#
# Matches are redacted for credentials before printing, but the report may
# still contain hostnames and paths: review before pasting anywhere public.
set -eu

MAX=15
REPOS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --max) MAX="${2:?--max needs a number}"; shift 2 ;;
    --max=*) MAX="${1#--max=}"; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *) REPOS="$REPOS $1"; shift ;;
  esac
done

case "$MAX" in ''|*[!0-9]*) echo "error: --max must be a number" >&2; exit 2 ;; esac
[ -n "$REPOS" ] || { echo "error: no repo given (usage: scan-integrations.sh <repo>...)" >&2; exit 2; }
for r in $REPOS; do
  [ -d "$r" ] || { echo "error: not a directory: $r" >&2; exit 2; }
done

EXCLUDES="--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv
--exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=dist
--exclude-dir=build --exclude-dir=target --exclude-dir=work
--exclude-dir=.terraform --exclude-dir=.idea"

# category@@extended-regex (case-insensitive). Deliberately broad: a false
# positive costs one line of review, a false negative silently removes a
# capability the estate actually has.
CATEGORIES=$(cat <<'EOF'
file-transfer@@sftp|ftps|ftp[[:space:]]|rsync|lftp|scp[[:space:]]|mput|mget|ftplib|paramiko
scheduler@@crontab|cron\.d|insert_job|autosys|control-?m|ctmfw|\.jil|airflow|@daily|@hourly|quartz
database@@dblink|database[[:space:]]+link|tnsnames|sqlplus|sqlldr|expdp|impdp|jdbc:|cx_oracle|oracledb|psycopg|pymysql|pyodbc|sqlalchemy|create_engine
messaging@@kafka|confluent|rabbitmq|pika\.|amqp|activemq|solace|ibm_mq|pymqi|amqsput|dbms_aq|[^a-z]jms[^a-z]|servicebus|sqs
http-api@@requests\.(get|post|put|delete)|urllib|utl_http|wsdl|soap|curl[[:space:]]|wget[[:space:]]|swagger|openapi|endpoint
etl-tool@@informatica|pmcmd|datastage|dsjob|talend|ssis|\.dtsx|dbt[[:space:]]run|pentaho|abinitio|odi_
object-store@@boto3|s3://|aws[[:space:]]+s3|gsutil|gs://|azcopy|az[[:space:]]+storage|blob\.core|minio
container@@dockerfile|docker-compose|docker[[:space:]]+run|kubectl|helm[[:space:]]|openshift|podman|k8s
notification@@mailx|sendmail|smtplib|utl_smtp|hooks\.slack|slack_webhook|pagerduty|msteams
secrets-store@@wallet|vault|keyring|credstash|\.netrc|secretsmanager|keyvault
monitoring@@splunk|appdynamics|dynatrace|prometheus|grafana|nagios|zabbix|kibana|logstash
EOF
)

# Credentials never leave the repo: mask before anything is printed.
redact() {
  sed -E -e 's/([Ii][Dd][Ee][Nn][Tt][Ii][Ff][Ii][Ee][Dd][[:space:]]+[Bb][Yy][[:space:]]+)[^[:space:];]+/\1***/g' \
         -e 's/([Pp][Aa][Ss][Ss][A-Za-z_]*[[:space:]]*[=:][[:space:]]*)[^[:space:],;)"]+/\1***/g' \
         -e 's/([Tt][Oo][Kk][Ee][Nn][A-Za-z_]*[[:space:]]*[=:][[:space:]]*)[^[:space:],;)"]+/\1***/g' \
         -e 's/([Ss][Ee][Cc][Rr][Ee][Tt][A-Za-z_]*[[:space:]]*[=:][[:space:]]*)[^[:space:],;)"]+/\1***/g' \
         -e 's#(//[^/[:space:]:@]*):[^@[:space:]]*@#\1:***@#g' \
         -e 's#([A-Za-z0-9_.$-]+)/[^@/[:space:]"]+@#\1/***@#g' \
    | cut -c1-200
}

printf '# Integration scan — %s\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'Repos scanned:\n'
for r in $REPOS; do printf -- '- %s\n' "$(cd "$r" && pwd)"; done
printf '\nMatches are redacted for credentials. Presence in code is evidence a\n'
printf 'mechanism is IN USE; it is not evidence that new use is permitted.\n'

OIFS=$IFS
printf '%s\n' "$CATEGORIES" | while IFS= read -r entry; do
  [ -n "$entry" ] || continue
  CAT=${entry%%@@*}
  PAT=${entry#*@@}

  printf '\n## %s\n\n' "$CAT"
  printf '```\ngrep -rIniE --exclude-dir=... '\''%s'\'' <repo>\n```\n\n' "$PAT"

  TOTAL=0
  BODY=""
  for r in $REPOS; do
    ABS=$(cd "$r" && pwd)
    NAME=$(basename "$ABS")
    # shellcheck disable=SC2086
    HITS=$(grep -rIniE $EXCLUDES -- "$PAT" "$ABS" 2>/dev/null || true)
    if [ -z "$HITS" ]; then
      BODY="$BODY| $NAME | — | _searched, no references found_ |
"
      continue
    fi
    N=$(printf '%s\n' "$HITS" | wc -l | tr -d ' ')
    TOTAL=$((TOTAL + N))
    ROWS=$(printf '%s\n' "$HITS" | head -n "$MAX" \
      | sed -e "s#^$ABS/##" | redact \
      | sed -e 's/|/\\|/g' \
            -e "s#^\([^:]*:[0-9]*\):#| $NAME | \1 | #" \
            -e 's/$/ |/')
    BODY="$BODY$ROWS
"
    if [ "$N" -gt "$MAX" ]; then
      BODY="$BODY| $NAME | … | _${N} hits total, ${MAX} shown_ |
"
    fi
  done

  if [ "$TOTAL" -eq 0 ]; then
    printf '**No matches in any repo.** Absence is evidenced by the pattern above.\n'
    printf 'Confirm with the user before recording this capability as `absent` —\n'
    printf 'a mechanism can exist in the estate without appearing in these repos.\n'
  else
    printf '| repo | file:line | match (redacted) |\n|---|---|---|\n%s' "$BODY"
  fi
done
IFS=$OIFS

printf '\n---\n\nScan complete. Every row above is a candidate `in-use` capability row;\n'
printf 'every "no matches" category is a candidate `absent` row. Neither is final\n'
printf 'until the user confirms status (available / deprecated / requires-approval /\n'
printf 'forbidden) — see skills/estate-profile/SKILL.md §4.\n'
