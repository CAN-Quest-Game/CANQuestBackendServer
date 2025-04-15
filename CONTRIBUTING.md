## About

**CANQuest** is a modular UDS server framework built on top of the python-can library.  
It lets you easily simulate ECUs and test automotive cybersecurity workflows in a plug-and-play environment.

## 🛠️ Features

- 📡 **SocketCAN Support**
- 🧪 **UDS Protocol (ISO 14229-1) Implementation**
- 🔌 **Modular ECU Support**
- 🧰 **Custom UDS Service Extensions**

## Installation & Setup

- Clone the repo by running `git clone https://github.com/CAN-Quest-Game/CANQuestBackendServer.git`
- Run `python -r requirements.txt`
- Run `sh setup.sh` to run dockerized container for server **(optional)**
- Entrypoint file is main, run `python3 main.py`
    - For verbose mode, run `python3 main.py -v` or `python3 main.py --verbose` 
- Need a client to test with? Run [dummy_tcp.py](utils/dummy_tcp.py) (it's really dumb)!
- Known issues are documented in Issues, feel free to create issues, but do not expect them to be integrated to this base platform!

## Adding Custom ECUs
- Add customizable ECUs in the [ecus](ecus/) folder!
- Inherit from abstract base class [ECU](ecus/ecu.py) and develop the four required methods & any additional ones.
- Remember to add your ECU to [CAN_handler](server/can_handler.py)'s ecu dictionary. Here's an example of the key:value pair format. It is `ECU_REQ_ARB_ID: [ECU_NAME, ECU_RSP_ARB_ID]`
```python
     ecu_dict = {
                0x123: ['ECM', 0x321], 
                0x456: ['BCM', 0x654], 
                0x789: ['VCU', 0x7FF]
                }
```
- Also in [CAN_handler](server/can_handler.py), instantiate your ECU by name. Example:
```python
    if name == "ECM":
        self.ecus[req_arb_id] = ECM(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
```
- `handle_request` is the most customizable function in the ECU base class. Implement your logic (security access, sessions) here!
- Reference the examples in the [ecus](ecus/) folder for more info!

## Adding Custom/More UDS Services
- UDS Services currently implemented include:
```python
    0x10: DiagnosticSessionControl()
    0x11: ECUReset()
    0x23: ReadMemoryByAddress()
    0x27: SecurityAccess()
    0x3E: TesterPresent()
```
- To add more UDS services, access the [services](/services) folder and create new files or add to [uds_services.py](/services/uds_services.py)
- Inherit from abstract base class UDS Service and develop the 6 required methods, along with any other necessary ones.
- Remember to initialize all services present on an ECU through instantiating the services in [initialize_services](ecus/ecu.py). Here is an example:
```python
    def initialize_services(self):
        return {
            0x10: DiagnosticSessionControl(),
            0x3E: TesterPresent()
        }
```
- **Best Practice**: overload existing services in your custom ECUs rather than change the base concrete implementations.
- Reference examples in [uds_services.py](/services/uds_services.py) or refer to the ISO 14229-1 standard.

## Contributors
CANQuest Team: Shams Ahson