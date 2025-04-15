'''
Filename: can_handler.py
Author: CANQuest Team
Version: 1.0prod
Description: CAN Handler module for the CANQuest Backend Server. This module handles CAN bus initialization, message sending and receiving, and ECU management.
'''
import sys
import can
import time
import config
from ecus.ecm import ECM
from ecus.bcm import BCM    
from ecus.vcu import VCU
        
class CAN_Handler:
    '''Class to handle CANbus initialization, message sending and recieving, ECU additions. Creates instance of type can_handler.'''
    def __init__(self, interface='socketcan', channel='vcan0', bitrate=500000, verbose=config.verbose):
        '''
        Function to initialize the CAN_Handler class.
        Arguments:
        - interface: CAN interface type (default is 'socketcan').
        - channel: CAN channel (default is 'vcan0').
        - bitrate: CAN bus bitrate (default is 500000).
        - verbose: boolean flag to enable verbose output (default is False), taken from config.py
        '''
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus = None
        self.ecus = {}
        self._initialize_ecus()
        self.verbose = verbose

    def setup(self):
        '''Function to initialize the CANbus interface.'''
        try:
            print(f"Setting up CAN interface {self.channel}...")
            self.bus = can.interface.Bus(interface=self.interface, channel=self.channel, bitrate=self.bitrate)
        except OSError as e:
            print(f"Error setting up CAN interface: {e}")
            sys.exit(1)

    def send_msg(self, can_id, data, is_multiframe=False, is_extended_id=False, is_status=False):
        '''
        Function to send a standard-length message on the CANbus.
        Arguments:
        - can_id: TX arbitration CAN ID of the message.
        - data: Data to be sent in the message.
        - is_multiframe: Boolean flag to indicate if the message is a multi-frame message (default is False).
        - is_extended_id: Boolean flag to indicate if the message uses extended ID (default is False).
        - is_status: Boolean flag to indicate if the message is a status message (default is False).
        '''
        try:
            if is_multiframe is True: #if multiframe message, pass to send_multiframe_msg
                self.send_multiframe_msg(can_id, data, is_extended_id)
                return
            if is_status is True: #send status messages without DLC as regular CAN messages
                message = can.Message(arbitration_id=can_id, data=data, is_extended_id=is_extended_id)
                self.bus.send(message)
                return
            #calculate Data Length Code (DLC) for diagnostic messages and send over interface
            dlc = len(data)
            final_data = []
            final_data = [dlc] + data
            message = can.Message(arbitration_id=can_id, data=final_data, is_extended_id=is_extended_id)
            self.bus.send(message)
            if (self.verbose): print(f"Sent message: {message}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def send_multiframe_msg(self, can_id, data, is_extended_id=False):
        '''
        Function to send a multi-frame message on the CANbus.
        Arguments:
        - can_id: TX arbitration CAN ID of the message.
        - data: Data to be sent in the message.
        - is_extended_id: Boolean flag to indicate if the message uses extended ID (default is False).
        '''
        try:
            dlc = len(data)
            updated_data = [dlc] + data
            #break into frames of 7 bytes (+1 for DLC)
            frame_size = 7
            num_frames = (len(updated_data)  + (frame_size - 1)) // frame_size
            btf_sequences = [0x10, 0x21, 0x22, 0x23, 0x24, 0x25]
            for f in range(0, num_frames):
                btf = btf_sequences[f]
                frame = updated_data[f*frame_size:(f+1)*frame_size]
                final_frame = [btf] + frame
                message = can.Message(arbitration_id=can_id, data=final_frame, is_extended_id=is_extended_id)
                self.bus.send(message)
                if (self.verbose): print(f"Sent message: {message}")
        except can.CanError:
            print("MESSAGE NOT SENT")

    def recv_msg(self):
        '''Function to recieve a message on the CANbus. Actively listens through initialization.'''
        try:
            message = self.bus.recv()
            if (self.verbose): print(f"Received message: {message}")
            #parse the message and extract the payload
            parsed = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
            payload = ''
            for i in range(message.dlc):
                payload += '{:02x} '.format(message.data[i])

            #map the ecu based on the TX arbitration ID (request)
            ecu = self.get_ecu(message.arbitration_id)
            if ecu:
                ecu.handle_request(payload, self)
            else:
                if (self.verbose): print("ECU not found")
            return message, payload
        
        except can.CanError:
            print("MESSAGE NOT RECEIVED")

    def shutdown(self):
        '''Function to close the CANbus interface.'''
        print("Shutting down CAN interface...")
        if self.bus:
            if config.client_sock:
                config.client_sock.sendall("-1".encode('utf-8')) 
            self.bus.shutdown()
    
    def _initialize_ecus(self):
        '''Function to map the arbitration ID to the corresponding ECU.'''

        #TODO: add your own ECU mapping here in the key: value pair format, ECU_REQUEST_ARB_ID: [ECU_NAME, ECU_RESPONSE_ARB_ID]
        ecu_dict = {
                0x123: ['ECM', 0x321], 
                0x456: ['BCM', 0x654], 
                0x789: ['VCU', 0x7FF]
                }
        
        #TODO: add your own ECU initialization here, make sure to import custom class at the top as well
        for req_arb_id, (name, rsp_arb_id) in ecu_dict.items():
            if name == "ECM":
                self.ecus[req_arb_id] = ECM(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
            elif name == "BCM":
                self.ecus[req_arb_id] = BCM(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
            elif name == "VCU":
                self.ecus[req_arb_id] = VCU(name, req_arb_id, rsp_arb_id, verbose=config.verbose)
    
    def get_ecu(self,arb_id):
        '''Helper function to return request arbitration ID of the ECU.'''
        return self.ecus.get(arb_id)
    
    def broadcast_wiper_data(self):
        '''Function to broadcast wiper data on the CANbus. This function runs in a separate thread. Can disable if desired.'''
        while not config.stop_can.is_set():
            with config.status_lock:
                stat_msg = [config.wiper_status, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            self.send_msg(0x058, stat_msg, is_status=True)
            time.sleep(0.1)