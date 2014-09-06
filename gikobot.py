import sys
import socket
from random import randint
import sqlite3
import time
import traceback
import datetime

############
# SETTINGS #
############
network = 'irc.rizon.net'
port = 6667
channel = "#gikopoi"
userNameBot = "GikoBot"
newLine = "\r\n"
kaomojiPath = "kaomoji.txt"

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
    	if len(self.splitted) < 3 : return False
        return self.splitted[1] == "PRIVMSG" and self.splitted[2] == channel
    
    def messageSenderUsername(self):
        return self.splitted[0].split("!")[0][1:].upper()
        
    def messageContent(self):
        output = ""
        for s in xrange(3, len(self.splitted)):
            output = output + self.splitted[s] + " "
        return output[1:-1]

#############
# FUNCTIONS #
#############

def printDebug(text):
    print("[" + datetime.datetime.strftime(datetime.datetime.now(), "%d/%m/%Y %H:%M") + "] " + text)

def sendMessageToChannel(text):
    print(type(text))
    irc.send("PRIVMSG " + channel + " :" + text + newLine)

def getRandomKaomoji():
    return kaomojiList[randint(0, len(kaomojiList)-1)]

##########
# QUOTES #
##########

def addQuote(msg):
    quote = msg.messageContent()[10:]
    db = sqlite3.connect("gikobot.sqlite")
    db.execute("INSERT INTO quotes (quote, num_views) VALUES (?, (select min(num_views) from quotes))", (quote,))
    db.commit()
    db.close()
    sendMessageToChannel("Quote added")
    
def sendQuote():
    db = sqlite3.connect("gikobot.sqlite")
    row = db.execute("SELECT quote, rowid FROM quotes ORDER BY num_views, random() LIMIT 1").fetchone()
    quote = row[0]
    rowid = row[1]
    sendMessageToChannel(quote.encode("utf8"))
    db.execute("UPDATE quotes set num_views = num_views + 1 where rowid = ?", (rowid,))
    db.commit()
    db.close()

#################
# PROGRAM START #
#################

f = open(kaomojiPath, "r")
kaomojiList = f.readlines()
f.close()

#Init database:
db = sqlite3.connect("gikobot.sqlite")
db.execute("CREATE TABLE IF NOT EXISTS quotes (quote TEXT)")
db.close()

print("Connecting...")
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((network, port))
irc.send("NICK " + userNameBot + newLine)
print("Logging in...")
time.sleep(0.5)
irc.send("USER " + userNameBot + " 8 * : " + userNameBot + newLine)
time.sleep(0.5)
irc.send("JOIN " + channel + newLine)
time.sleep(0.5)
print("Logged in.")

currentLine = ""

while True:
    currentLine = currentLine + irc.recv(1)
    if currentLine[-1] == '\n':
    
        try:
            currentLine = currentLine[:-2] # remove '\r\n'
	    currentLine = currentLine.decode("utf8")
	    printDebug(currentLine)
            msg = Message(currentLine)
            if msg.isPing():
                irc.send("PONG " + msg.pingContent() + newLine)
                irc.send("JOIN " + channel + newLine) #in case i was ping'd before receiving all the MOTD (yotsubano.me does that, for example)
            elif msg.isMessage():
                command = msg.messageContent().split(" ")[0]
#                if command == "!quit":
#                    sendMessageToChannel("SHUTTING DOWN")
#                    irc.send("PART " + channel + newLine)
#                    irc.send("QUIT" + newLine)
#                    irc.close()
#                    sys.exit(0)
                if command == "!kaomoji":
                    sendMessageToChannel(getRandomKaomoji())
                elif command == "!addquote":
                    addQuote(msg)
                elif command == "!quote":
                    sendQuote()
		elif command == "!help":
		    sendMessageToChannel("Commands available: !kaomoji !quote !addquote")
                #else:
                #   sendMessageToChannel("SHUT UP, " + msg.messageSenderUsername())
        except:
	    traceback.print_exc()
            try:
                sendMessageToChannel(errorMessage)
            except:
	    	print("some error?")
		
        currentLine = ""
