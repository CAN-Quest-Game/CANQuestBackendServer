import sys
import can
import time
import random
import socket
import re
from abc import ABC, abstractmethod
import uds_services
from uds_services import *

class CAN_Handler:
    '''Class to handle CANbus initialization, message sending and recieving.'''
    def __init__(self, interface='socketcan', channel='vcan0', bitrate=500000):
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

    def send_msg(self, can_id, data, is_multiframe=False, is_extended_id=False):
        '''Send a message on the CANbus.'''
        try:
            if is_multiframe is True:
                self.send_multiframe_msg(can_id, data, is_extended_id)
                return
            dlc = len(data)
            final_data = []
            final_data = [dlc] + data
            message = can.Message(arbitration_id=can_id, data=final_data, is_extended_id=is_extended_id)
            self.bus.send(message)
            print(f"Sent message: {message}")
            #if (verbose): print(f"Message sent on {bus.channel_info}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def send_multiframe_msg(self, can_id, data, is_extended_id=False):
        '''Send a multi-frame message on the CANbus.'''
        try:
            dlc = len(data)
            updated_data = [dlc] + data
            print("Updated data:", updated_data)
            print(len(updated_data))
            frame_size = 7
            num_frames = (len(updated_data)  + (frame_size - 1)) // frame_size
            print(num_frames)
            btf_sequences = [0x10, 0x21, 0x22, 0x23, 0x24, 0x25]
            for f in range(0, num_frames):
                btf = btf_sequences[f]
                frame = updated_data[f*frame_size:(f+1)*frame_size]
                final_frame = [btf] + frame
                print([hex(x) for x in final_frame])
                message = can.Message(arbitration_id=can_id, data=final_frame, is_extended_id=is_extended_id)
                self.bus.send(message)
                print(f"Sent message: {message}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def recv_msg(self):
        '''Recieve a message on the CANbus.'''
        try:
            message = self.bus.recv()
            print(f"Received message: {message}")
            parsed = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
            payload = ''
            for i in range(message.dlc):
          #      payload += '{0:x} '.format(message.data[i])
                payload += '{:02x} '.format(message.data[i])

            ecu = self.get_ecu(message.arbitration_id)
            if ecu:
                ecu.handle_request(payload, self)
            else:
                print("ECU not found")
            return message, payload
                  #while True:
            s=''
            for i in range(message.dlc ):
                s +=  '{:02x} '.format(message.data[i])
            #print(' {}'.format(c+s))
            return message, s
        
        except KeyboardInterrupt:
            print('\n\rRecv Msg Keyboard interrupt')
            self.shutdown()
            exit(0)
    
    def _initialize_ecus(self):
        '''Map the arbitration ID to the corresponding ECU.'''
        ecu_dict = {
                0x123: ['ECM', 0x321], 
                0x456: ['BCM', 0x654], 
                0x789: ['VCU', 0x7FF]
                }
        for req_arb_id, (name, rsp_arb_id) in ecu_dict.items():
            if name == "ECM":
                self.ecus[req_arb_id] = ECM(name, req_arb_id, rsp_arb_id)
            elif name == "BCM":
                self.ecus[req_arb_id] = BCM(name, req_arb_id, rsp_arb_id)
            elif name == "VCU":
                self.ecus[req_arb_id] = VCU(name, req_arb_id, rsp_arb_id)
    
    def get_ecu(self,arb_id):
        return self.ecus.get(arb_id)
    
class ECU(ABC):
    def __init__(self, name, req_arb_id, rsp_arb_id):
        self.name = name
        self.req_arb_id = req_arb_id
        self.rsp_arb_id = rsp_arb_id
        self.supported_services = self.initialize_services()
        self.active_session = None #initialize to default session

    #TODO:add self.security_level checks
    #add self.session checks
        
    def initialize_services(self):
            pass
        #     return {
        #     0x10: DiagnosticSessionControl(),
        #     0x11: ECUReset(),
        #     # 0x27: 'SecurityAccess',  # TODO: Implement SecurityAccess
        #     # 0x28: 'CommunicationControl',
        #     0x3E: TesterPresent(),
        #     # 0x22: 'ReadDataByIdentifier',
        #     0x23: ReadMemoryByAddress(),
        #     # 0x2E: 'WriteDataByIdentifier',
        #     # 0x2F: 'InputOutputControlByIdentifier',
        #     # 0x31: 'RoutineControl',
        #     # 0x34: 'RequestDownload',
        #     # 0x35: 'RequestUpload',
        #     # 0x36: 'TransferData',
        #     # 0x37: 'RequestTransferExit'
        # }
    
    def get_service(self, service_id):
        service = self.supported_services.get(service_id)
        if not service:
            print(f"Service ID {hex(service_id)} not found.")
        return service
    
    @abstractmethod
    def handle_request(self, payload):
        pass

class ECM(ECU):
    def __init__(self, name, req_arb_id, rsp_arb_id):
        super().__init__(name, req_arb_id, rsp_arb_id)

    def initialize_services(self):
        return {
            0x10: DiagnosticSessionControl(),
            0x3E: TesterPresent()
        }

    def handle_request(self, payload, cansend):
        print(len(payload))
        payload_bytes = re.split(r'\s+', payload)
        dlc = payload_bytes[0]
        service_id = int(payload_bytes[1], 16)
        print(service_id)
        service=self.get_service(service_id)
        
        if service is None:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
            return
        elif service.validate_length(dlc, payload_bytes) is False:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
            return

        
        if isinstance(service, DiagnosticSessionControl):
            self.active_session = service.get_diagnostic_session(payload_bytes)
            print("Active session is:", self.active_session)
        rsp = service.construct_msg(payload_bytes)
        print(rsp)
        if self.active_session == 0x01: #maybe not the best way to do this
            if rsp == [0x7E, 0x01]:
                print("success yuh")
                cansend.send_msg(self.rsp_arb_id, rsp)
                cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x62, 0x6C, 0x61, 0x73, 0x74, 0x6F, 0x66, 0x66, 0x7D], is_multiframe=True)
            else:
                cansend.send_msg(self.rsp_arb_id, rsp)
        else:
            cansend.send_msg(self.rsp_arb_id, rsp)

