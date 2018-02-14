#!/bin/bash

set -e
set -x

# need to call containernet's entrypoint to enable OVS
exec /containernet/util/docker/entrypoint_centos.sh $*
