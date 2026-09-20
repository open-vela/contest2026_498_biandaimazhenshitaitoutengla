#!/usr/bin/env bash
set -euo pipefail

robot=${1:?robot id required}
source /etc/default/openvela-formation
test "$robot" = "$ROBOT_ID"
docker exec MentorPi rm -f /run/openvela-formation/command-arm.json
echo "Disarmed $robot."
