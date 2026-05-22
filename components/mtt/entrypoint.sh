#!/bin/bash
set -e

printenv | grep -v "no_proxy" >> /etc/environment

echo "127.0.0.1 localhost" >> /etc/hosts

service ssh start

exec /mtt/scripts/init.sh
