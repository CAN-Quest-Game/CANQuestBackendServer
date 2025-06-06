'''
Filename: uds_services.py
Author: CANQuest Team
Version: 1.0prod
Description: Abstract UDS service class used for CANQuest Backend Server. Followed by concrete implementations of UDS services for BCM, ECM, and VCU. Can add more services as needed.
These classes define the structure and methods for handling UDS services such as Diagnostic Session Control, Tester Present, ECU Reset, Read Memory By Address, and Security Access.
Refer to ISO 14229-1 for UDS protocol details and help with implementation.
'''
from abc import *

class UDS_Service(ABC):
    '''Abstract base class for all UDS services.'''

    @abstractmethod
    def __init__(self):
        '''
        Function to initialize the UDS_Service class.
        '''
        self.service_id = None
        self.subfunction_id = None
        self.nrc = None #nrc = negative response code
        self.diagnostic_sessions = []
        pass

    @abstractmethod
    def construct_msg(self):
        '''
        Abstract method to construct the final response message payload. This method MUST be implemented in the derived classes.
        '''
        pass

    @abstractmethod
    def validate_length(self, dlc, payload):
        '''
        Abstract method to validate the length of the payload. This method MUST be implemented in the derived classes.
        Arguments:
        - dlc: Data Length Code of the message.
        - payload: Payload of the received CAN message.
        '''
        pass

    @abstractmethod
    def subfunction(self):
        '''
        Abstract method to check the subfunction validity of the UDS service. This method MUST be implemented in the derived classes.
        '''
        pass

    @abstractmethod
    def positive_response(self):
        '''
        Abstract method to construct the positive response message. This method MUST be implemented in the derived classes.
        '''
        pass

    @abstractmethod
    def negative_response(self):
        '''
        Abstract method to construct the negative response message. This method MUST be implemented in the derived classes.
        '''
        pass


class DiagnosticSessionControl(UDS_Service):
    '''Concrete implementation of the UDS service for Diagnostic Session Control.'''
    def __init__(self):
        self.service_id = 0x10
        self.nrc = None
        self.subfunction_id = None
        
    def validate_length(self, dlc, payload):
        if (int(dlc) != (len(payload) - 2)) or (len(payload) != 4): #TODO: change all length checks to != length lol
            return False
        else:
            return True
            
    def subfunction(self, payload, trigger_programming_session=False):
        valid_subfunctions = [0x01, 0x03] #default session and extended diagnostic session
        if trigger_programming_session: #able to dynamically trigger if programming session is supported
            valid_subfunctions.append(0x02)
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False
        
    def get_diagnostic_session(self, payload, trigger=False):
        '''Special function for Diagnostic Session Control to check if the session is valid and return the session ID.'''
        subfunc_check = self.subfunction(payload, trigger_programming_session=trigger)
        if subfunc_check:
            return self.subfunction_id
        else:
            return None

    def construct_msg(self, payload, special_case=False, key=None):
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload, trigger_programming_session=special_case)
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13 #Invalid length or format
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12 #Subfunction not supported
            return self.negative_response()
        else:
            self.nrc = 0x22 #Conditions not correct otherwise
            return self.negative_response()

    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]
    
    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class TesterPresent(UDS_Service):
    '''Concrete implementation of the UDS service for Tester Present.'''
    def __init__(self):
        self.service_id = 0x3E
        self.nrc = None
        self.subfunction_id = None

    def validate_length(self, dlc, payload):
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 4):
            return False
        else:
            return True

    def subfunction(self, payload):
        valid_subfunctions = [0x01] #subfunction 0x01 standard to support
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False

    def construct_msg(self, payload):
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload)
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13 #Invalid length or format
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12 #Subfunction not supported
            return self.negative_response()
        else:
            self.nrc = 0x22 #Conditions not correct otherwise
            return self.negative_response()

    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]

    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class ECUReset(UDS_Service):
    '''Concrete implementation of the UDS service for ECU Reset.'''
    def __init__(self):
        self.service_id = 0x11
        self.nrc = None
        self.subfunction_id = None

    def validate_length(self, dlc, payload):
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 4):
            return False
        else:
            return True

    def subfunction(self, payload):
        valid_subfunctions = [0x01, 0x03] #hard reset and soft reset allowed
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False

    def construct_msg(self, payload):
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload)
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13 #Invalid length or format
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12 #Subfunction not supported
            return self.negative_response()
        else:
            self.nrc = 0x22 #Conditions not correct otherwise
            return self.negative_response()
    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]

    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]
    
