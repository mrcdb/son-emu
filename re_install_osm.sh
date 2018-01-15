#!/bin/bash
lxc delete -f RO SO-ub VCA
sleep 10
./install_osm.sh --lxdimages

