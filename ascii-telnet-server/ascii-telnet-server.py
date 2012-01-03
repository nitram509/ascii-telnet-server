#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Copyright (c) 2008, Martin W. Kirst
## All rights reserved.
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
##    * Redistributions of source code must retain the above copyright notice,
##      this list of conditions and the following disclaimer.
##    * Redistributions in binary form must reproduce the above copyright
##      notice, this list of conditions and the following disclaimer in the
##      documentation and/or other materials provided with the distribution.
##    * Neither the name of the <ORGANIZATION> nor the names of its
##      contributors may be used to endorse or promote products derived from
##      this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
## OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
## EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
  ASCII art movie Telnet player.
  Version         : 0.1 (20080912)

  Can stream an ~20 minutes ASCII movie via Telnet emulation
  as stand alone server or via xinetd daemon. 
  Tested with Python 2.3, Python 2.5, Python 2.7

  Original art work : Simon Jansen ( http://www.asciimation.co.nz/ )
  Telnetification
  & Player coding   : Martin W. Kirst ( http://www.bitkings.de )
"""

import sys
import time
import SocketServer
import threading
import os.path
from StringIO import StringIO
from optparse import OptionParser


###############################################################################
MAXDIM = (80, 24)   # maximum dimension of the VT100 terminal


###############################################################################
class VT100Codes:
	"""
		Some escape codes used within VT100 Streams
		@see: http://ascii-table.com/ansi-escape-sequences-vt-100.php
	"""
	ESC = chr(27)          # VT100 escape character constant
	JMPHOME = ESC+"[H"     # Move cursor to upper left corner 
	CLEARSCRN = ESC+"[2J"  # Clear entire screen
	CLEARDOWN = ESC+"[J"   # Clear screen from cursor down
	
	def JMPXY(self, intX, intY):
		"""
			static method!
			Send VT100 commands: goto position X,Y
			@param intX: x coordinate (starting at 1) 
			@param intY: y coordinate (starting at 1)
			@return: the VT100 code as a string
		"""
		if not (intX<0 or intX>MAXDIM[0] or intY<0 or intY>MAXDIM[1]):
			return VT100Codes.ESC+"[" + str(intY) + ";" + str(intX) + "H"
		else:
			sys.stderr.write("Warning, coordinates out of range. (%d,%d)" % (intX,y))
			
###############################################################################
class Frame:
	"""
		One frame is 67 columns and 13 rows in effective size on screen.
		Use 'displayTime' to get the frame cycles this specific frame should
		be displayed.
		Use 'data' to get the 13 lines.
	"""
	def __init__(self):
		self.displayTime = 1  # number of frame cycles to display this frame, default 1
		self.data = []        # 13 lines

###############################################################################
class Movie:
	"""
		A movie consists of frames and is empty by default.
		Movies are loaded from text files.
		Use 'dimension' to get the dimension of the movie.
		A movie only can be loaded once. A second try will fail.
	"""
	
	def __init__(self):
		self.__frames = []
		self.__loaded = False
		self.dimension = (67, 13)
		f = Frame()
		f.data.append("No movie yet loaded.")
		self.__frames.append(f)
	
	def loadMovie(self, fileName):
		"""
			Loads the ASCII movie from given text file.
			Using an encoded format, described on
			http://www.asciimation.co.nz/asciimation/ascii_faq.html
			In short:
			67x14 chars,
			lines separated with 0x0a,
			first line is a number telling delay in number of frames,
			13 lines effective movie size,
			15 frames per second,
		"""
		if self.__loaded:
			# we don't want to be loaded twice.
			return False
		f = open(fileName, "r")
		self.__frames = []
		currentFrame = None
		counter = 0
		maxLinesPerFrame = self.dimension[1] + 1   # incl. meta data (time information)
		maxWidth = self.dimension[0]
		for l in f.readlines():
			i = -1
			if ((counter % maxLinesPerFrame) == 0):
				try:
					i = int(l[0:3])
				except:
					i = -1
			if (len(l.strip()) <= 3) and (i > 0) and (i <= 999):
				currentFrame = Frame()
				currentFrame.data = []
				currentFrame.displayTime = i
				self.__frames.append(currentFrame)
			else:
				if currentFrame:
					# first strip every white character from the right
					l = l.rstrip()
					# second fill them with blanks, that they later
					# automatically clear old lines from screen
					l = l.ljust(maxWidth)
					# to center the frame on the screen, we also add some
					# BLANKs on the left side
					l = l.rjust(maxWidth + (MAXDIM[0] - maxWidth)/2)
					currentFrame.data.append(l)
			counter += 1
		self.__loaded = True
		return True

	def getEncFrames(self):
		"""
			return a list with frames.
			Each frame carries its own display time, thats why it's 'encoded'.
		"""
		return self.__frames
	
###############################################################################
class TelnetRequestHandler(SocketServer.StreamRequestHandler):
	"""
		Request handler used for multi threaded TCP server
		@see: SocketServer.StreamRequestHandler
	"""
	
	filename = None # filename is set once, so it's immutable and safe for multi threading
	
	def handle(self):
		movie = Movie()
		movie.loadMovie(TelnetRequestHandler.filename)
		player = VT100Player(movie)
		player.onNextFrame = self.onNextFrame
		player.play()
		
	def onNextFrame(self, screenBuffer):
		"""
			Gets the current screen buffer and writes it to the socket.
		"""
		try:
			self.wfile.write(screenBuffer.read())
		except:
			pass # we ignore, when an IO error occurs ... the movie is over then ;-)
		

###############################################################################
class VT100Player:
	"""
		Player class plays a movie. Offers higher methods for play, stop,
		fast forward and rewind on the movie. It also stores the current
		position.
		It exposes the all frame numbers in real values. Therefore not encoded. 
	"""
	# __TIMEBAR = " <" + "".join("." for i in range(MAXDIM[0]-4)) + ">"
	__TIMEBAR = " <" + "".ljust(MAXDIM[0]-4) + ">"
	
	def __init__(self, movie):
		self.__movie = movie
		self.__movCursor = 0   # virtual cursor pointing to the current frame
		self.__maxFrames = 0
		for f in self.__movie.getEncFrames():
			self.__maxFrames += f.displayTime

	def getDuration(self):
		"""
			return the number of seconds this movie is playing
		"""
		return self.__maxFrames / 15 # 15 frames per second

	def play(self):
		"""
			plays the movie
		"""
		for frame in self.__movie.getEncFrames():
			self.__movCursor += frame.displayTime
			self.__onNextFrameInternal(frame, self.__movCursor)
			time.sleep(frame.displayTime/15.0)
	
	def __onNextFrameInternal(self, frame, framePos):
		"""
			internal event, happen when next frame should be drawn
		"""
		screenbuf = StringIO()
		if framePos <= 1:
			screenbuf.write(VT100Codes.CLEARSCRN)
		# center vertical, with respect to the time bar
		y = (MAXDIM[1] - 1 - self.__movie.dimension[1]) / 2
		screenbuf.write(VT100Codes().JMPXY(1, y)) # self.__sendJMPXY(1, y);
		for line in frame.data:
			screenbuf.write(line + "\r\n")
		self._updateTimeBar(screenbuf, framePos, self.__maxFrames)
		# now rewind the internal buffer and fire the public event
		screenbuf.seek(0)
		self.onNextFrame(screenbuf)
	
	def onNextFrame(self, screenBuffer):
		"""
			Public event method, which can be used to get new Screens.
			
			@param screenBuffer: its a file like object containing the VT100 screen buffer
		"""
		pass
	
	def _updateTimeBar(self, screenBuffer, intCurrentValue, intMaxSize=10):
		"""
			Writes at the bottom of the screen a line like this
			<.......o.....................>
			Left and right are one blank spaces from the max screen dimensions
			It should visualize a timeline with 'o' is the current position.
			
			@param screenBuffer: file like object, where the data is written to
			@param intCurrentValue: current value
			@param intMaxSize: maximum value  
		"""
		screenBuffer.write(VT100Codes().JMPXY(1, MAXDIM[1])) # self.__sendJMPXY(1,MAXDIM[1])
		screenBuffer.write(self.__TIMEBAR)    # self.wfile.write(self.__TIMEBAR)
		# now some weird calculations incl. some tricks to avoid rounding errors. 
		x = min( (((intCurrentValue) * (MAXDIM[0] - 4)) / (intMaxSize - 1)) , (MAXDIM[0] - 4 - 1) )
		screenBuffer.write(VT100Codes().JMPXY(x+3, MAXDIM[1])) # self.__sendJMPXY(x+3,MAXDIM[1])
		screenBuffer.write("o")

###############################################################################
def runTcpServer(interface, port, filename):
	"""
		@param interface: bind to this interface 
		@param port: bind to this port
		@param filename: file name of the ASCII movie  
	"""
	TelnetRequestHandler.filename = filename
	server = SocketServer.ThreadingTCPServer((interface, port), TelnetRequestHandler)
	try:
		server.serve_forever()
	except:
		pass # if some one cancels the player, we don't care

###############################################################################
def onNextFrameStdOut(screenBuffer):
	sys.stdout.write(screenBuffer.read())
	
def runStdOut(filename):
	"""
		@param filename: file name of the ASCII movie  
	"""
	movie = Movie()
	movie.loadMovie(filename)
	player = VT100Player(movie)
	player.onNextFrame = onNextFrameStdOut
	try:
		player.play()
	except:
		pass # if some one cancels the player, we don't care
	

### MAiN ######################################################################
if __name__ == "__main__":
	usage = "Usage: %prog [options]"
	parser = OptionParser(usage=usage)
	parser.add_option("", "--standalone", dest="tcpserv", action="store_true",
					  help="Run as stand alone multi threaded TCP server (default)")
	parser.add_option("", "--stdout", dest="tcpserv", action="store_false",
					  help="Run with STDIN and STDOUT, for example in XINETD " + 
								"instead of stand alone TCP server. " +
								"Use with python option '-u' for unbuffered " +
								"STDIN STDOUT communication")
	parser.add_option("-f", "--file", dest="filename", metavar="FILE",
					  help="Text file containing the ASCII movie")
	parser.add_option("-i", "--interface", dest="interface",
					  help="Bind to this interface (default '0.0.0.0', all interfaces)",
					  default="0.0.0.0" )
	parser.add_option("-p", "--port", dest="port", metavar="PORT",
					  help="Bind to this port (default 23, Telnet)",
					  default=23, type="int")
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
					  help="Verbose (default for TCP server)")
	parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
					  help="Quiet! (default for STDIN STDOUT server)")
	parser.set_defaults(interface="0.0.0.0",
					    port=23,
					    tcpserv=True,
					    verbose=True,)
	(options, args) = parser.parse_args()
	
	if not (options.filename and os.path.exists(options.filename)):
		parser.exit(1, "Error, file not found! See --help for details.\n")
	
	if options.tcpserv:
		if options.verbose:
			print "Running TCP server on %s:%d" % (options.interface, options.port)
			print "Playing movie " + options.filename
		runTcpServer(options.interface, options.port, options.filename)
	else:
		runStdOut(options.filename)
		
	sys.exit(0)