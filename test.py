import sys
import can
import time
import random
import socket
from dataclasses import dataclass

# Constants
IP = '127.0.0.1'
PORT = 5015
VIN = "1FMCU9C74AKB96069"
CAN_INTERFACE = 'vcan0'
VERBOSE = 0

# Service registry
SERVICES = {
    0x10: "DiagnosticSessionControl",
    0x11: "ECUReset",
    0x3E: "TesterPresent",
    0x27: "SecurityAccess",
    0x22: "ReadDataByIdentifier",
    0x23: "ReadMemoryByAddress",
    0x2E: "WriteDataByIdentifier",
    0x31: "RoutineControl",
    
    # Add other services...
}

# Encapsulate global state
@dataclass
class CANState:
    session: int = 1
    security_access: int = 0
    attempts: int = 0
    key: list = None

# CAN Handler
class CANHandler:
    def __init__(self, interface):
        self.state = CANState()
        self.bus = self.setup_can(interface)

    def setup_can(self, interface):
        try:
            print(f"Setting up CAN interface {interface}...")
            return can.interface.Bus(interface='socketcan', channel=interface, bitrate=500000)
        except OSError:
            print(f"Cannot find {interface} interface.")
            sys.exit(1)

    def send_msg(self, arb_id, data, is_extended=False):
        try:
            msg = can.Message(arbitration_id=arb_id, data=data, is_extended_id=is_extended)
            self.bus.send(msg)
            if VERBOSE:
                print(f"Message sent on {self.bus.channel_info}")
        except can.CanError:
            print("Message NOT sent")

    def recv_msg(self):
        try:
            message = self.bus.recv()  # Wait until a message is received.
            data = ''.join(f'{byte:02x} ' for byte in message.data)
            return message, data
        except KeyboardInterrupt:
            print('\nRecv Msg Keyboard interrupt')
            self.bus.shutdown()
            sys.exit(0)

# Service Handlers
class UDSHandler:
    def __init__(self, state, can_handler):
        self.state = state
        self.can_handler = can_handler

    def handle_request(self, can_id, payload):
        if can_id == 0x123:
            print("ECM module")
            self.handle_ecm_request(payload)
        elif can_id == 0x456:
            print("BCM module")
            self.handle_bcm_request(payload)
        elif can_id == 0x789:
            print("VCU module")
            self.handle_vcu_request(payload)
        else:
            print(f"Unknown CAN ID: {can_id}")
            #self.can_handler.send_msg(0x7F, [0x12, 0x34, 0x78, 0x56, 0x00, 0x00, 0x00, 0x00])

    def handle_ecm_request(self, payload):
        payload = payload.split()
        #print(payload)
        print(f"ECM Request: {payload}")
        service_id = payload[1]
        print(service_id)
        if service_id == 0x3E:
            print("Tester Present Enabled")
            if len(payload) < 2: 
                self.can_handler.send_msg(0x321, [0x03, 0x7F, service_id, 0x13]) #incorrectMessageLengthOrInvalidFormat
                return
            pid = int(payload[3:5],16)
            if pid == 0x01:
                self.state.CANState.session = 1			
                self.can_handler.send_msg(0x321, [0x02, id+0x40, pid]) 
                self.can_handler.send_msg(0x321, [0x10, 0x21, 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x62]) 
                self.can_handler.send_msg(0x321, [0x21, 0x6C, 0x61, 0x73, 0x74, 0x6F, 0x66, 0x66])
                self.can_handler.send_msg(0x321, [0x22, 0x7D])
				#client_sock.sendall(b"START CAR!!!!!!!!!!!!!!")
            else:
                self.state.CANState.session = 3
                self.can_handler.send_msg(0x321, [0x03, 0x7F, service_id, 0x11]) #subfunctionNotSupported	

    def handle_bcm_request(self, payload):
    
        '''IDK YET'''
    def handle_bscm_request(self, payload):
        print("BSCM Module")
        # Add BSCM-specific handling logic here.

# Helper functions
def get_id_string(service_id):
    prefix = ""
    if 0x10 <= service_id <= 0x3e or 0x80 <= service_id <= 0xbe:
        prefix = "Request_"
    elif 0x50 <= service_id <= 0x7e or 0xc0 <= service_id <= 0xfe:
        prefix = "PosResponse_"
        service_id -= 0x40

    if service_id == 0x7f:
        return "NegResponse"

    return prefix + SERVICES.get(service_id, f"UNKNOWN_{service_id:02x}")

def key_from_seed(seed):
    secret = [0x5B, 0x41, 0x74, 0x65, 0x7D]
    return [(seed_byte ^ secret_byte) for seed_byte, secret_byte in zip(seed, secret)]

# Main
def main():
    can_handler = CANHandler(CAN_INTERFACE)
    uds_handler = UDSHandler(can_handler.state, can_handler)

    while True:
        message, data = can_handler.recv_msg()
        print(f"Received message: {data}")
        uds_handler.handle_request(message.arbitration_id, data)

if __name__ == "__main__":
    main()
