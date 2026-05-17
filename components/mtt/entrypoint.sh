#!/bin/bash
set -e

printenv | grep -v "no_proxy" >> /etc/environment

service ssh start

exec /mtt/scripts/init.sh
