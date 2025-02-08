import can
import time
from abc import *

class UDS_Service(ABC):
    '''Abstract class for UDS services.'''
    @abstractmethod
    def __init__(self):
        self.service_id = None
        self.subfunction_id = None
        self.nrc = None
        self.diagnostic_sessions = []
        pass

    @abstractmethod
    def construct_msg(self):
        pass

    @abstractmethod
    def validate_length(self, dlc, payload):
        pass

    @abstractmethod
    def subfunction(self):
        pass

    @abstractmethod
    def positive_response(self):
        pass

    @abstractmethod
    def negative_response(self):
        pass


class DiagnosticSessionControl(UDS_Service):
    '''tbd'''
    def __init__(self):
        self.service_id = 0x10
        self.nrc = None
        self.subfunction_id = None
        
    def validate_length(self, dlc, payload):
        print("VALIDATE LENGTH", len(payload))
        if (int(dlc) != (len(payload) - 2)) or (len(payload) != 4): #TODO: change all length checks to != length lol
            return False
        else:
            return True
            
    def subfunction(self, payload, trigger_programming_session=False):
        valid_subfunctions = [0x01, 0x03]
        if trigger_programming_session:
            valid_subfunctions.append(0x02)
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False
        
    def get_diagnostic_session(self, payload, trigger=False):
        subfunc_check = self.subfunction(payload, trigger_programming_session=trigger)
        if subfunc_check:
            return self.subfunction_id
        else:
            return None

    def construct_msg(self, payload, special_case=False, key=None):
        print("DiagnosticSessionControl")
        print(payload)
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload, trigger_programming_session=special_case)
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12
            return self.negative_response()
        else:
            self.nrc = 0x22
            return self.negative_response()

    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]
    
    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class TesterPresent(UDS_Service):
    '''tbd'''
    def __init__(self):
        self.service_id = 0x3E
        self.nrc = None
        self.subfunction_id = None

    def validate_length(self, dlc, payload):
        print("VALIDATE LENGTH", len(payload))
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 4):
            return False
        else:
            return True

    def subfunction(self, payload):
        valid_subfunctions = [0x01]
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False

    def construct_msg(self, payload):
        print("TesterPresent")
        print(payload)
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload)
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12
            return self.negative_response()
        else:
            self.nrc = 0x22
            return self.negative_response()

    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]

    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class ECUReset(UDS_Service):
    '''tbd'''
    def __init__(self):
        self.service_id = 0x11
        self.nrc = None
        self.subfunction_id = None

    def validate_length(self, dlc, payload):
        print("VALIDATE LENGTH", len(payload))
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 4):
            return False
        else:
            return True

    def subfunction(self, payload):
        valid_subfunctions = [0x01, 0x03]
        #id = int(payload[0:2],16)
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False

    def construct_msg(self, payload):
        print("ECUReset")
        print(payload)
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload)
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12
            return self.negative_response()
        else:
            self.nrc = 0x22
            return self.negative_response()
    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]

    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class ReadMemoryByAddress(UDS_Service):
    '''tbd'''
    def __init__(self):
        self.service_id = 0x23
        self.nrc = None

    def validate_length(self, dlc, payload):
        print("VALIDATE LENGTH", len(payload))
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 5):
            return False
        else:
            return True

    def addressAndLengthFormatValidation(self, payload):
        '''Check if the address and length format is correct'''
        #add second nibble check for 05 - i forgot what that means lol
        #shouldn't it be 14 lol i am so confused
        #TODO add logic for mem size check
        mem_size = []
        addressAndLengthFormatIdentifier = hex(int(payload[2], 16))
        print("Address and Length Format Identifier: ", addressAndLengthFormatIdentifier)
        mem_address = payload[3:5]
        mem_size = payload[5:6]
        print("Memory Address: ", mem_address)
        print("Memory Size: ", mem_size)
        nibble1 = addressAndLengthFormatIdentifier[2]
        nibble2 = addressAndLengthFormatIdentifier[3]
        if int(nibble1) != len(mem_address) or int(nibble2) != len(mem_size):
            return False
        else:
            print("mem ok")
            return True


    def subfunction(self, payload):
        mem_address = hex(int(''.join(payload[3:5]), 16))
        print(mem_address)
        valid_mem_address_range = (0x0000, 0xFFFF)
        if valid_mem_address_range[0] <= int(mem_address, 16) <= valid_mem_address_range[1]:
            print("ok")
            return True
        else:
            return False

    def construct_msg(self, payload, special_case=True, key=None):
        print("ReadMemoryByAddress")
        print(payload)
        dlc = payload[0]
        addr_len_check = self.addressAndLengthFormatValidation(payload)
        subfunc_check = self.subfunction(payload)
        length_check = self.validate_length(dlc, payload)
        if length_check and addr_len_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13
            return self.negative_response()
        elif addr_len_check == False or addr_len_check == False:
            self.nrc = 0x31
            return self.negative_response()
        else:
            self.nrc = 0x22
            return self.negative_response()

    def positive_response(self):
        return [self.service_id+0x40]

    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class SecurityAccess(UDS_Service):
    def __init__(self):
        self.service_id = 0x27
        self.nrc = None
        self.subfunction_id = None

    def subfunction(self, payload):
        valid_subfunctions = [0x01, 0x02]
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            # if subfunction == 0x02:
            #     if self.check_key(payload, stored_key) is False:
            #         self.nrc = 0x35
            #         return False
            self.subfunction_id = subfunction
            return True
        else:
            return False
        
    def check_key(self, payload, stored_key):
        key = []
        for i in range(3,6):
            key.append(int(payload[i], 16))
        #key = int(payload[3:6], 16)
        print("CHECK KEY:", key, stored_key)
        if key == stored_key:
            return True
        else:
            return False
    
    def validate_length(self, dlc, payload):
        print("VALIDATE LENGTH", len(payload))
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 4):
            return False
        else:
            return True
        
    def construct_msg(self, payload, special_case=True, key=None):
        print("SecurityAccess")
        print(payload)
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload)
        if self.subfunction_id == 0x02:
            key_check = self.check_key(payload, stored_key=key)
            if key_check == False:
                self.nrc = 0x35
                return self.negative_response()
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13
            return self.negative_response()
        # elif key_check == False:
        #     self.nrc = 0x35
        #     return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12
            return self.negative_response()
        else:
            self.nrc = 0x22
            return self.negative_response()
        
    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]
    
    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]

    
