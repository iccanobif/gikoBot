import sys
import socket

############
# SETTINGS #
############
network = 'irc.rizon.net'
port = 6667
channel = "#gikopoiTest"
userNameBot = "GikoBot"
newLine = "\r\n"

#####################
# CLASS DEFINITIONS #
#####################

class Message:
	"""This represents a message sent from the server"""
	def __init__(self, line):
		self.line = line
		self.splitted = line.split(" ")

#I expect lines to look kinda like this: ":iccanobif!iccanobif@fib.fib PRIVMSG #gikopoi :test"	

	def isPing(self):
		return self.splitted[0] == "PING"
		
	def pingContent(self):
		return self.splitted[1]
	
	def isMessage(self):
		return self.splitted[1] == "PRIVMSG" and self.splitted[2] == channel
	
	def messageSenderUsername(self):
		return self.splitted[0].split("!")[0][1:].upper()
		
	def messageContent(self):
		return self.splitted[3][1:]

def sendMessageToChannel(text):
	irc.send("PRIVMSG " + channel + " :" + text + newLine)

#################
# PROGRAM START #
#################

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((network, port))
irc.send("NICK " + userNameBot + newLine)
irc.send("USER " + userNameBot + " 8 * : " + userNameBot + newLine)
irc.send("JOIN " + channel + newLine)
sendMessageToChannel("Hello, this is GikoBot. I will try my best "
					"to participate constructively in your conversations." + newLine)

currentLine = ""

while True:
	currentLine = currentLine + irc.recv(1)
	if currentLine[-1] == '\n':
		currentLine = currentLine[:-2] # remove '\r\n'
		print(currentLine)
		msg = Message(currentLine)
		if msg.isPing():
			irc.send("PONG " + msg.pingContent() + newLine)
		elif msg.isMessage():
			if msg.messageContent() == "!quit":
				sendMessageToChannel("SHUTTING DOWN")
				irc.send("PART " + channel + newLine)
				irc.send("QUIT" + newLine)
				irc.close()
				sys.exit(0)
			else:
				sendMessageToChannel("SHUT UP, " + msg.messageSenderUsername())
				
		currentLine = ""
