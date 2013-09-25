import sys
import socket
from random import randint
import sqlite3

############
# SETTINGS #
############
network = 'irc.rizon.net'
port = 6667
channel = "#gikopoi"
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
		output = ""
        for s in xrange(2, len(self.splitted) - 1):
            output = output + s + " "
        return output[:-1]

#############
# FUNCTIONS #
#############

def sendMessageToChannel(text):
	irc.send("PRIVMSG " + channel + " :" + text + newLine)

def getRandomKaomoji():
	return kaomojiList[randint(0, len(kaomojiList)-1)]

##########
# QUOTES #
##########

def addQuote(msg):
    quote = msg.messageContent()[0:9]
    db = sqlite3.connect("gikobot.sqlite")
    db.execute("INSERT INTO quotes (quote) VALUES (?)", (quote,))
    db.commit()
    db.close()
    
def sendQuote():
    db = sqlite3.connect("gikobot.sqlite")
    quote = db.execute("SELECT quote FROM quotes ORDER BY random() LIMIT 1").fetchone()[0]
    sendMessageToChannel(quote)
    db.close()
	
#################
# PROGRAM START #
#################

f = open("f:\mieiprogrammi\gikobot\kaomoji.txt", "r")
kaomojiList = f.readlines()
f.close()

#Init database:
db = sqlite3.connect("gikobot.sqlite")
db.execute("CREATE TABLE IF NOT EXISTS quotes (quote TEXT)")
db.close()

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((network, port))
irc.send("NICK " + userNameBot + newLine)
irc.send("USER " + userNameBot + " 8 * : " + userNameBot + newLine)
irc.send("JOIN " + channel + newLine)
#sendMessageToChannel("Hello, this is GikoBot. I will try my best "
#					"to participate constructively in your conversations." + newLine)

currentLine = ""

while True:
	currentLine = currentLine + irc.recv(1)
	if currentLine[-1] == '\n':
		currentLine = currentLine[:-2] # remove '\r\n'
		print(currentLine)
		msg = Message(currentLine)
		if msg.isPing():
			irc.send("PONG " + msg.pingContent() + newLine)
			irc.send("JOIN " + channel + newLine) #in case i was ping'd before receiving all the MOTD (yotsubano.me does that, for example)
		elif msg.isMessage():
            command = msg.messageContent().split(" ")[0]
        
			if command == "!quit":
				sendMessageToChannel("SHUTTING DOWN")
				irc.send("PART " + channel + newLine)
				irc.send("QUIT" + newLine)
				irc.close()
				sys.exit(0)
			elif command == "!kaomoji":
				sendMessageToChannel(getRandomKaomoji())
            elif command == "!addquote"
                addQuote(msg)
            elif command == "!quote"
                sendQuote(msg)
			#else:
			#	sendMessageToChannel("SHUT UP, " + msg.messageSenderUsername())
				
		currentLine = ""
