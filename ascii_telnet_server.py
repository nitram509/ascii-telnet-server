# coding=utf-8
# !/usr/bin/env python

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Copyright (c) 2008, Martin W. Kirst All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
#  Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
#  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#  PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#  TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
  ASCII art movie Telnet player.
  Version         : 0.1

  Can stream an ~20 minutes ASCII movie via Telnet emulation
  as stand alone server or via xinetd daemon.
  Tested with Python 2.6+, Python 3.5+

  Original art work : Simon Jansen ( http://www.asciimation.co.nz/ )
  Telnetification
  & Player coding   : Martin W. Kirst ( https://github.com/nitram509/ascii-telnet-server )
  Python3 Update: Ryan Jarvis

"""
from __future__ import division, print_function

import os
import sys
from optparse import OptionParser

from ascii_telnet.ascii_movie import Movie
from ascii_telnet.ascii_player import VT100Player
from ascii_telnet.ascii_server import TelnetRequestHandler, ThreadedTCPServer


def runTcpServer(interface, port, filename, framerate, sizew, sizeh, fsizew, fsizeh):
    """
    Start a TCP server that a client can connect to that streams the output of
     Ascii Player

    Args:
        interface (str):  bind to this interface
        port (int): bind to this port
        filename (str): file name of the ASCII movie
        framerate (int): FPS of the movie
        sizew (int): Width of the screen
        sizeh (int): Height of the screen(Including timebar)
        fsizew (int): Width of the movie
        fsizeh (int): Height of the movie
    """
    TelnetRequestHandler.filename = filename
    TelnetRequestHandler.framerate = framerate
    TelnetRequestHandler.sizew = sizew
    TelnetRequestHandler.sizeh = sizeh
    TelnetRequestHandler.fsizew = fsizew
    TelnetRequestHandler.fsizeh = fsizeh
    server = ThreadedTCPServer((interface, port), TelnetRequestHandler)
    server.serve_forever()


def runStdOut(filepath, framerate, sizew, sizeh, fsizew, fsizeh):
    """
    Stream the output of the Ascii Player to STDOUT
    Args:
        filepath (str): file path of the ASCII movie
        framerate (int): FPS of the movie
        sizew (int): Width of the screen
        sizeh (int): Height of the screen(Including timebar)
        fsizew (int): Width of the movie
        fsizeh (int): Height of the movie
    """

    def draw_frame_to_stdout(screen_buffer):
        sys.stdout.write(screen_buffer.read().decode('iso-8859-15'))

    movie = Movie(sizew, sizeh, fsizew, fsizeh)
    movie.load(filepath)
    player = VT100Player(movie, framerate)
    player.draw_frame = draw_frame_to_stdout
    player.play()


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
                      default="0.0.0.0")
    parser.add_option("-p", "--port", dest="port", metavar="PORT",
                      help="Bind to this port (default 23, Telnet)",
                      default=23, type="int")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Verbose (default for TCP server)")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
                      help="Quiet! (default for STDIN STDOUT server)")
    parser.add_option("-r","--framerate",dest="framerate",metavar="FPS",
                      help="Set the framerate of the movie(default 24)")
    parser.add_option("-s","--size",dest="size",metavar="WIDTHxHEIGHT",
                      help="Set the screen size of the movie(default 80x24). "+
                           "Including the timebar, so the maximum framesize is WIDTHx(HEIGHT-1)"+
                           "(default maximum 80x23)")
    parser.add_option("-S","--framesize",dest="framesize",metavar="FRAME_WIDTHxFRAME_HEIGHT",
                      help="Set the frame size(depending on the movie you are to play) "+
                           "(default 67x13)")
    parser.set_defaults(interface="0.0.0.0",
                        port=23,
                        tcpserv=True,
                        verbose=True,
                        framerate=24,
                        size="80x24",
                        framesize="67x13" )
    options = parser.parse_args()[0]

    if not (options.filename and os.path.exists(options.filename)):
        parser.exit(1, "Error, file not found! See --help for details.\n")
    
    try:
        framerate = int(options.framerate)
        sizew = int(options.size.split("x",1)[0])
        sizeh = int(options.size.split("x",1)[1])
        fsizew = int(options.framesize.split("x",1)[0])
        fsizeh = int(options.framesize.split("x",1)[1])
    except ValueError:
        print("Pleasi enter integer when specifying framerate/[frame]size.")
        os._exit(0)
    if fsizew > sizew or fsizeh > sizeh-1:
        print("Framesize too large!")
        os._exit(0)

    try:
        if options.tcpserv:
            if options.verbose:
                print("Running TCP server on {0}:{1}".format(options.interface, options.port))
                print("Playing movie {0}".format(options.filename))
            runTcpServer(options.interface, options.port, options.filename,
                         framerate, sizew ,sizeh, fsizew, fsizeh)
        else:
            runStdOut(options.filename, framerate, sizew, sizeh, fsizew, fsizeh)
    except KeyboardInterrupt:
        print("Ascii Player Quit.")
