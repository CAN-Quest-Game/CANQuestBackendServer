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

## Function Reference

📁 [config.py](server/config.py)
| Variable Name   | Description                      | Value |
|-----------------|----------------------------------|-------------|
| wiper_status |  Changes status message based on wipers interaction. | Initialized 0x00, changes to 0x01 when wipers activated.
| status_lock | Threading lock that changes status message thread.  | Instantiated object of type Lock.
| verbose  |  When true, the server prints more status information/messages.    | Initialized to false, can change to true.
| client_sock | Client socket connection. | Initialized to none.
| server_socket | Server socket connection. | Initialized to none.
| stop_can | Threading event that changes active receiving of CAN messages. | Instantiated object of type Event.
| server_down | When true, indicates that server has completed shutdown. | Initialized to false.

📁 [can_handler.py](server/can_handler.py)
| Function Name   | Description                      | Arguments         |
|-----------------|----------------------------------|-------------------|
| init | Function to initialize the CAN_Handler class.  | - interface: CAN interface type (default is 'socketcan'). <br> - channel: CAN channel (default is 'vcan0'). <br> - bitrate: CAN bus bitrate (default is 500000). <br> - verbose: boolean flag to enable verbose output (default is False), taken from config.py              |
| setup   | Function to initialize CANBus Interface. | - self  |
| send_msg | Function to send a standard-length message on the CANbus. | - can_id: TX arbitration CAN ID of the message. <br> - data: Data to be sent in the message. <br> - is_multiframe: Boolean flag to indicate if the message is a multi-frame message (default is False). <br> - is_extended_id: Boolean flag to indicate if the message uses extended ID (default is False). <br> - is_status: Boolean flag to indicate if the message is a status message (default is False).|
| send_multiframe_msg | Function to send a multi-frame message on the CANbus. |- can_id: TX arbitration CAN ID of the message.<br> - data: Data to be sent in the message. <br> - is_extended_id: Boolean flag to indicate if the message uses extended ID (default is False).|
| recv_msg | Function to recieve a message on the CANbus. Actively listens through initialization. | self |
| shutdown | Function to close the CANbus interface. | self
| _initialize_ecus | Function to map the arbitration ID to the corresponding ECU. | self |
| get_ecus | Helper function to return request arbitration ID of the ECU. | - arb-id: request arbitration ID.
| broadcast_wiper_data | Function to broadcast wiper data on the CANbus. This function runs in a separate thread. Can disable if desired. | self |

📁 [main.py](main.py)
| Function Name   | Description                      | Arguments         |
|-----------------|----------------------------------|-------------------|
| can_message_handler | Function to handle CAN messages. It runs in a separate thread and continuously receives messages from the CAN bus. | - can_handler: instance of the CAN_Handler class. <br> - stop_can: threading.Event object to signal when to stop the thread. |
| client_handler | Function to handle client connections. It runs in a separate thread and continuously receives messages from the client. | - client_sock: socket object for the client connection. <br> - can_handler: instance of the CAN_Handler class. <br> - stop_can: threading.Event object to signal when to stop the thread. <br> - verbose: boolean flag to enable verbose output, taken from config.py |
| main | Main function to start the server and handle client connections. It sets up the CAN bus and starts threads for handling CAN messages and client connections. | - verbose: from config file


📁 [ecu.py](ecus/ecu.py)
| Function Name   | Description                      | Arguments         |
|-----------------|----------------------------------|-------------------|
| init | Function to initialize the ECU class. | - name: Name of the ECU. <br>- req_arb_id: Request arbitration ID for the ECU. <br>- rsp_arb_id: Response arbitration ID for the ECU.<br> - verbose: Boolean flag to enable verbose output (default is False), taken from config.py |
| initialize_services | Helper function to initialize the services dictionary. This function should be overridden in the derived classes. Returns dictionary of supported UDS services by ECU. Key: value pairs are formatted as {service_id (hex): service_object}. | - self |
| get_service | Helper function to get the service object based on the service ID. |  - service_id: Service ID to look up. |
| handle_request | Abstract method to handle UDS services flow based on message received by user. This method MUST be implemented in the derived classes. | - payload: Payload of the CAN message received. |

📁 [uds_services.py](services/uds_services.py)
| Function Name   | Description                      | Arguments         |
|-----------------|----------------------------------|-------------------|
| init | Function to initialize the UDS_Service class. | - self |
| construct_msg | Abstract method to construct the final response message payload. This method MUST be implemented in the derived classes. | - self |
| validate_length | Abstract method to validate the length of the payload. This method MUST be implemented in the derived classes. |- dlc: Data Length Code of the message. <br> - payload: Payload of the received CAN message. |
| subfunction | Abstract method to check the subfunction validity of the UDS service. This method MUST be implemented in the derived classes. | - self |
| positive_response | Abstract method to construct the positive response message. This method MUST be implemented in the derived classes. | - self |
| negative_response | Abstract method to construct the negative response message. This method MUST be implemented in the derived classes. | - self | 

## Contributors
- CANQuest Team: Shams Ahson