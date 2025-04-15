'''
Filename: ecu.py
Author: CANQuest Team
Version: 1.0prod
Description: Abstract ECU base class used for CANQuest Backend Server. This class serves as a base for specific ECU implementations (e.g., BCM, ECM, VCU). It defines the structure and methods for handling UDS services.
'''
from abc import ABC, abstractmethod
import config

class ECU(ABC):
    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=config.verbose):
        '''
        Function to initialize the ECU class.
        Arguments:
        - name: Name of the ECU.
        - req_arb_id: Request arbitration ID for the ECU.
        - rsp_arb_id: Response arbitration ID for the ECU.
        - verbose: Boolean flag to enable verbose output (default is False), taken from config.py
        '''
        self.name = name
        self.req_arb_id = req_arb_id
        self.rsp_arb_id = rsp_arb_id
        self.supported_services = self.initialize_services() #initialize services dictionary
        self.active_session = None #initialize to default session
        self.verbose=verbose
        
    def initialize_services(self):
            '''
            Helper function to initialize the services dictionary. This function should be overridden in the derived classes.
            Returns: Dictionary of supported UDS services by ECU. 
            Key: value pairs are formatted as {service_id (hex): service_object}.
            '''
            pass
    
    def get_service(self, service_id):
        '''
        Helper function to get the service object based on the service ID.
        Arguments:
        - service_id: Service ID to look up.
        Returns: Service object if found, None otherwise.
        '''
        service = self.supported_services.get(service_id)
        if not service:
            if (self.verbose): print(f"Service ID {hex(service_id)} not found.")
        return service
    
    @abstractmethod
    def handle_request(self, payload):
        ''' 
        Abstract method to handle UDS services flow based on message received by user. This method MUST be implemented in the derived classes.
        Arguments:
        - payload: Payload of the CAN message received.
        See ECM, BCM, and VCU classes for example implementation.
        '''
        pass