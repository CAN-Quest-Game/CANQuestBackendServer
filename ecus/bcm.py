'''
Filename: bcm.py
Author: CANQuest Team
Version: 1.0prod
Description: Custom Body Control Module (BCM) class used for Quest 2. Inherits from the ECU class.
'''
import time
import re
from .ecu import ECU
from services.uds_services import *
import server.config as config

class BCM(ECU):

    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=False):
        super().__init__(name, req_arb_id, rsp_arb_id, verbose=False)

    def initialize_services(self):
        return {
            0x10: DiagnosticSessionControl(),
            0x11: ECUReset(),
            }
    
    def handle_request(self, payload, cansend):
        if (self.verbose): print("BCM")
        if (self.verbose): print(len(payload))
        payload_bytes = re.split(r'\s+', payload)
        dlc = payload_bytes[0]
        service_id = int(payload_bytes[1], 16)
        if (self.verbose): print(service_id)
        service=self.get_service(service_id)
        
        if service is None:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x11])
            return
        elif service.validate_length(dlc, payload_bytes) is False:
            cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x13])
            return
        
        if isinstance(service, DiagnosticSessionControl):
            self.active_session = service.get_diagnostic_session(payload_bytes)
            if (self.verbose): print("Active session is:", self.active_session)
        rsp = service.construct_msg(payload_bytes)
        if (self.verbose): print(rsp)
        if self.active_session == 0x03:
            if rsp == [0x51, 0x03]:
                if (self.verbose): print("success yuh")
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x78])
                with config.status_lock:
                    config.wiper_status = 0x01
                if (self.verbose): print("Wipers activated")
                if config.client_sock:
                    config.client_sock.send("0x0E".encode('utf-8'))
                time.sleep(15)
                with config.status_lock:
                    config.wiper_status = 0x00
                if (self.verbose): print("Wipers off, reset complete")
                cansend.send_msg(self.rsp_arb_id, rsp)
                cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x63, 0x61, 0x6E, 0x71, 0x75, 0x65, 0x73, 0x74, 0x5F, 0x68, 0x65, 0x61, 0x64, 0x71, 0x75, 0x61, 0x72, 0x74, 0x65, 0x72, 0x73, 0x7D], is_multiframe=True)
                if config.client_sock:
                    config.client_sock.send("0x0F".encode('utf-8'))
            else:
                cansend.send_msg(self.rsp_arb_id, rsp)
        else:
            cansend.send_msg(self.rsp_arb_id, rsp)
