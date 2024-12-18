#!/usr/bin/python
#!/usr/bin/env python3


import sys
import can
import time
import random
import socket
import threading

IP = '141.215.219.197'
PORT = 8080

clean, longdata = range(2)
bus = can.Bus()
can_id = ""
verbose = 1
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

def broadcast_wiper_data():
	global wiper_status
	while True:
		with status_lock:
			stat_msg = [
				wiper_status, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
			]
		send_msg(0x058, stat_msg)
		time.sleep(0.1)
		


def handle_data(payload, pkt_len):
	global security_access, session, key, attempts
	global wiper_status
	if len(payload) < 2: return	
	id = int(payload[0:2],16)
	print(id)
	id_s = get_id_string(id)
	if can_id == 0x123:		
		print ("ECM Module")
		if id == 0x10: #issue with CC.py not being able to pick it up - idk why
			if (verbose): print ("Diagnostics access")
			security_access = 0
			if len(payload) < 6:
				send_msg(0x321, [0x03, 0x7F, id, 0x13])
				return
			pid = int(payload[3:5],16)
			print(pid)
			if pid == 0x03:
				session = 3
				send_msg(0x321, [0x02, id+0x40, pid])
			else:
				session = 1
				send_msg(0x321, [0x03, id+0x40, pid])
		if id == 0x3E:
			if (verbose): print ("Tester Present")
			security_access = 0					
			if len(payload) < 6:
				send_msg(0x321, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			pid = int(payload[3:5],16)
			if pid == 0x01:
				session = 1			
				send_msg(0x321, [0x02, id+0x40, pid]) 
				send_msg(0x321, [0x10, 0x21, 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x62]) 
				send_msg(0x321, [0x21, 0x6C, 0x61, 0x73, 0x74, 0x6F, 0x66, 0x66])
				send_msg(0x321, [0x22, 0x7D])
				#.encode()
				client_sock.sendall("0x00".encode('utf-8'))


			else:
				session = 1
				send_msg(0x321, [0x03, 0x7F, id, 0x12]) #subfunctionNotSupported
		else:
			send_msg(0x321, [0x03, 0x7F, id, 0x11])		

	elif can_id == 0x456:
		print ("BCM module")
		if id == 0x10:
			if (verbose): print ("Diagnostics access")
			security_access = 0
			print(len(payload))
			if len(payload) < 6:
				send_msg(0x654, [0x03, 0x7F, id, 0x13])
				return
			pid = int(payload[3:5],16)
			print(pid)
			if pid == 0x03:
				session = 3
				send_msg(0x654, [0x02, id+0x40, pid])
			elif pid == 0x01:
				session = 1
				send_msg(0x654, [0x02, id+0x40, pid])
			else:
				send_msg(0x654, [0x03, 0x7F, id, 0x12]) #subfunctionNotSupported

		elif id == 0x11:
			if session == 3:
				if (verbose): print ("ECUReset")
				if len(payload) < 2:
					send_msg(0x654, [0x03, 0x7F, id, 0x13])
					return
				pid = int(payload[3:5],16)
				if pid == 0x01:
					send_msg(0x654, [0x02, id+0x40, pid])
				elif pid == 0x03:
					send_msg(0x654, [0x02, id+0x40, pid])
					send_msg(0x654, [0x10, 0x13, 0x66, 0x6C, 0x61, 0x67, 0x7B, 0x74])
					send_msg(0x654, [0x21, 0x72, 0x69, 0x63, 0x6B, 0x79, 0x5F, 0x6C])
					send_msg(0x654, [0x22, 0x65, 0x76, 0x65, 0x6C, 0x73, 0x7D])
					send_msg(0x654, [0x10, 0x62, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
					with status_lock:
						wiper_status = 0x01
					print("Wipers activated")
					client_sock.send("0x0D".encode('utf-8'))
					time.sleep(20)
					with status_lock:
						wiper_status = 0x00
					print("Wipers off, reset complete")
					client_sock.send("0x0E".encode('utf-8'))
					#client_sock.sendall(b"0x0D")
				else:
					send_msg(0x654, [0x03, 0x7F, id, 0x12])
			else:
				send_msg(0x654, [0x03, 0x7F, id, 0x7F])
		else:
			send_msg(0x654, [0x03, 0x7F, id, 0x11]) #serviceNotSupported
			
			
	elif can_id == 0x789:
		print ("VCU Module")

		if id == 0x10:
			if (verbose): print ("Diagnostics access")
			security_access = 0					
			if len(payload) < 6:
				send_msg(0x7FF, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			pid = int(payload[3:5],16)
			if pid == 0x01:
				session = 1			
				send_msg(0x7FF, [0x02, id+0x40, pid]) 
			elif pid == 0x02:				
				session = 2
				send_msg(0x7FF, [0x02, id+0x40, pid]) 
			else:
				#session = 1
				send_msg(0x7FF, [0x03, 0x7F, id, 0x12]) #subfunctionNotSupported		

		elif id == 0x23:
			if (verbose): print ("Read Memory by Address")
			print ("Read Memory by Address")
			print (len(payload))
			if len(payload) < 6:
				send_msg(0x7FF, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			
			if session != 2:				#if not in session 2 repond with serviceNotSupportedInActiveSession 03 7f 23 7f
				send_msg(0x7FF, [0x03, 0x7F, id, 0x7F]) #serviceNotSupportedInActiveSession
				return
			
			pid = int(payload[3:5],16)			
			if pid == 0x21: #2-byte address 1-byte length
				
				if security_access != 1: #if security access is not 1 respond with securityAccessDenied 03 7f 23 33
					send_msg(0x7FF, [0x03, 0x7F, id, 0x33]) #securityAccessDenied
					return
				if len(payload) < 5:
					send_msg(0x7FF, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat
					return
				print (f"Payload: {payload}")
				address = payload[6:8] + payload[9:11]
				length = payload[12:14]
				address = int(address, 16)
				length = int(length, 16)
				print (f"Address: {address}")
				print (f"Length: {length}")

				if address == 0x1209 and length == 0x05:
					#66 6C 61 67 7B 79 61 5F 64 69 64 5F 69 74 5F 64 75 64 65 7D
					send_msg(0x7FF, [0x10, id+0x40, 0x12, 0x09, 0x14, 0x66, 0x6C, 0x61]) #positive response with 1-byte of memory data
					send_msg(0x7FF, [0x21, 0x67, 0x7B, 0x79, 0x61, 0x5F, 0x64, 0x69]) #positive response with 1-byte of memory data	
					send_msg(0x7FF, [0x22, 0x64, 0x5F, 0x74, 0x5F, 0x64, 0x75, 0x64]) #positive response with 1-byte of memory data
					send_msg(0x7FF, [0x23, 0x65, 0x7D]) #positive response with 1-byte of memory data
					#add logic for TCP socket 
					client_sock.sendall("0x04".encode('utf-8'))
				else:
					send_msg(0x7FF, [0x03, 0x7F, id, 0x13]) #invalid format
			
			else:
				send_msg(0x7FF, [0x03, 0x7F, id, 0x13]) #invalid format only accepting 2-byte address and 1-byte length


		elif id == 0x27:
			if (verbose): print ("Security access")
			if (session < 2):
				send_msg(0x7FF, [0x03, 0x7F, id, 0x7F]) #serviceNotSupportedInActiveSession		
				print ("serviceNotSupportedInActiveSession")
				return				
			if len(payload) < 6:
				send_msg(0x7FF, [0x03, 0x7F, id, 0x13]) #incorrectMessageLengthOrInvalidFormat			
				return
			pid = int(payload[3:5],16)
			if pid == 0x01:
				if (verbose): print ("Sending seed")
				#generate random seed
				s1 = random.randint(0,255)				
				s2 = random.randint(0,255)
				s3 = random.randint(0,255)
				send_msg(0x7FF, [0x05, id+0x40, pid, s1, s2, s3])
				key = key_from_seed([s1, s2, s3])
				print(f"stored key:  {key}")
				attempts = 0
			if pid == 0x02:
				if (verbose): print ("verifying key")

				if len(payload) < 5:
					send_msg(0x7FF, [0x03, 0x7F, id, 0x13])
					return				
				if attempts > 5:
					send_msg(0x7FF, [0x03, 0x7F, id, 0x36])
					security_access = 0
					session = 1
					return
				
				key_received = ['0x' + payload[6:8], '0x' + payload[9:11], '0x' + payload[12:14]] #will need to change this bug for single digit hex vals
				print ('key received')
				print((key_received))
				if (key_received == key):
					send_msg(0x7FF, [0x02, id+0x40, 0x02])
					send_msg(0x7FF, [0x10, 0x0C, 0x72, 0x65, 0x4D, 0x45, 0x4D, 0x62])
					send_msg(0x7FF, [0x21, 0x65, 0x72, 0x3A, 0x12, 0x09])
					security_access = 1
					print ("Success")
				else:
					send_msg(0x7FF, [0x03, 0x7F, id, 0x35])					
					attempts += 1

		else:
			send_msg(0x7FF, [0x03, 0x7F, id, 0x11]) #serviceNotSupported	
	else:
		pass
		#unknown module
	

def setup_can(interface):
	global bus
	try:
		print("Bring up %s...." % (interface))
		time.sleep(0.1)
		bus = can.interface.Bus(interface='socketcan', channel=interface, bitrate=500000)

	
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
	# seed = [0x00, 0x00, 0x00]
	print("generated seed: ")
	print(seed)
	key = [hex(seed_val ^ 0xFF) for seed_val in seed]
	print("calculated key: ")
	print(key)
	return key

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
			print(msg)
			print(data)
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
	wiper_status = 0x00
	status_lock = threading.Lock()
	
	while True:
		try:
			client_sock, addr = server_socket.accept()
			print(f"Accepted connection from {addr}")
			threading.Thread(target=broadcast_wiper_data, daemon=True).start()
			main()
			#broadcast_wiper_data()
			break # stop the loop if the function completes sucessfully
		except Exception as e:
			print("Function errored out!", e)
			print("Retrying ... ")
