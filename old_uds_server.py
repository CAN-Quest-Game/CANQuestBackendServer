#!/usr/bin/python
#!/usr/bin/env python3


import sys
import can
import time
import random
import socket

IP = '127.0.0.1'
PORT = 5001

VIN = "1FMCU9C74AKB96069"
clean, longdata = range(2)
bus = can.Bus()
can_id = ""
verbose = 0
session = 1
security_access = 0
attempts = 0
key = None



services = {	
		0x10: "DiagnosticSessionControl",
		0x11: "ECUReset",
		0x27: "SecurityAccess",
		0x28: "CommunicationControl",
		0x3e: "TesterPresent",
		0x83: "AccessTimingParameter",
		0x84: "SecuredDataTransmission",
		0x85: "ControlDTCSetting",
		0x86: "ResponseOnEvent",
		0x87: "LinkControl",
		0x22: "ReadDataByIdentifier",
		0x23: "ReadMemoryByAddress",
		0x24: "ReadScalingDataByIdentifier",
		0x2a: "ReadDataByPeriodicIdentifier",
		0x2c: "DynamicallyDefineDataIdentifier",
		0x2e: "WriteDataByIdentifier",
		0x3d: "WriteMemoryByAddress",
		0x14: "ClearDiagnosticInformation",
		0x19: "ReadDTCInformation",
		0x2f: "InputOutputControlByIdentifier",
		0x31: "RoutineControl",
		0x34: "RequestDownload",
		0x35: "RequestUpload",
		0x36: "TransferData",
		0x21: "readDataByLocalIdentifier",
		0x3b: "writeDataByLocalIdentifier",
		0x37: "RequestTransferExit",
		0x18: "readDiagnosticTroubleCodesByStatus"}

def get_id_string(id):
	prefix = ""
	if (0x10 <= id and id <= 0x3e) or (0x80 <= id and id <= 0xbe):
		prefix = "Request_"
	if (0x50 <= id and id <= 0x7e) or (0xc0 <= id and id <= 0xfe):
		prefix = "PosResponse_"
		id -= 0x40
	if id == 0x7f:
		return "NegResponse"	
	if id in services:
		id_s = prefix + services[id]
		if (verbose): print (id_s)
	else:
		id_s = prefix + "UNKNOWN_%02x" % id
	return id_s

