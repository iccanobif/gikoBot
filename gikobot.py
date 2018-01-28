import socket
import select
from random import randint
from collections import deque
import sqlite3
import time
import traceback
from datetime import datetime
import os
import re

############
# SETTINGS #
############
NETWORK = 'irc.rizon.net'
PORT = 6667
BOTNAME = "GikoBot"
CHANNEL = "#gikopoi"
END_MESSAGE = "\r\n"
KAOMOJI_PATH = "kaomoji.txt"
SLEEP_DURATION = 0.5

#####################
# CLASS DEFINITIONS #
#####################


class Message:
    """This represents a message sent from the server"""

    def __init__(self, line):
        self.line = line
        # I expect lines to look kinda like this: ":iccanobif!iccanobif@fib.fib PRIVMSG #gikopoi :test"
        self.splitted = line.split(" ")

    def is_ping(self):
        return self.splitted[0] == "PING"

    def is_privmsg(self):
        if len(self.splitted) < 3:
            return False
        return self.splitted[1] == "PRIVMSG" and self.splitted[2] == CHANNEL

    def ping_content(self):
        return self.splitted[1]

    def sender_username(self):
        return self.splitted[0].split("!")[0][1:]

    def privmsg_content(self):
        output = ""
        for s in range(3, len(self.splitted)):
            output = output + self.splitted[s] + " "
        return output[1:-1]


class HereQuote:
    """This class is used by addQuote() to create multi-line quotes"""

    def __init__(self, terminator):
        self.terminator = terminator
        self.content = ''
        self.terminated = False

    def append(self, text):
        if not self.terminated:
            if self.terminator in text:
                text = text.split(self.terminator)[0]
                self.terminated = True
            else:
                text += '\n'
            self.content += text


class MessageQueue:
    """For handling per-user IO operations"""

    def __init__(self, user):
        self.queue = deque()
        self.nick = user        # target nick

    def is_empty(self):
        return len(self.queue) == 0

    def take(self):
        if self.is_empty():
            return None
        return self.queue.popleft()

    def put(self, e):
        self.queue.append(e)

    def __iter__(self):
        return iter(self.queue)

    def __next__(self):
        return next(self.queue)

    def __len__(self):
        return len(self.queue)


