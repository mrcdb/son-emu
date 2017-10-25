#!/bin/bash
set -e

echo "vim-emu/devops-stages/stage-test.sh"

# trigger ovs setup since container entrypoint is overwritten by Jenkins
service openvswitch-switch start

# ensure the test image is there
docker pull 'ubuntu:trusty'

# debugging
echo "Tests executed inside: $(hostname)"
echo "Tests executed by user: $(whoami)"

# trigger the tests
cd /son-emu/
pwd
ls
ls src/
ls src/emuvim/
ls src/emuvim/test/
ls src/emuvim/test/unittest
py.test -v src/emuvim/test/unittest
