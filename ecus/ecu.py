from abc import ABC, abstractmethod
import config

class ECU(ABC):
    def __init__(self, name, req_arb_id, rsp_arb_id, verbose=config.verbose):
        self.name = name
        self.req_arb_id = req_arb_id
        self.rsp_arb_id = rsp_arb_id
        self.supported_services = self.initialize_services()
        self.active_session = None #initialize to default session
        self.verbose=verbose

    #TODO:add self.security_level checks
    #add self.session checks
        
    def initialize_services(self):
            pass
    
    def get_service(self, service_id):
        service = self.supported_services.get(service_id)
        if not service:
            if (self.verbose): print(f"Service ID {hex(service_id)} not found.")
        return service
    
    @abstractmethod
    def handle_request(self, payload):
        pass