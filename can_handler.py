import sys
import can
import time
import random
import socket
import threading
import re
from abc import ABC, abstractmethod
import uds_services
from uds_services import *
import ipaddress

        
class CAN_Handler:
    '''Class to handle CANbus initialization, message sending and recieving.'''
    def __init__(self, interface='socketcan', channel='vcan0', bitrate=500000, verbose=False):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus = None
        self.ecus = {}
        self._initialize_ecus()

    def setup(self):
        '''Initialize the CANbus interface.'''
        try:
            print(f"Setting up CAN interface {self.channel}...")
            self.bus = can.interface.Bus(interface=self.interface, channel=self.channel, bitrate=self.bitrate)
        except OSError as e:
            print(f"Error setting up CAN interface: {e}")
            sys.exit(1)

    def send_msg(self, can_id, data, is_multiframe=False, is_extended_id=False, is_status=False):
        '''Send a message on the CANbus.'''
        try:
            if is_multiframe is True:
                self.send_multiframe_msg(can_id, data, is_extended_id)
                return
            if is_status is True:
                message = can.Message(arbitration_id=can_id, data=data, is_extended_id=is_extended_id)
                self.bus.send(message)
                return
            dlc = len(data)
            final_data = []
            final_data = [dlc] + data
            message = can.Message(arbitration_id=can_id, data=final_data, is_extended_id=is_extended_id)
            self.bus.send(message)
            if (verbose): print(f"Sent message: {message}")
            #if (verbose): print(f"Message sent on {bus.channel_info}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def send_multiframe_msg(self, can_id, data, is_extended_id=False):
        '''Send a multi-frame message on the CANbus.'''
        try:
            dlc = len(data)
            updated_data = [dlc] + data
            #print("Updated data:", updated_data)
            #print(len(updated_data))
            frame_size = 7
            num_frames = (len(updated_data)  + (frame_size - 1)) // frame_size
            #print(num_frames)
            btf_sequences = [0x10, 0x21, 0x22, 0x23, 0x24, 0x25]
            for f in range(0, num_frames):
                btf = btf_sequences[f]
                frame = updated_data[f*frame_size:(f+1)*frame_size]
                final_frame = [btf] + frame
                #print([hex(x) for x in final_frame])
                message = can.Message(arbitration_id=can_id, data=final_frame, is_extended_id=is_extended_id)
                self.bus.send(message)
                if (verbose): print(f"Sent message: {message}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def recv_msg(self):
        '''Recieve a message on the CANbus.'''
        try:
            message = self.bus.recv()
            if (verbose): print(f"Received message: {message}")
            parsed = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
            payload = ''
            for i in range(message.dlc):
          #      payload += '{0:x} '.format(message.data[i])
                payload += '{:02x} '.format(message.data[i])

            ecu = self.get_ecu(message.arbitration_id)
            if ecu:
                ecu.handle_request(payload, self)
            else:
                if (verbose): print("ECU not found")
            return message, payload
        
        except KeyboardInterrupt:
            client_sock.sendall("SHUTDOWN".encode('utf-8'))
            print('\n\rRecv Msg Keyboard interrupt. Bye!')
            self.shutdown()
            exit(0)

    def shutdown(self):
        '''Close the CANbus interface.'''
        print("Shutting down CAN interface...")
        self.bus.shutdown()
   
    def listener(self):
            data = client_sock.recv(1024).decode()
            print('\n' + f"Received from client: {data}" + '\n')
    
    def _initialize_ecus(self):
        '''Map the arbitration ID to the corresponding ECU.'''
        ecu_dict = {
                0x123: ['ECM', 0x321], 
                0x456: ['BCM', 0x654], 
                0x789: ['VCU', 0x7FF]
                }
        for req_arb_id, (name, rsp_arb_id) in ecu_dict.items():
            if name == "ECM":
                self.ecus[req_arb_id] = ECM(name, req_arb_id, rsp_arb_id, verbose=verbose)
            elif name == "BCM":
                self.ecus[req_arb_id] = BCM(name, req_arb_id, rsp_arb_id, verbose=verbose)
            elif name == "VCU":
                self.ecus[req_arb_id] = VCU(name, req_arb_id, rsp_arb_id, verbose=verbose)
    
    def get_ecu(self,arb_id):
        return self.ecus.get(arb_id)
    
    def broadcast_wiper_data(self):
        global wiper_status
        while True:
            with status_lock:
                stat_msg = [wiper_status, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            self.send_msg(0x058, stat_msg, is_status=True)
            time.sleep(0.1)

    
class ECU(ABC):
    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=False):
        self.name = name
        self.req_arb_id = req_arb_id
        self.rsp_arb_id = rsp_arb_id
        self.supported_services = self.initialize_services()
        self.active_session = None #initialize to default session

    #TODO:add self.security_level checks
    #add self.session checks
        
    def initialize_services(self):
            pass
    
    def get_service(self, service_id):
        service = self.supported_services.get(service_id)
        if not service:
            if (verbose): print(f"Service ID {hex(service_id)} not found.")
        return service
    
    @abstractmethod
    def handle_request(self, payload):
        pass

class ECM(ECU):
    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=False):
        super().__init__(name, req_arb_id, rsp_arb_id, verbose=False)

    def initialize_services(self):
        return {
            0x10: DiagnosticSessionControl(),
            0x3E: TesterPresent()
        }

    def handle_request(self, payload, cansend, verbose=False):
        if (verbose): print(len(payload))
        payload_bytes = re.split(r'\s+', payload)
        dlc = payload_bytes[0]
        service_id = int(payload_bytes[1], 16)
        if (verbose): print(service_id)
        service=self.get_service(service_id)
        
        if service is None:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
            return
        elif service.validate_length(dlc, payload_bytes) is False:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
            return

        
        if isinstance(service, DiagnosticSessionControl):
            self.active_session = service.get_diagnostic_session(payload_bytes)
            if (verbose): print("Active session is:", self.active_session)
        rsp = service.construct_msg(payload_bytes)
        if (verbose): print(rsp)
        if self.active_session == 0x01: #maybe not the best way to do this
            if rsp == [0x7E, 0x01]:
                if(verbose): print("success yuh")
                cansend.send_msg(self.rsp_arb_id, rsp)
                cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x62, 0x6C, 0x61, 0x73, 0x74, 0x6F, 0x66, 0x66, 0x7D], is_multiframe=True)
                client_sock.sendall("0x00".encode('utf-8'))
            else:
                cansend.send_msg(self.rsp_arb_id, rsp)
        else:
            cansend.send_msg(self.rsp_arb_id, rsp)

