#!/bin/bash
echo "vim-emu/devops-stages/stage-test.sh"

# trigger ovs setup since container entrypoint is overwritten by Jenkins
service openvswitch-switch start

# ensure the test image is there
docker pull 'ubuntu:trusty'

# debugging
echo "Tests executed inside: $(hostname)"
whoami

# trigger the tests
cd /son-emu/; pwd; py.test -v src/emuvim/test/unittest
