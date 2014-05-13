import sys
import socket
import struct
import os
import select

#Create RRQ/WRQ packet.
def createRequestPacket(command, filename):
	return struct.pack('>H' + str(len(filename)) + 'sb5sb', command, filename, 0, 'OCTET', 0) #fyrsti param er format skv byte-um
#Create Data packet.
def createDataPacket(command, block, dataPack):
	return struct.pack('>HH', command, block) + dataPack 
#Create Acknowledgement packet.
def createACKPacket(command, block):
	return struct.pack('>HH', command, block) 
#Create Error packet.
def createErrorPacket(command, errorCode, errorMsg):
	return struct.pack('>HH' + str(len(errorMsg)) + 'sb', command, errorCode, errorMsg, 0) 
#If client receives error, print out error and error message.
def errorHandling(block, dataPack):
	length = len(dataPack) - 4
	errData = struct.unpack('>' + str(length) + 's', dataPack[4:])[0]
	print 'Error no ' + str(block) + '. ' + str(errData)
	sys.exit(-1)
#Send RRQ and follow up.
def getCmd():
	packet = createRequestPacket(1, filename)
	try:
		sock.sendto(packet, (server, port))
		sock.settimeout(3)
	except:
		print 'Packet has not been sent'
	data = 516
	fullLength = True
	firstPack = True
#	While the packet is of full length we keep on receiving packets, sending acknowledgements and writing the file.
	while (fullLength == True):
		try:
			dataPack, (ResponseAddress, ResponsePort) = sock.recvfrom(516)
		except:
			print 'Packet not recieved'
		command = struct.unpack(">H", dataPack[:2])[0]
		block = struct.unpack(">H", dataPack[2:4])[0]
		data = dataPack[4:]
#		roll over, if file has more than 65535 packets reset block count.
		if (block == 65535):
			firstPack = False
			sendBlock = 0
		else:
			sendBlock = block + 1
		ackPacket = createACKPacket(4, sendBlock)
#		Handle error packets from server.
		if(command == 5 and block != 0):
			errorHandling(block, dataPack)
#		change port number when first pack has been received.
		if (block == 1 and firstPack == True):
			newPort = ResponsePort
#			Open file to write, create it if it does not exist, overwrite data in already existing file with that name.
			try:
				f = open(filename, 'wb')
			except:
				print 'No such file'
				sys.exit(-1)
			dataString = str(data)
			f.write(dataString)
			sock.sendto(ackPacket, (server, newPort))
		else:
#			Check if port number is right, if so write data else send error pack.
			if (newPort == ResponsePort):
#				Open file to write, append any data to the file.
				try:
					f = open(filename, 'ab')
				except:
					print 'No such file'
					sys.exit(-1)
				dataString = str(data)
				f.write(dataString)
				sock.sendto(ackPacket, (server, newPort))
			else:
				errorPacket = createErrorPacket(5, 0, 'not right port')
				sock.sendto(errorPacket, (server, newPort))
		f.close()
		if (len(dataPack) < 516):
			fullLength = False
#Send WRQ and follow up.
def postCmd():
	packet = createRequestPacket(2, filename)
	sock.sendto(packet, (server, port))
	dataLeftToSend = True
	try:
		f = open(filename, 'rb')
	except:
		print 'No such file'
		sys.exit(-1)
#	While the packet is of full length we keep on sending data packets when we receive acknowledgements.
	while (dataLeftToSend == True):	
		try:
			recPack, (ResponseAddress, ResponsePort) = sock.recvfrom(516)
		except:
			print 'Packet not recieved'
		command = struct.unpack(">H", recPack[:2])[0]
		block = struct.unpack(">H", recPack[2:4])[0]
#		Handle error packets from server.
		if(command == 5):
			errorHandling(block, recPack)
#		If server has not received last packet, resend last packet.S
		elif (command == 5 and block == 0):
			sock.sendto(dataPack, (ResponseAddress, ResponsePort))
#		Else send file over in packets of 512 bytes.
		else:
			data = f.read(512)
#			roll over, if file has more than 65535 packets reset block count.
			if (block == 65535):
				print 'start over'
				sendBlock = 0
			else:
				sendBlock = block + 1
			dataPack = createDataPacket(3, sendBlock, data)
			sock.sendto(dataPack, (ResponseAddress, ResponsePort))
		if(len(data) < 512):
			dataLeftToSend = False
	f.close()


server = sys.argv[1]
command = sys.argv[2]
filename = sys.argv[3]
time_in_seconds = 3
 
if len(sys.argv) == 5:
	port = sys.argv[4]
else:
	port = 69

#Start connection, first argument represents the internet connection and the second represents UDP connection
try:
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
except:
	print 'No connection'
	
if command == "lesa":
	getCmd()
elif command == "skrifa":
	postCmd()
else:
	print "Error: please enter properly formatted command"
	sys.exit(-1)