class BCM(ECU):
    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=False):
        super().__init__(name, req_arb_id, rsp_arb_id, verbose=False)

    def initialize_services(self):
        return {
            0x10: DiagnosticSessionControl(),
            0x11: ECUReset(),
            }
    
    def handle_request(self, payload, cansend):
        global wiper_status
        if (verbose): print("BCM")
        if (verbose): print(len(payload))
        payload_bytes = re.split(r'\s+', payload)
        dlc = payload_bytes[0]
        service_id = int(payload_bytes[1], 16)
        if (verbose): print(service_id)
        service=self.get_service(service_id)
        
        if service is None:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
            return
        elif service.validate_length(dlc, payload_bytes) is False:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
            return
        
        if isinstance(service, DiagnosticSessionControl):
            self.active_session = service.get_diagnostic_session(payload_bytes)
            if (verbose): print("Active session is:", self.active_session)
        rsp = service.construct_msg(payload_bytes)
        if (verbose): print(rsp)
        if self.active_session == 0x03:
            if rsp == [0x51, 0x03]:
                if (verbose): print("success yuh")
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x78])
                # cansend.send_msg(self.rsp_arb_id, rsp)
                # cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x74, 0x72, 0x69, 0x63, 0x6B, 0x79, 0x5F, 0x6C, 0x65, 0x76, 0x65, 0x6C, 0x73, 0x7D], is_multiframe=True)
                with status_lock:
                    wiper_status = 0x01
                if (verbose): print("Wipers activated")
                client_sock.send("0x0D".encode('utf-8'))
                time.sleep(15)
                with status_lock:
                    wiper_status = 0x00
                if (verbose): print("Wipers off, reset complete")
                cansend.send_msg(self.rsp_arb_id, rsp)
                cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x74, 0x72, 0x69, 0x63, 0x6B, 0x79, 0x5F, 0x6C, 0x65, 0x76, 0x65, 0x6C, 0x73, 0x7D], is_multiframe=True)
                client_sock.send("0x0E".encode('utf-8'))
            else:
                cansend.send_msg(self.rsp_arb_id, rsp)
        else:
            cansend.send_msg(self.rsp_arb_id, rsp)


