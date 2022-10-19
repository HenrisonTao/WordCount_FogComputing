# WordCount_FogComputing with Docker (show the Hottest-N words)
The program was designed to demo the fog computing for word count. I was using Python3 and Docker to implement it.
![arch](https://user-images.githubusercontent.com/17466501/196716419-670d7343-4a67-411c-8bf5-8162a80b7e46.png)
![screenshot](https://user-images.githubusercontent.com/17466501/196716526-341017d8-22e1-40f4-952e-1d7b715baba4.png)

### Prerequisites
The program needs to install [Docker](https://docs.docker.com/get-docker/) and [Docker-Compose](https://docs.docker.com/compose/).

### Getting Started
Follow the steps :
1. git clone the project
```
git clone https://github.com/HenrisonTao/WordCount_FogComputing.git
cd WordCount_FogComputing
```
2. Check the docker env file if you need to edit the env file.
```
vim dockerComposeEnv
```
3. Build or pull docker image\
Option1 : build image
```
docker build --no-cache --force-rm -f ./Dockerfile_Ubuntu -t hytao/fognode
```
Option2 : pull image
```
docker pull hytao/fognode
```
4. Start all nodes 
```
sudo chmod 777 docker_compose_*
./docker_compose_run.sh
```
5. if you want the ClientNode1 to send the data(test_data.txt) to FogNode1
```
docker exec -it ClientNode1 bash
```
Wait for enter the ClientNode1 bash then run the commands
( #&gt; python3 main.py 2 &lt;FOG_NODE_IP&gt; &lt;FOG_NODE_PORT&gt;)
```
python3 main.py 2 172.20.11.1 5001
```
6. Check the CloudNode logs and we can see the Hottest-N words 
```
docker logs -f CloudNode 
```
7. If you want to change the text_data in client node.
( #&gt; docker cp ./text_data.txt &lt;ClientNode Name&gt;:./text_data.txt)
```
docker cp ./src_code/text_data.txt ClientNode1:./text_data.txt
```
