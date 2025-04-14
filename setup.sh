#!/bin/bash

echo "Checking if Python3 is installed..."
if ! command -v python3 > /dev/null; then
    echo "Installing Python3..."
    sudo apt update
    sudo apt install python3
else
    echo "Python3 is already installed."
fi

echo "Checking if pip is installed..."
if ! command -v pip3 > /dev/null; then
    echo "Installing pip3..."
    sudo apt install- python3-pip
else
    echo "pip3 is already installed."
fi

echo "Checking if can-utils is installed..."
if ! command -v candump > /dev/null; then
    echo "Installing can-utils..."
    sudo apt install can-utils
else
    echo "can-utils is already installed."
fi

echo "Checking if Caring-Caribou tool is installed..."
if ! command caringcaribou -h > /dev/null && ! command cc.py -h > /dev/null; then
    echo "Installing Caring-Caribou tool..."
    git clone https://github.com/CaringCaribou/caringcaribou.git
    cd caringcaribou
    sudo pip3 install -r requirements.txt
    sudo python3 setup.py install
else
    echo "Caring-Caribou tool is already installed."
fi

echo "Checking for ~/.canrc file..."
if [ ! -f $HOME/.canrc ]; then
    echo "Creating .canrc file..."
    printf "[default]\ninterface = socketcan\nchannel = can0" > $HOME/.canrc
else
    echo "~/.canrc file already exists."
fi

if ip link show vcan0 > /dev/null; then
    echo "vcan0 interface is already setup."
else
    echo "Setting up vcan0 interface..."
    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set vcan0 up
fi

echo "\n------------------MESSAGE FROM THE WHITE HAT-------------------------"
echo "Setup complete! Try dumping all can messages with candump vcan0."
echo "Caring-Caribou is a helpful tool you can explore by running caringcaribou -h or cc.py -h."

#echo "Pulling latest server image..."
sudo docker pull canquest0/my-can-handler-image:latest >/dev/null

echo "Starting server container..."
sudo docker run -it --rm --network=host --name my-can-handler-container canquest0/my-can-handler-image:latest