class BCM(ECU):
    def __init__(self, name, req_arb_id, rsp_arb_id):
        super().__init__(name, req_arb_id, rsp_arb_id)

    def initialize_services(self):
        return {
            0x10: DiagnosticSessionControl(),
            0x11: ECUReset(),
            }

    def handle_request(self, payload, cansend):
        print("BCM")
        print(len(payload))
        payload_bytes = re.split(r'\s+', payload)
        dlc = payload_bytes[0]
        service_id = int(payload_bytes[1], 16)
        print(service_id)
        service=self.get_service(service_id)
        
        if service is None:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
            return
        elif service.validate_length(dlc, payload_bytes) is False:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
            return
        
        if isinstance(service, DiagnosticSessionControl):
            self.active_session = service.get_diagnostic_session(payload_bytes)
            print("Active session is:", self.active_session)
        rsp = service.construct_msg(payload_bytes)
        print(rsp)
        if self.active_session == 0x03:
            if rsp == [0x51, 0x03]:
                print("success yuh")
                cansend.send_msg(self.rsp_arb_id, rsp)
                cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x74, 0x72, 0x69, 0x63, 0x6B, 0x79, 0x5F, 0x6C, 0x65, 0x76, 0x65, 0x6C, 0x73, 0x7D], is_multiframe=True)
            else:
                cansend.send_msg(self.rsp_arb_id, rsp)
        else:
            cansend.send_msg(self.rsp_arb_id, rsp)


