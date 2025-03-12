import sys
import can
import time
import config
from ecus.ecm import ECM
from ecus.bcm import BCM    
from ecus.vcu import VCU
        
class CAN_Handler:
    '''Class to handle CANbus initialization, message sending and recieving.'''
    def __init__(self, interface='socketcan', channel='vcan0', bitrate=500000, verbose=config.verbose):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus = None
        self.ecus = {}
        self._initialize_ecus()
        self.verbose = verbose

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
            if (self.verbose): print(f"Sent message: {message}")
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
                if (self.verbose): print(f"Sent message: {message}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def recv_msg(self):
        '''Recieve a message on the CANbus.'''
        try:
            message = self.bus.recv()
            if (self.verbose): print(f"Received message: {message}")
            parsed = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
            payload = ''
            for i in range(message.dlc):
          #      payload += '{0:x} '.format(message.data[i])
                payload += '{:02x} '.format(message.data[i])

            ecu = self.get_ecu(message.arbitration_id)
            if ecu:
                ecu.handle_request(payload, self)
            else:
                if (self.verbose): print("ECU not found")
            return message, payload
        
        except can.CanError:
            print("MESSAGE NOT RECEIVED")

    def shutdown(self):
        '''Close the CANbus interface.'''
        print("Shutting down CAN interface...")
        if self.bus:
            if config.client_sock:
                config.client_sock.sendall("SHUTDOWN".encode('utf-8')) 
            self.bus.shutdown()
    
    def _initialize_ecus(self):
        '''Map the arbitration ID to the corresponding ECU.'''
        ecu_dict = {
                0x123: ['ECM', 0x321], 
                0x456: ['BCM', 0x654], 
                0x789: ['VCU', 0x7FF]
                }
        for req_arb_id, (name, rsp_arb_id) in ecu_dict.items():
            if name == "ECM":
                self.ecus[req_arb_id] = ECM(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
            elif name == "BCM":
                self.ecus[req_arb_id] = BCM(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
            elif name == "VCU":
                self.ecus[req_arb_id] = VCU(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
    
    def get_ecu(self,arb_id):
        return self.ecus.get(arb_id)
    
    def broadcast_wiper_data(self):
        while not config.stop_can.is_set():
            with config.status_lock:
                stat_msg = [config.wiper_status, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            self.send_msg(0x058, stat_msg, is_status=True)
            time.sleep(0.1)