class GikoBot:
    def __init__(self):
        self.penis_length = 8
        self.here_quotes = {}
        self.write_queue = deque()
        self.message_queues = {}                # associate message queues with nicks
        self.socket = None
        self.input = ""

    def login(self):
        printDebug("Logging in...")
        self.socket = socket.socket()
        self.socket.connect((NETWORK, PORT))
        self.send('NICK ' + BOTNAME)
        self.send("USER " + BOTNAME + " 8 * : " + BOTNAME)
        self.send("JOIN " + CHANNEL)
        self.socket.setblocking(0)
        printDebug("Logged in...")

    def send(self, msg):
        self.socket.send(str(msg + END_MESSAGE).encode('utf-8'))
        time.sleep(SLEEP_DURATION)

    def send_privmsg(self, dest, msg):
        self.send('PRIVMSG ' + dest + " :" + msg)

    def write(self):
        if len(self.write_queue) == 0:
            return
        # TODO: reap dead message queues
        for mq in self.write_queue:
            msg = mq.take()
            if msg is not None:
                self.send_privmsg(mq.nick, msg)

    def handle_input(self, msg):
        if msg.is_ping():
            self.send('PONG ' + msg.ping_content())
            # iccanobif: in case i was ping'd before receiving all the MOTD (yotsubano.me does that, for example)
            self.send('JOIN ' + CHANNEL)
        elif msg.is_privmsg():
            nick = msg.sender_username()
            command = msg.privmsg_content().split(" ")[0].lower().strip()
            if nick in self.here_quotes:
                self.add_quote(nick, msg.privmsg_content())
            elif command == "!kaomoji":
                self.send_privmsg(CHANNEL, getRandomKaomoji())
            elif command == "!addquote":
                self.add_quote(nick, msg.privmsg_content()[10:])
            elif command == "!quote":
                self.send_quote()
            elif command == "!quotecount":
                db = sqlite3.connect("gikobot.sqlite")
                row = db.execute("SELECT count(1) FROM quotes").fetchone()
                count = row[0]
                db.close()
                self.send_privmsg(CHANNEL, "Total quotes: " + str(count))
            elif command == "!help":
                self.send_privmsg(
                    CHANNEL, "Commands available: !kaomoji !quote !addquote !touchpenis !figlet !dumpquotes")
                self.send_privmsg(
                    CHANNEL, "                    !quotecount !pop")
            elif command == "!kaomojicount":
                self.send_privmsg(
                    CHANNEL, "Kaomoji available: " + str(len(kaomoji_list)))
            elif command == "!touchpenis":
                self.touch_penis(nick)
            elif command == "!figlet":
                self.figlet(msg)
            elif command == "!dumpquotes":
                self.dump_quotes(msg)
            elif command == "!pop":
                self.pop_quote()
            elif command == "\x01action":
                self.send_privmsg(CHANNEL, 'ouch')

    def read(self):
        # roris: since this is probably larger than an irc message,
        # it is probably safe to assume that at least one tcp packet
        # has arrived
        data = self.socket.recv(1024)
        if data:
            data = data.decode('utf-8')
            self.input += data
            # roris: find the message terminator and slice instead of splitting
            # Split always a returns an array, regardless of the source being
            # split or not
            i = self.input.find("\r\n")
            while i != -1:
                msg = Message(self.input[0:i])
                self.input = self.input[i+2:]
                self.handle_input(msg)
                i = self.input.find("\r\n")
        else:
            printDebug("Restarting connection...")
            self.socket.close()
            time.sleep(60)
            self.login()

    def restart(self):
        self.input = ""
        self.socket.close()
        time.sleep(60)
        self.login()

    def be_a_bot(self):
        inputs = [self.socket]
        outputs = []

        if len(self.write_queue) != 0:
            outputs.append(self.socket)

        readable, writeable, exceptional = select.select(
            inputs, outputs, inputs, 1)

        if len(exceptional) != 0:
            self.restart()
            return

        if len(readable) != 0:
            self.read()

        if len(writeable) != 0:
            self.write()

    ############
    # COMMANDS #
    ############
    def figlet(self, msg):
        input = msg.privmsg_content()[8:]
        input = re.sub("[^a-zA-Z0-9 ]", "", input)[0:20]
        printDebug(input)
        output = os.popen(
            "figlet -d figletfonts \"" + input + "\"").readlines()
        for line in output:
            self.send_privmsg(CHANNEL, line)

    def touch_penis(self, usr):
        self.send_privmsg(CHANNEL, usr + ' gently touches the penis!')
        self.penis_length += 1
        p = '8'
        for i in range(0, self.penis_length):
            p += '='
        p += 'D'
        self.send_privmsg(CHANNEL, p)

    ##########
    # QUOTES #
    ##########
    def add_quote(self, nick, text):
        if text.strip() == "":
            return

        if nick not in self.here_quotes:
            p = re.compile(r'(^\s*<<)([\sa-zA-Z0-9_]+)$')
            m = p.match(text)

            if m:
                quote = HereQuote(m.group(2).strip())
                self.here_quotes[nick] = quote
                return
            else:   # regular quote
                quote = text
        else:
            quote = self.here_quotes[nick]
            quote.append(text)

            if not quote.terminated:
                return
            quote = quote.content
            self.here_quotes.pop(nick)

        ts = datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M")
        db = sqlite3.connect("gikobot.sqlite")
        db.execute(
            "INSERT INTO quotes (quote, num_views, timestamp) VALUES (?, (select min(num_views) from quotes), ?)", (quote, ts))
        db.commit()
        db.close()
        self.send_privmsg(CHANNEL, nick + ': added quote ;)')

    # Add all the quotes to the requesting user's message queue
    def dump_quotes(self, msg):
        sender = msg.sender_username()
        if sender not in self.message_queues:
            mq = MessageQueue(sender)
            self.write_queue.append(mq)
            self.message_queues[sender] = mq
        else:
            mq = self.message_queues[sender]

        db = sqlite3.connect("gikobot.sqlite")
        rows = db.execute(
            "SELECT quote, rowid, timestamp FROM quotes").fetchall()
        db.close()
        for row in rows:
            for line in row[0].splitlines():
                mq.put('#{0:04d} [{1}] {2}'.format(row[1], row[2], line))

    # send a random quote to the channel
    def send_quote(self):
        db = sqlite3.connect("gikobot.sqlite")
        row = db.execute(
            "SELECT quote, rowid, timestamp FROM quotes ORDER BY num_views, random() LIMIT 1").fetchone()
        for line in row[0].splitlines():
            self.send_privmsg(
                CHANNEL, '#{0:04d} [{1}] {2}'.format(row[1], row[2], line))

        db.execute(
            "UPDATE quotes set num_views = num_views + 1 where rowid = ?", (row[1],))
        db.commit()
        db.close()

    # send the last added quote to the channel
    def pop_quote(self):
        db = sqlite3.connect("gikobot.sqlite")
        row = db.execute(
            "SELECT quote, rowid, timestamp FROM quotes ORDER BY rowid DESC LIMIT 1").fetchone()
        for line in row[0].splitlines():
            self.send_privmsg(
                CHANNEL, '#{0:04d} [{1}] {2}'.format(row[1], row[2], line))

#############
# FUNCTIONS #
#############


def printDebug(text):
    print("[" + datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M") + "] " + text)


def getRandomKaomoji():
    return kaomoji_list[randint(0, len(kaomoji_list)-1)]

#################
# PROGRAM START #
#################


kaomoji_list = ""
with open(KAOMOJI_PATH, mode='r', encoding="utf-8") as f:
    kaomoji_list = f.readlines()
    f.close()

currentLine = ""
bot = GikoBot()
bot.login()

while True:
    bot.be_a_bot()
