#!/usr/bin/env bash
set -euo pipefail

robot=${1:?robot id required}
source /etc/default/openvela-formation
test "$robot" = "$ROBOT_ID"
docker exec MentorPi pkill -f "^python3 /opt/openvela-formation/formation_lab/fleet_bridge.py --robot $robot( |$)" || true