def handle_data(payload, pkt_len):
	global security_access, session, key, attempts
	if len(payload) < 2: return	
	id = int(payload[0:2],16)
	id_s = get_id_string(id)
	if can_id == 0x123:
		#Parking Assist Module reply to 0x73E
		print ("ECM Module")
		if id == 0x3E:
			if (verbose): print ("Tester Present")
			security_access = 0					
			if len(payload) < 2:
				send_msg(0x321, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			pid = int(payload[3:5],16)
			if pid == 0x01:
				session = 1			
				send_msg(0x321, [0x02, id+0x40, pid]) 
				send_msg(0x321, [0x10, 0x21, 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x62]) 
				send_msg(0x321, [0x21, 0x6C, 0x61, 0x73, 0x74, 0x6F, 0x66, 0x66])
				send_msg(0x321, [0x22, 0x7D])
				client_sock.sendall(b"START CAR!!!!!!!!!!!!!!")

			else:
				session = 1
				send_msg(0x321, [0x03, 0x7F, id, 0x11]) #subfunctionNotSupported		



	elif can_id == 0x456:
		#Chassis Computer SJB module reply to 0x72E
		print ("BCM module")
	elif can_id == 0x789:
		#PowerTrain Control Module reply to 0x7E8
		print ("BSCM Module")
		if id == 0x09:	# Request Vehicle Information
			print ("Request Vehicle Information")		
			if len(payload) < 6:
				send_msg(0x7E8, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat
				return
			pid = int(payload[3:5],16)
			if pid == 0x00:
				print ("Replying with ALL Pids supported.")
				send_msg(0x7E8, [0x06, id+0x40, 0x00, 0x55, 0x00, 0x00, 0x00])
			elif pid == 0x02:
				print ("Sending VIN")
				send_msg(0x7E8, [0x10, id+0x40, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00])
				print(VIN)

		elif id == 0x10:
			if (verbose): print ("Diagnostics access")
			security_access = 0					
			if len(payload) < 6:
				send_msg(0x7E8, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			pid = int(payload[3:5],16)
			if pid == 0x01:
				session = 1			
				send_msg(0x7E8, [0x02, id+0x40, pid]) 
			elif pid == 0x02:				
				session = 2
				send_msg(0x7E8, [0x02, id+0x40, pid]) 
			else:
				session = 1
				send_msg(0x7E8, [0x03, 0x7F, id, 0x11]) #subfunctionNotSupported		

		elif id == 0x23:
			if (verbose): print ("Read Memory by Address")
			print ("Read Memory by Address")
			print (len(payload))
			if len(payload) < 6:
				send_msg(0x7E8, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			
			if session != 2:				#if not in session 2 repond with serviceNotSupportedInActiveSession 03 7f 23 7f
				send_msg(0x7E8, [0x03, 0x7F, id, 0x7f]) #serviceNotSupportedInActiveSession
				return
			
			pid = int(payload[3:5],16)			
			if pid == 0x21: #2-byte address 1-byte length
				
				if security_access != 1: #if security access is not 1 respond with securityAccessDenied 03 7f 23 33
					send_msg(0x7E8, [0x03, 0x7F, id, 0x33]) #securityAccessDenied
					return
				if len(payload) < 15:
					send_msg(0x7E8, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat
					return
				print (payload)
				address = payload[6:8] + payload[9:11]
				length = payload[12:14]
				address = int(address, 16)
				length = int(length, 16)
				#The memory region starts at 0x1000 and ends at 0x1EC0, length of firmware is 3776 in decimal
				if address < 0x1000 or (address+length)>0x1EC0:
					send_msg(0x7E8, [0x03, 0x7F, id, 0x31]) #requestOutOfRange
					return			
				memory_address = address - 0x1000
				f = open('fw.bin', 'rb')
				f.seek(memory_address)
				memory_read = f.read(1) #accepting just 1-byte for purposes of this training only, future versions should support a ISO-TP response for more bytes.
				memory_read = memory_read[0]
				send_msg(0x7E8, [0x02, id+0x40, memory_read]) #positive response with 1-byte of memory data	
			
			else:
				send_msg(0x7E8, [0x03, 0x7F, id, 0x13]) #requestOutOfRange only accepting 2-byte address and 1-byte length


		elif id == 0x27:
			if (verbose): print ("Security access")
			if (session < 2):
				send_msg(0x7E8, [0x03, 0x7F, id, 0x7F]) #serviceNotSupportedInActiveSession		
				print ("serviceNotSupportedInActiveSession")
				return				
			if len(payload) < 6:
				send_msg(0x7E8, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			pid = int(payload[3:5],16)
			if pid == 0x01:
				if (verbose): print ("Sending seed")
				#generate random seed
				s1 = random.randint(0,255)				
				s2 = random.randint(0,255)
				s3 = random.randint(0,255)
				send_msg(0x7E8, [0x05, id+0x40, 0x01, s1, s2, s3])
				key = key_from_seed([s1, s2, s3])
				print (key)
				attempts = 0
			if pid == 0x02:
				if (verbose): print ("verifying key")

				if len(payload) < 15:
					send_msg(0x7E8, [0x03, 0x7F, id, 0x22])
					return				
				if attempts > 5:
					send_msg(0x7E8, [0x03, 0x7F, id, 0x36])
					security_access = 0
					session = 1
					return
				
				key_received = [int(payload[6:8],16), int(payload[9:11],16), int(payload[12:14],16)]
				print (key_received)
				if (key_received == key):
					send_msg(0x7E8, [0x02, id+0x40, 0x02])
					security_access = 1
					print ("Success")
				else:
					send_msg(0x7E8, [0x03, 0x7F, id, 0x35])					
					attempts += 1


	else:
		pass
		#unknown module


	#print ( id_s )
	

def setup_can(interface):
	global bus
	try:
		print("Bring up %s...." % (interface))
		#os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
		time.sleep(0.1)
		bus = can.interface.Bus(interface='socketcan', channel=interface, bitrate=500000)
        #bus = can.interface.Bus(interface='socketcan', channel='vcan0', bitrate=500000)
        #bus = can.interface.Bus(interface='socketcan', channel='can0', bitrate=500000)
        # bus = can.Bus(interface='socketcan', channel='vcan0', bitrate=250000)
        # bus = can.Bus(interface='pcan', channel='PCAN_USBBUS1', bitrate=250000)
        # bus = can.Bus(interface='ixxat', channel=0, bitrate=250000)
        # bus = can.Bus(interface='vector', app_name='CANalyzer', channel=0, bitrate=250000)
	
	except OSError:
		print("Cannot find %s interface." % (interface))
		exit()

	print('Ready')


def send_msg(arb_id, data, is_extended=False):
	try:
		msg = can.Message(arbitration_id=arb_id, data=data, is_extended_id= is_extended)
		bus.send(msg)
		if (verbose): print(f"Message sent on {bus.channel_info}")
	except can.CanError:
		print("Message NOT sent")

def recv_msg():
	try:
        #while True:
		message = bus.recv()    # Wait until a message is received.
		c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
		s=''
		for i in range(message.dlc ):
			s +=  '{:02x} '.format(message.data[i])
		#print(' {}'.format(c+s))
		return message, s
	except KeyboardInterrupt:
        #Catch keyboard interrupt
        #os.system("sudo /sbin/ip link set can0 down")
		print('\n\rRecv Msg Keyboard interrupt')
		bus.shutdown()
		exit(0)

def key_from_seed(seed):
    secret = "5B 41 74 65 7D"
    s1 = int(secret[0:2],16)
    s2 = int(secret[3:5],16)
    s3 = int(secret[6:8],16)
    s4 = int(secret[9:11],16)
    s5 = int(secret[12:14],16)
    seed_int = (seed[0]<<16) + (seed[1]<<8) + (seed[2]) 
    or_ed_seed = ((seed_int & 0xFF0000) >> 16) | (seed_int & 0xFF00) | (s1 << 24) | (seed_int & 0xff) << 16
    mucked_value = 0xc541a9

    for i in range(0,32):
        a_bit = ((or_ed_seed >> i) & 1 ^ mucked_value & 1) << 23
        v9 = v10 = v8 = a_bit | (mucked_value >> 1)
        mucked_value = v10 & 0xEF6FD7 | ((((v9 & 0x100000) >> 20) ^ ((v8 & 0x800000) >> 23)) << 20) | (((((mucked_value >> 1) & 0x8000) >> 15) ^ ((v8 & 0x800000) >> 23)) << 15) | (((((mucked_value >> 1) & 0x1000) >> 12) ^ ((v8 & 0x800000) >> 23)) << 12) | 32 * ((((mucked_value >> 1) & 0x20) >> 5) ^ ((v8 & 0x800000) >> 23)) | 8 * ((((mucked_value >> 1) & 8) >> 3) ^ ((v8 & 0x800000) >> 23))

    for j in range(0,32):
        a_bit = ((((s5 << 24) | (s4 << 16) | s2 | (s3 << 8)) >> j) & 1 ^ mucked_value & 1) << 23
        v14 = v13 = v12 = a_bit | (mucked_value >> 1)
        mucked_value = v14 & 0xEF6FD7 | ((((v13 & 0x100000) >> 20) ^ ((v12 & 0x800000) >> 23)) << 20) | (((((mucked_value >> 1) & 0x8000) >> 15) ^ ((v12 & 0x800000) >> 23)) << 15) | (((((mucked_value >> 1) & 0x1000) >> 12) ^ ((v12 & 0x800000) >> 23)) << 12) | 32 * ((((mucked_value >> 1) & 0x20) >> 5) ^ ((v12 & 0x800000) >> 23)) | 8 * ((((mucked_value >> 1) & 8) >> 3) ^ ((v12 & 0x800000) >> 23))

    key = ((mucked_value & 0xF0000) >> 16) | 16 * (mucked_value & 0xF) | ((((mucked_value & 0xF00000) >> 20) | ((mucked_value & 0xF000) >> 8)) << 8) | ((mucked_value & 0xFF0) >> 4 << 16)
#    return "%02X %02X %02X" % ( (key & 0xff0000) >> 16, (key & 0xff00) >> 8, key & 0xff) 
    return [(key & 0xff0000) >> 16, (key & 0xff00) >> 8, key & 0xff]

def main():
	global can_id

	if(len(sys.argv) < 2):
		print ("Usage: %s <can interface> " % (sys.argv[0]))
		sys.exit(1)

	interface = sys.argv[1]
	setup_can(interface)

	to_read = 0
	current_one = 0
	already_read = 0
	long_data = ""

	#change while true to a Thread process
	try:
		while True:
			msg, data = recv_msg()
			can_id = msg.arbitration_id
			data_type = data[0:2]
			#print (data)
			if data_type[0] == '0':
				# single frame
				pkt_len = int(data_type, 16)
				if len(data) < 3+pkt_len*3:
					continue # frame not complete
				payload = data[3:3+pkt_len*3]
				if (pkt_len):
					handle_data(payload, pkt_len)
			if data_type[0] == '1':
				# first frame
				if (verbose): print ("first frame received")
				if to_read != 0:
					# didn't finish the last long data transmission
	#				print "DIDN'T READ FULL PACKET"
					handle_data(long_data, already_read)
				# first frame packet
				pkt_len = (int(data_type[1], 16) << 8) + int(data[3:5], 16)
				current_one = 0
				to_read = pkt_len
				already_read = 6
				long_data = data[6:]
				# need to send flow control here
				if (verbose): print ("send flow control")

			if data_type[0] == '2':
				# consecutive frame
				if (verbose): print ("consecutive frame received")
				if current_one+1 == int(data_type[1],16) :
					current_one = int(data_type[1],16)
					payload = data[3:]
					read_this_time = min(to_read - already_read, 7)
		#			print "read %d" % read_this_time 
					already_read += read_this_time
					long_data += " " + data[3:3+read_this_time*3]
					if already_read == to_read:
						handle_data(long_data, to_read)
						to_read = 0					
				else:
					if (verbose): print("Error Lost Packet")

			if data_type[0] == '3':
				# flow control
				if (verbose): print ("Flow control frame received")				
	#			if type[1] == '0':
	#				print("clear to send") 	
	#			else:
	#				print("wait")
				pass		
			#print data
	except KeyboardInterrupt:
		print("Keyboard interrupt...")
		bus.shutdown()
		exit(0)


if __name__ == '__main__':
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((IP, PORT))
	server_socket.listen(1)
	print(f"Server listening on {IP}:{PORT}")
	
	while True:
		try:
			client_sock, addr = server_socket.accept()
			print(f"Accepted connection from {addr}")
			main()
			break # stop the loop if the function completes sucessfully
		except Exception as e:
			print("Function errored out!", e)
			print("Retrying ... ")