class ReadMemoryByAddress(UDS_Service):
    '''Concrete implementation of the UDS service for Read Memory By Address.'''
    def __init__(self):
        self.service_id = 0x23
        self.nrc = None

    def validate_length(self, dlc, payload):
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 5):
            return False
        else:
            return True

    def addressAndLengthFormatValidation(self, payload):
        '''Check if the address and length format is correct. Check ISO 14229-1 for details, not 100% sure if this is correct implementation.'''
        #add second nibble check for 05 - i forgot what that means lol
        #shouldn't it be 14 lol i am so confused
        #TODO add logic for mem size check
        mem_size = []
        addressAndLengthFormatIdentifier = hex(int(payload[2], 16))
        mem_address = payload[3:5]
        mem_size = payload[5:6]
        nibble1 = addressAndLengthFormatIdentifier[2]
        nibble2 = addressAndLengthFormatIdentifier[3]
        if int(nibble1) != len(mem_address) or int(nibble2) != len(mem_size):
            return False
        else:
            return True

    def subfunction(self, payload):
        mem_address = hex(int(''.join(payload[3:5]), 16)) #parse the address
        valid_mem_address_range = (0x0000, 0xFFFF) #check if address is in range
        if valid_mem_address_range[0] <= int(mem_address, 16) <= valid_mem_address_range[1]:
            return True
        else:
            return False

    def construct_msg(self, payload, special_case=True, key=None):
        dlc = payload[0]
        addr_len_check = self.addressAndLengthFormatValidation(payload)
        subfunc_check = self.subfunction(payload)
        length_check = self.validate_length(dlc, payload)
        if length_check and addr_len_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13 #Invalid length or format
            return self.negative_response()
        elif addr_len_check == False or addr_len_check == False:
            self.nrc = 0x31 #Request out of range specific for mem address
            return self.negative_response()
        else:
            self.nrc = 0x22 #Conditions not correct otherwise
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
        valid_subfunctions = [0x01, 0x02] #request seed and send key at only level 1,2 pair
        subfunction = int(payload[2], 16)
        if subfunction in valid_subfunctions:
            self.subfunction_id = subfunction
            return True
        else:
            return False
        
    def check_key(self, payload, stored_key):
        '''Checking if key entered by user matches key calculated by ECU server...'''
        key = []
        for i in range(3,6):
            key.append(int(payload[i], 16))
        if key == stored_key:
            return True
        else:
            return False
    
    def validate_length(self, dlc, payload):
        if (int(dlc) != (len(payload) - 2)) or (len(payload) < 4):
            return False
        else:
            return True
        
    def construct_msg(self, payload, special_case=True, key=None):
        dlc = payload[0]
        length_check = self.validate_length(dlc, payload)
        subfunc_check = self.subfunction(payload)
        if self.subfunction_id == 0x02:
            key_check = self.check_key(payload, stored_key=key)
            if key_check == False:
                self.nrc = 0x35 #invalid key
                #TODO: implement 0x36 to protect against brute force, if you're feeling evil
                return self.negative_response()
        if length_check and subfunc_check:
            response = self.positive_response()
            return response
        elif length_check == False:
            self.nrc = 0x13 #Invalid length or format
            return self.negative_response()
        elif subfunc_check == False:
            self.nrc = 0x12 #Subfunction not supported
            return self.negative_response()
        else:
            self.nrc = 0x22 #Conditions not correct otherwise
            return self.negative_response()
        
    def positive_response(self):
        return [self.service_id+0x40, self.subfunction_id]
    
    def negative_response(self):
        return [0x7F, self.service_id, self.nrc]

    