class VCU(ECU):
        
        def __init__(self, name, req_arb_id, rsp_arb_id):
            super().__init__(name, req_arb_id, rsp_arb_id)
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
            print("generated seed", seed)
            self.seed = seed
            key = [(seed_val ^ 0xFF) for seed_val in seed]
            print("stored key: ", key)
            hex_key = [hex(key_byte) for key_byte in key]
            print("hex key: ", hex_key)
            self.stored_key = key
            return rsp
        
        # def key_from_seed(self, rsp):
        #     key = [(seed_val ^ 0xFF) for seed_val in self.seed]
        #     print("calculated key: ", key)
        #     self.stored_key = key
        #     rsp.append(key)
        #     return rsp
        # TODO: add implementation that once unlocked and tried to request seed again, add request sequence error!
        

        def handle_request(self, payload, cansend):
            print(len(payload))    #apparently mem addr is not returnedd))
            payload_bytes = re.split(r'\s+', payload)
            dlc = payload_bytes[0]
            service_id = int(payload_bytes[1], 16)
            print(service_id)
            service=self.get_service(service_id)
            if service is None:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
                return
            elif service.validate_length(dlc, payload_bytes) is False:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
                return
            if isinstance(service, DiagnosticSessionControl):
                self.active_session = service.get_diagnostic_session(payload_bytes, trigger=True)
                print("Active session is:", self.active_session)
            rsp = service.construct_msg(payload_bytes, special_case=True, key=self.stored_key)
            print(rsp)
            if self.active_session == 0x02 or isinstance(service, DiagnosticSessionControl):
                print("worked")
                if rsp == [0x67, 0x01]:
                    print("security success yuh")
                    new_rsp = self.security_algorithm(rsp)
                    cansend.send_msg(self.rsp_arb_id, new_rsp)
                elif rsp == [0x67, 0x02]:
                    print("validated seed, successful unlock")
                    cansend.send_msg(self.rsp_arb_id, rsp)
                    cansend.send_msg(self.rsp_arb_id, [0x72, 0x65, 0x4D, 0x45, 0x4D, 0x62, 0x65, 0x72, 0x3A, 0x12, 0x09], is_multiframe=True)
                    self.unlocked = True
                elif isinstance(service, ReadMemoryByAddress):
                    if self.unlocked == True:
                        if rsp == [0x63]:
                            print("success yuh")
                            cansend.send_msg(self.rsp_arb_id, [rsp[0], 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x79, 0x61, 0x5F, 0x64, 0x69, 0x64, 0x5F, 0x69, 0x74, 0x5F, 0x64, 0x75, 0x64, 0x65, 0x7D], is_multiframe=True)
                        else:
                            cansend.send_msg(self.rsp_arb_id, rsp)
                    else:
                        cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x33])

                else:
                    cansend.send_msg(self.rsp_arb_id, rsp)
                #change logic here soon please! (use self.unlocked)
                #if self.unlocked:
            # elif isinstance(service, ReadMemoryByAddress):
            #     if self.unlocked == True:
            #         if rsp == [0x63]:
            #             print("success yuh")
            #             cansend.send_msg(self.rsp_arb_id, [rsp[0], 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x79, 0x61, 0x5F, 0x64, 0x69, 0x64, 0x5F, 0x69, 0x74, 0x5F, 0x64, 0x75, 0x64, 0x65, 0x7D], is_multiframe=True)
            #     # elif rsp == [0x63]:
            #     #     print("success yuh")
            #     #     cansend.send_msg(self.rsp_arb_id, [rsp[0], 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x79, 0x61, 0x5F, 0x64, 0x69, 0x64, 0x5F, 0x69, 0x74, 0x5F, 0x64, 0x75, 0x64, 0x65, 0x7D], is_multiframe=True)
            #     else:
            #         cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x33])
            else:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x7F])




def main():
    can_handler = CAN_Handler()
    can_handler.setup()
    while True:
        x, returned= can_handler.recv_msg()

        print("PRINTING")
        print(x)
        print(returned)
        #payload = data[3:3+pkt_len*3]

        
        
if __name__ == '__main__':
    main()