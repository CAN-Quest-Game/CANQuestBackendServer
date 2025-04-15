TO RUN:
- Run python3 main.py
(optional, can do -v or --verbose for verbose)
- Run dummy_tcp.py to test
- Run algo_shams.py to easily get key value from seed if you're in a hurry

## About

**CANQuest** is a modular UDS server framework built on top of the python-can library.  
It lets you easily simulate ECUs and test automotive cybersecurity workflows in a plug-and-play environment.

## 🛠️ Features

- 📡 **SocketCAN Support**
- 🧪 **UDS Protocol (ISO 14229-1) Implementation**
- 🔌 **Modular ECU Support**
- 🧰 **Custom UDS Service Extensions**

## Installation & Setup

- Run `python -r requirements.txt`
- Run `sh setup.sh` to run dockerized container for server **(optional)**
- Entrypoint file is main, run `python3 main.py`
    - For verbose mode, run `python3 main.py -v` or `python3 main.py --verbose` 
- Need a client to test with? Run [dummy_tcp.py](dummy_tcp.py) (it's really dumb)!

## Adding Custom ECUs

## Adding Custom Services

## Contributors
