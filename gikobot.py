import sys
import socket
from random import randint
import sqlite3
import time
import traceback
import datetime
import os
import re
import codecs

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
        return self.splitted[0].split("!")[0][1:]
        
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
    irc.send("PRIVMSG " + channel + " :" + text + newLine)

def sendMessageToNick(nick, text):
    irc.send("PRIVMSG " + nick + " :" + text + newLine)

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

penisLength = 0

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
    #TODO: Handle len(currentLine) == 0 (that means we got disconnected and 
    #      have to reconnect
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
                command = msg.messageContent().split(" ")[0].lower()
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
		elif command == "!quotecount":
                    db = sqlite3.connect("gikobot.sqlite")
                    row = db.execute("SELECT count(1) FROM quotes").fetchone()
                    count = row[0]
		    db.close()
		    sendMessageToChannel("Total quotes: " + str(count))
		elif command == "!help":
		    sendMessageToChannel("Commands available: !kaomoji !quote !addquote !quotecount !touchPenis !figlet !dumpquotes")
		elif command == "!kaomojicount":
		    sendMessageToChannel("Kaomoji available: " + str(len(kaomojiList)))
		elif command == "!touchpenis":
		    sendMessageToChannel(msg.messageSenderUsername() + " gently touches the penis!")
		    penisLength += 1
		    penis = "8"
		    for i in xrange(0, penisLength):
		        penis = penis + "="
	            penis = penis + "D"
		    sendMessageToChannel(penis)
		elif command == "!figlet":
                    input = msg.messageContent()[8:]
		    input = re.sub("[^a-zA-Z0-9 ]", "", input)[0:20]
		    print(input)
		    output = os.popen("./figlet -d figletfonts \"" + input + "\"").readlines()
		    for line in output:
		        sendMessageToChannel(line)
                        time.sleep(0.5)
                elif command == "!dumpquotes":
                    # would be dangerous if the list grows huge.. well it isn't huge yet, so nothing to worry about.
                    # from time import sleep
                    db = sqlite3.connect("gikobot.sqlite")
                    quoteList = db.execute("SELECT quote FROM quotes").fetchall()
                    db.close()
                    for quote in quoteList:
                        sendMessageToNick(msg.messageSenderUsername().encode('utf8'), quote[0].encode('utf8'))
                        # do a sleep here to avoid floods
                        time.sleep(0.5)
                    print("finished dumping to", msg.messageSenderUsername())
                elif command == "!pop":
		    sendMessageToChannel("not implemented lol")
		
        except:
	    traceback.print_exc()
            try:
		#TODO: if the error was a disconnection from the server?
                sendMessageToChannel(errorMessage)
            except:
	    	print("some error?")
		
        currentLine = ""
