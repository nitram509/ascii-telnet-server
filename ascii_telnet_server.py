# coding=utf-8
# !/usr/bin/env python

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Copyright (c) 2008..2019, Martin W. Kirst All rights reserved.
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
  Version         : 0.2

  Can stream an ~20 minutes ASCII movie via Telnet emulation
  as stand alone server or via xinetd daemon.
  Tested with Python 2.6+, Python 3.5+

  Original art work : Simon Jansen ( http://www.asciimation.co.nz/ )
  Telnetification
  & Player coding   : Martin W. Kirst ( https://github.com/nitram509/ascii-telnet-server )

  Contributors
  Ryan Jarvis : Python3 update
  @ZenithalHourlyRate : Bad Apple movie, frame rate stabilization

"""
from __future__ import division, print_function

import os
import sys
from optparse import OptionParser

from ascii_telnet.ascii_movie import Movie
from ascii_telnet.ascii_player import VT100Player
from ascii_telnet.ascii_server import TelnetRequestHandler, ThreadedTCPServer


# constants ##########

SEPARATOR = "x"
DEFAULT_FRAME_SIZE = "67x13"
DEFAULT_SCREEN_SIZE = "80x24"
DEFAULT_FRAMERATE = 24
DEFAULT_INTERFACE = "0.0.0.0"
DEFAULT_PORT = 23

######################


def run_tcp_server(interface, port, filename, frame_rate, screen_width, screen_height, frame_with, frame_height):
    """
    Start a TCP server that a client can connect to that streams the output of
     Ascii Player

    Args:
        interface (str):  bind to this interface
        port (int): bind to this port
        filename (str): file name of the ASCII movie
        frame_rate (int): FPS of the movie
        screen_width (int): Width of the screen
        screen_height (int): Height of the screen (including timeline)
        frame_with (int): Width of the movie
        frame_height (int): Height of the movie
    """
    TelnetRequestHandler.filename = filename
    TelnetRequestHandler.framerate = frame_rate
    TelnetRequestHandler.screen_width = screen_width
    TelnetRequestHandler.screen_height = screen_height
    TelnetRequestHandler.movie_with = frame_with
    TelnetRequestHandler.movie_height = frame_height
    server = ThreadedTCPServer((interface, port), TelnetRequestHandler)
    server.serve_forever()


def run_std_out(filepath, frame_rate, screen_width, screen_height, frame_width, frame_height):
    """
    Stream the output of the Ascii Player to STDOUT
    Args:
        filepath (str): file path of the ASCII movie
        frame_rate (int): FPS of the movie
        screen_width (int): Width of the screen
        screen_height (int): Height of the screen (including timeline)
        frame_width (int): Width of the movie
        frame_height (int): Height of the movie
    """

    def draw_frame_to_stdout(screen_buffer):
        sys.stdout.write(screen_buffer.read().decode('iso-8859-15'))

    movie = Movie(screen_width, screen_height, frame_width, frame_height)
    movie.load(filepath)
    player = VT100Player(movie, frame_rate)
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
                      help=("Bind to this interface (default '%s', all interfaces)" % DEFAULT_INTERFACE),
                      default=DEFAULT_INTERFACE)
    parser.add_option("-p", "--port", dest="port", metavar="PORT",
                      help=("Bind to this port (default %d, Telnet)" % DEFAULT_PORT),
                      default=DEFAULT_PORT, type="int")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Verbose (default for TCP server)")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
                      help="Quiet! (default for STDIN STDOUT server)")
    parser.add_option("-r", "--framerate", dest="framerate", metavar="FPS",
                      help=("Set the framerate of the movie (default %d)" % DEFAULT_FRAMERATE))
    parser.add_option("-s", "--screen_size", dest="screen_size", metavar="WIDTHxHEIGHT",
                      help="Set the screen size of the movie (default %s). " % DEFAULT_SCREEN_SIZE +
                           "Including the timeline, so the maximum frame size is WIDTHx(HEIGHT-1) " +
                           "(default maximum 80x23)")
    parser.add_option("-S", "--frame_size", dest="frame_size", metavar="FRAME_WIDTHxFRAME_HEIGHT",
                      help="Set the movie's frame size (depending on the movie you are to play) " +
                           "(default %s)" % DEFAULT_FRAME_SIZE)
    parser.set_defaults(interface=DEFAULT_INTERFACE,
                        port=DEFAULT_PORT,
                        tcpserv=True,
                        verbose=True,
                        framerate=DEFAULT_FRAMERATE,
                        screen_size=DEFAULT_SCREEN_SIZE,
                        frame_size=DEFAULT_FRAME_SIZE)
    options = parser.parse_args()[0]

    if not (options.filename and os.path.exists(options.filename)):
        parser.exit(1, "Error, file not found! See --help for details.\n")

    if SEPARATOR not in options.frame_size:
        parser.exit(1, "Error, the frame size must follow the format WIDTHxHEIGHT, "
                       "whereas width and height are numbers.\n")

    if SEPARATOR not in options.screen_size:
        parser.exit(1, "Error, the screen size must follow the format WIDTHxHEIGHT, "
                       "whereas width and height are numbers.\n")

    if not str(options.framerate).isdigit():
        parser.exit(1, "Error, the framerate must be a number.\n")

    framerate = int(options.framerate)
    screen_width = int(DEFAULT_SCREEN_SIZE.split("x", 1)[0])
    screen_height = int(DEFAULT_SCREEN_SIZE.split("x", 1)[1])
    frame_width = int(DEFAULT_FRAME_SIZE.split("x", 1)[0])
    frame_height = int(DEFAULT_FRAME_SIZE.split("x", 1)[1])
    try:
        screen_sizes = str(options.screen_size).lower().split(SEPARATOR, 1)
        screen_width = int(screen_sizes[0].strip())
        screen_height = int(screen_sizes[1].strip())
        frame_sizes = str(options.frame_size).lower().split(SEPARATOR, 1)
        frame_width = int(frame_sizes[0].strip())
        frame_height = int(frame_sizes[1].strip())
    except ValueError:
        parser.exit(1, "Please enter integer when specifying screen size or frame size.\n")

    if frame_width > screen_width:
        parser.exit(1, "The frame width must equal or smaller than the screen width.\n")

    if frame_height > screen_height - 1:
        parser.exit(1, "The frame height must be smaller than the screen height-1.\n")

    try:
        if options.tcpserv:
            if options.verbose:
                print("Running TCP server on {0}:{1}".format(options.interface, options.port))
                print("Playing movie file {0}".format(options.filename))
            run_tcp_server(options.interface, options.port, options.filename,
                           framerate, screen_width, screen_height, frame_width, frame_height)
        else:
            run_std_out(options.filename, framerate, screen_width, screen_height, frame_width, frame_height)
    except KeyboardInterrupt:
        print("Quit.")