class VCU(ECU):
        
        def __init__(self, name, req_arb_id, rsp_arb_id, verbose=False):
            super().__init__(name, req_arb_id, rsp_arb_id, verbose=False)
            self.unlocked = False
            self.seed = []
            self.stored_key = []
            
        def initialize_services(self):
            return {
                0x10: DiagnosticSessionControl(),
                0x23: ReadMemoryByAddress(),
                0x27: SecurityAccess()
                }
        
        def security_algorithm(self, rsp):
            seed = []
            for i in range(0,3):
                seed_val = random.randint(0,255)
                seed.append(seed_val)
                rsp.append(seed_val)
            if(verbose): print("generated seed", seed)
            self.seed = seed
            key = [(seed_val ^ 0xFF) for seed_val in seed]
            if (verbose): print("stored key: ", key)
            hex_key = [hex(key_byte) for key_byte in key]
            if (verbose): print("hex key: ", hex_key)
            self.stored_key = key
            return rsp

        def handle_request(self, payload, cansend):
            if (verbose): print(len(payload))    #apparently mem addr is not returnedd))
            payload_bytes = re.split(r'\s+', payload)
            dlc = payload_bytes[0]
            service_id = int(payload_bytes[1], 16)
            if (verbose): print(service_id)
            service=self.get_service(service_id)
            if service is None:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
                return
            elif service.validate_length(dlc, payload_bytes) is False:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
                return
            if isinstance(service, DiagnosticSessionControl):
                self.active_session = service.get_diagnostic_session(payload_bytes, trigger=True)
                if (verbose): print("Active session is:", self.active_session)
            rsp = service.construct_msg(payload_bytes, special_case=True, key=self.stored_key)
            if (verbose): print(rsp)
            if self.active_session == 0x02 or isinstance(service, DiagnosticSessionControl):
                if (verbose): print("worked")
                if rsp == [0x67, 0x01]:
                    if (verbose): print("security success yuh")
                    new_rsp = self.security_algorithm(rsp)
                    cansend.send_msg(self.rsp_arb_id, new_rsp)
                elif rsp == [0x67, 0x02]:
                    if (verbose): print("validated seed, successful unlock")
                    cansend.send_msg(self.rsp_arb_id, rsp)
                    cansend.send_msg(self.rsp_arb_id, [0x72, 0x65, 0x4D, 0x45, 0x4D, 0x62, 0x65, 0x72, 0x3A, 0x12, 0x09], is_multiframe=True)
                    self.unlocked = True
                elif isinstance(service, ReadMemoryByAddress):
                    if self.unlocked == True:
                        if rsp == [0x63]:
                            if (verbose): print("success yuh")
                            cansend.send_msg(self.rsp_arb_id, [rsp[0], 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x79, 0x61, 0x5F, 0x64, 0x69, 0x64, 0x5F, 0x69, 0x74, 0x5F, 0x64, 0x75, 0x64, 0x65, 0x7D], is_multiframe=True)
                            client_sock.sendall("0x04".encode('utf-8'))
                        else:
                            cansend.send_msg(self.rsp_arb_id, rsp)
                    else:
                        cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x33])

                else:
                    cansend.send_msg(self.rsp_arb_id, rsp)
            else:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x7F])


def main(verbose):
    can_handler = CAN_Handler(verbose=verbose)
    can_handler.setup()
    while True:
        threading.Thread(target=can_handler.broadcast_wiper_data, daemon=True).start()
        can_handler.recv_msg()


       # can_handler.listener()
        
if __name__ == '__main__':
    wiper_status = 0x00
    status_lock = threading.Lock()
    verbose = False

    import argparse
    try: 
        parser = argparse.ArgumentParser(description='CANQuest Backend Server')
        parser.add_argument('-v', '--verbose', action='store_true')
        
        args = parser.parse_args()
        
        if args.verbose:
            print("Verbose mode enabled")
            verbose = True



        print( "\n"
        " ██████╗ █████╗ ███╗   ██╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗ \n"
        "██╔════╝██╔══██╗████╗  ██║██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝\n"
        "██║     ███████║██╔██╗ ██║██║   ██║██║   ██║█████╗  ███████╗   ██║   \n"
        "██║     ██╔══██║██║╚██╗██║██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   \n"
        "╚██████╗██║  ██║██║ ╚████║╚██████╔╝╚██████╔╝███████╗███████║   ██║   \n"
        " ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝  \n"
        "--------------------------------------------------------------------\n"
        "Welcome to the CANQuest Backend Server v1.0!\n"
        "Have fun with your quests, but remember to be a ETHICAL hacker...\n"
        "To start, enter the IP address of your VM/device running this server.\n"
        "Then, enter that same IP address in the game interface.\n"
        "To exit the server, press Ctrl+C or Cmd+C at any time.\n"
        "--------------------------------------------------------------------\n")

        user_ip = input("Enter your IP address: ").strip()           
        try:
            ipaddress.ip_address(user_ip)
        except ValueError:
            print("Error: Invalid IP address format. Please try again.")
            exit()

        IP = user_ip
        PORT = 8080
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((IP, PORT))
            server_socket.listen(1)
            print(f"Server listening on {IP}:{PORT}")
        except Exception as e:
            print(f"Error: {e}, please restart the server.")
            exit()
        while True:
            try:
                client_sock, addr = server_socket.accept()
                print(f"Accepted connection from {addr}")
                main(verbose)
                break
            except Exception as e:
                print(f"Error: {e}")
                print("retrying...")
    except KeyboardInterrupt:
        print("\nQuest complete? We hope so...")