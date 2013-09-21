import sys
import socket

############
# SETTINGS #
############
network = 'irc.rizon.net'
port = 6667
channel = "#gikopoiTest"
userNameBot = "GikoBot"

#####################
# CLASS DEFINITIONS #
#####################

# class Message:
	# """This represents a message sent from the server"""
	# def __init__(self, line):
		# self.line = line
		# self.splitted = line.split(" ")
	
#I expect lines to look kinda like this: ":iccanobif!iccanobif@fib.fib PRIVMSG #gikopoi :test"	

	# def isPing(self):
		# return splitted[0] == "PING"
		
	# def pingContent(self):
		# return splitted[1]z
	
	# def isMessage(self):
		# return splitted[1] == "PRIVMSG" and splitted[2] == channel
	
	# def senderUsername:
		# return splitted[0].split("!")[0][1:].upper()
		
	# def content(self):
		# return splitted[3][:6]
		
#:iccanobif!iccanobif@fib.fib PRIVMSG #gikopoi :test
		
		
		
		


#################
# PROGRAM START #
#################

irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
irc.connect ( ( network, port ) )
irc.send ( "NICK " + userNameBot + "\r\n" )
irc.send ( "USER " + userNameBot + " 8 * : " + userNameBot + "\r\n" )
irc.send ( "JOIN " + channel + "\r\n" )
#irc.send ( 'PRIVMSG #gikopoi :Hello, this is GikoBot. I will try my best to participate constructively in your conversations.\r\n' )

currentLine = ""

while True:
	currentLine = currentLine + irc.recv(1)
	if currentLine[-1] == '\n':
		print(currentLine[:-2])
		# I expect lines to look kinda like this: ":iccanobif!iccanobif@fib.fib PRIVMSG #gikopoi :test"
		splitted = currentLine.split(" ")
		if splitted[1] == "PRIVMSG" and splitted[2] == channel:
			if splitted[3][:6] != ":!quit":
				username = splitted[0].split("!")[0][1:].upper()
				irc.send("PRIVMSG " + channel + " :SHUT UP, " + username + "\r\n")
			else:
				irc.send ( "PART " + channel + "\r\n" )
				irc.send ( "QUIT\r\n" )
				irc.close()
				sys.exit(0)
				
		currentLine = ""
