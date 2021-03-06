#!/bin/bash

# If display is not working:
# To access display add run "xhost +local:docker" before starting Docker
# via: https://askubuntu.com/questions/793100/start-gui-application-in-docker-container-with-sudo

xhost +local:docker

# nvidia-docker image
image=vframe:latest
docker images $image

# Jupyter notebook port
while getopts 'p:' flag; do
  case "${flag}" in
    p) port="${OPTARG}";;
    *) error "Unexpected option ${flag}" ;;
  esac
done

if [ ! -z "$port" ]; then
    echo "Port selected: $port"
else
    port="9090"
fi

docker_port="$port:$port"

# Either for main UNAS drive or for mobile UNAS drive
if [ -d "/media/adam/unas2go" ]; then
    data_store="/media/adam/unas2go/data_store"
elif [ -d "/media/adam/unas2go" ]; then
    data_store="/media/adam/unas2go/data_store"
elif [ -d "/media/adam/ah3tb" ]; then
    data_store="/media/adam/ah3tb/data_store"
elif [ -d "/media/undisclosed/unas2go" ]; then
    data_store="/media/undisclosed/unas2go/data_store"
elif [ -d "/mnt/unas" ]; then
    data_store="/mnt/unas/data_store"
else
    echo '[-] No data_store available. Exiting.'
    exit 0
fi
echo $data_store
# Get absolute path to vframe on local drive, could be refined
DOCKER_DIR=$(readlink -f "$0")
DOCKER_DIR_P1="$(dirname "$DOCKER_DIR")"
DOCKER_DIR_P2="$(dirname "$DOCKER_DIR_P1")"
#DOCKER_DIR_P3="$(dirname "$DOCKER_DIR_P2")"
vframe="$(dirname "$DOCKER_DIR_P2")"
echo $vframe

# --------------------------------------------------------

echo "
 __      ________ _____            __  __ ______ 
 \ \    / /  ____|  __ \     /\   |  \/  |  ____|
  \ \  / /| |__  | |__) |   /  \  | \  / | |__   
   \ \/ / |  __| |  _  /   / /\ \ | |\/| |  __|  
    \  /  | |    | | \ \  / ____ \| |  | | |____ 
     \/   |_|    |_|  \_\/_/    \_\_|  |_|______|
                                                 
                                            
Visual Forensics and Advanced Metadata Extraction

Stats:
display=$DISPLAY
port=$docker_port

Jupyter:
jupyter notebook --port $port --ip 0.0.0.0 --allow-root --no-browser

"


# TODO
# Make ports accessible to jupyter
# maybe fix the unix display bug
#--workdir=$(pwd)
#--user $(id -u) \

nvidia-docker run -it --privileged \
	--hostname VFRAME-$(hostname|sed -e 's/ubuntu-//') \
	--volume /tmp/.X11-unix:/tmp/.X11-unix \
    --volume="$data_store:/data_store" \
    --volume="$vframe:/vframe" \
    --volume="/home/$USER:/home/$USER" \
    --volume="/etc/group:/etc/group:ro" \
    --volume="/etc/passwd:/etc/passwd:ro" \
    --volume="/etc/shadow:/etc/shadow:ro" \
    --volume="/etc/sudoers.d:/etc/sudoers.d:ro" \
    -e DISPLAY=unix$DISPLAY \
    -p $docker_port \
    -e 'DARKNET_NP=/opt/darknet_ah' \
    -e "PASSWORD=none" \
	-e "USER_HTTP=1" \
    $image "$@"
[ "$sshx" = "true" ] && kill %1 # kill backgrounded socat