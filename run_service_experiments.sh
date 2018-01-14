#!/bin/bash
rm -r service_results
rm -r osm_service_results
mkdir -p service_results
mkdir -p osm_service_results
./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t UsCarrier.graphml --result-path service_results/UsCarrier_r1.pkl
sleep 10

#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t UsCarrier.graphml --result-path service_results/UsCarrier_r2.pkl
#sleep 10

./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t UsCarrier.graphml --result-path service_results/UsCarrier_r3.pkl
sleep 10

#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t UsCarrier.graphml --result-path service_results/UsCarrier_r4.pkl
#sleep 10
#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t UsCarrier.graphml --result-path service_results/UsCarrier_r5.pkl
#sleep 10

#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t DeutscheTelekom.graphml --result-path service_results/DeutscheTelekom_r1.pkl
#sleep 10
#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t DeutscheTelekom.graphml --result-path service_results/DeutscheTelekom_r2.pkl
#sleep 10
#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t DeutscheTelekom.graphml --result-path service_results/DeutscheTelekom_r3.pkl
#sleep 10
#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t DeutscheTelekom.graphml --result-path service_results/DeutscheTelekom_r4.pkl
#sleep 10
#./re_install_osm.sh
#sleep 10
#sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t DeutscheTelekom.graphml --result-path service_results/DeutscheTelekom_r5.pkl
#sleep 10

./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t Abilene.graphml --result-path service_results/Abilene_r1.pkl
sleep 10
./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t Abilene.graphml --result-path service_results/Abilene_r2.pkl
sleep 10
./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t Abilene.graphml --result-path service_results/Abilene_r3.pkl
sleep 10
./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t Abilene.graphml --result-path service_results/Abilene_r4.pkl
sleep 10
./re_install_osm.sh
sleep 10
sudo python examples/evaluation_osm_zoo.py --experiment service -r 1 -t Abilene.graphml --result-path service_results/Abilene_r5.pkl
sleep 10

echo "Finished!"
ls service_results
ls -lisah osm_service_results
