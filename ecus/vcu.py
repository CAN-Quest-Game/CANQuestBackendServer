'''
Filename: vcu.py
Author: CANQuest Team
Version: 1.0prod
Description: Custom Vehicle Cockpit Unit (VCU) class used for Quest 3. Inherits from the ECU class.
'''
import random
import re
from .ecu import ECU
from services.uds_services import *
import server.config as config

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
            if(self.verbose): print("generated seed", seed)
            self.seed = seed
            key = [(seed_val ^ 0xFF) for seed_val in seed]
            if (self.verbose): print("stored key: ", key)
            hex_key = [hex(key_byte) for key_byte in key]
            if (self.verbose): print("hex key: ", hex_key)
            self.stored_key = key
            return rsp

        def handle_request(self, payload, cansend):
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
                self.active_session = service.get_diagnostic_session(payload_bytes, trigger=True)
                if (self.verbose): print("Active session is:", self.active_session)
            rsp = service.construct_msg(payload_bytes, special_case=True, key=self.stored_key)
            if (self.verbose): print(rsp)
            if self.active_session == 0x02 or isinstance(service, DiagnosticSessionControl):
                if (self.verbose): print("worked")
                if rsp == [0x67, 0x01]:
                    if (self.verbose): print("security success yuh")
                    new_rsp = self.security_algorithm(rsp)
                    cansend.send_msg(self.rsp_arb_id, new_rsp)
                elif rsp == [0x67, 0x02]:
                    if (self.verbose): print("validated seed, successful unlock")
                    cansend.send_msg(self.rsp_arb_id, rsp)
                    cansend.send_msg(self.rsp_arb_id, [0x72, 0x65, 0x4D, 0x45, 0x4D, 0x62, 0x65, 0x72, 0x3A, 0x12, 0x09], is_multiframe=True)
                    self.unlocked = True
                elif isinstance(service, ReadMemoryByAddress):
                    if self.unlocked == True:
                        if rsp == [0x63]:
                            if (self.verbose): print("success yuh")
                            cansend.send_msg(self.rsp_arb_id, [rsp[0], 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x79, 0x61, 0x5F, 0x64, 0x69, 0x64, 0x5F, 0x69, 0x74, 0x5F, 0x64, 0x75, 0x64, 0x65, 0x7D], is_multiframe=True)
                            if config.client_sock:
                                config.client_sock.sendall("0x04".encode('utf-8'))
                        else:
                            cansend.send_msg(self.rsp_arb_id, rsp)
                    else:
                        cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x33])

                else:
                    cansend.send_msg(self.rsp_arb_id, rsp)
            else:
                cansend.send_msg(self.rsp_arb_id, [0x7F, service_id, 0x7F])
