#!/bin/bash

./generate_descriptor_pkg.sh -t vnfd -N ping
./generate_descriptor_pkg.sh -t vnfd -N pong
./generate_descriptor_pkg.sh -t nsd -N pingpong_nsd
