# WordCount_FogComputing with Docker (show the Hottest N words)
The program was designed to demo the fog computing for word count. I was using Python3 and Docker to implement it.

### Prerequisites
The program needs to install [Docker](https://docs.docker.com/get-docker/) and [Docker-Compose](https://docs.docker.com/compose/).


### Getting Started
Follow the behind steps :
1. git clone the project
2. Check the docker env file if you need to edit the env file.
```
vim dockerComposeEnv
```
3. Build docker containers
```
docker build --no-cache --force-rm -f ./Dockerfile_Ubuntu -t hytao/fognode .
```
4. Start all nodes 
```
sudo chmod 777 docker_compose_*
./docker_compose_run.sh
```
5. if you want the ClientNode1 to send the data(test_data.txt) to FogNode1
```
docker exec -it ClientNode1 bash
====================================
( ==> wait for enter the clientnode bash)
===================================
( In ClientNode1 )
( ex: python3 main.py 2 <FOG_NODE_IP> <FOG_NODE_PORT>)
python3 main.py 2 172.20.11.1 5001
```
6. Check the CloudNode logs and we can see the Hottest N words 
```
docker logs -f CloudNode 
```