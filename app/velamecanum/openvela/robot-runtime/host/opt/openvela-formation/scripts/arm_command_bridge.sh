#!/usr/bin/env bash
set -euo pipefail

robot=${1:?robot id required}
seconds=${2:-10}
source /etc/default/openvela-formation
test "$robot" = "$ROBOT_ID"
if [ "$(id -u)" -ne 0 ]; then echo 'run with sudo' >&2; exit 2; fi
case "$seconds" in ''|*[!0-9]*) echo 'duration must be an integer' >&2; exit 2;; esac
test "$seconds" -ge 1 && test "$seconds" -le 30
systemctl is-active --quiet "formation-agent@$robot.service"
systemctl is-active --quiet "formation-command-bridge@$robot.service"
docker exec MentorPi python3 -c '
import json
config = json.load(open("/opt/openvela-formation/config/mentorpi.json"))
raise SystemExit(0 if config.get("hardware_output_enabled") is True else 1)
'
lease_id=$(cat /proc/sys/kernel/random/uuid)
expiry=$(python3 -c "import time; print(time.monotonic() + $seconds)")
docker exec --env LEASE_ROBOT="$robot" --env LEASE_ID="$lease_id" \
  --env LEASE_EXPIRY="$expiry" MentorPi python3 -c '
import json, os, pathlib
folder = pathlib.Path("/run/openvela-formation")
folder.mkdir(mode=0o755, exist_ok=True)
path = folder / "command-arm.json"
path.write_text(json.dumps({"robot": os.environ["LEASE_ROBOT"], "id": os.environ["LEASE_ID"],
                            "expires_mono": float(os.environ["LEASE_EXPIRY"])}))
path.chmod(0o644)
'
echo "Armed $robot for at most $seconds seconds (lease $lease_id)."
