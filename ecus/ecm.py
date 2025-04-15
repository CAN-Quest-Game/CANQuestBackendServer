'''
Filename: ecm.py
Author: CANQuest Team
Version: 1.0prod
Description: Custom Engine Control Module (ECM) class used for Quest 1. Inherits from the ECU class.
'''
import re
from .ecu import ECU
from services.uds_services import *
import config

class ECM(ECU):

    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=config.verbose):
        super().__init__(name, req_arb_id, rsp_arb_id, verbose=config.verbose)

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
        if self.active_session == 0x01:
            if rsp == [0x7E, 0x01]:
                if(verbose): print("success yuh")
                cansend.send_msg(self.rsp_arb_id, rsp)
                cansend.send_msg(self.rsp_arb_id, [0x66, 0x6C, 0x61, 0x67, 0x7B, 0x75, 0x6D, 0x5F, 0x64, 0x65, 0x61, 0x72, 0x62, 0x6F, 0x72, 0x6E, 0x7D], is_multiframe=True)
                if config.client_sock:
                    config.client_sock.sendall("0x00".encode('utf-8'))
            else:
                cansend.send_msg(self.rsp_arb_id, rsp)
        else:
            cansend.send_msg(self.rsp_arb_id, rsp)