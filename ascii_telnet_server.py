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
"""
from __future__ import division, print_function

import os
import sys
from optparse import OptionParser

from ascii_telnet.ascii_movie import Movie
from ascii_telnet.ascii_player import VT100Player
from ascii_telnet.ascii_server import TelnetRequestHandler, ThreadedTCPServer


def runTcpServer(interface, port, filename):
    """
    Args:
        interface:  bind to this interface
        port: bind to this port
        filename: file name of the ASCII movie

    Returns:

    """
    TelnetRequestHandler.filename = filename
    server = ThreadedTCPServer((interface, port), TelnetRequestHandler)
    server.serve_forever()


def onNextFrameStdOut(screen_buffer):
    sys.stdout.write(screen_buffer.read().decode('iso-8859-15'))


def runStdOut(filename):
    """
    Args:
        filename: file name of the ASCII movie

    Returns:

    """

    movie = Movie(80, 24)
    movie.loadMovie(filename)
    player = VT100Player(movie)
    sys.stdout.write(player.CLEARSCRN)
    player.onNextFrame = onNextFrameStdOut
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
    parser.set_defaults(interface="0.0.0.0",
                        port=23,
                        tcpserv=True,
                        verbose=True, )
    (options, args) = parser.parse_args()

    if not (options.filename and os.path.exists(options.filename)):
        parser.exit(1, "Error, file not found! See --help for details.\n")

    if options.tcpserv:
        if options.verbose:
            print("Running TCP server on {0}:{1}".format(options.interface, options.port))
            print("Playing movie {0}".format(options.filename))
        runTcpServer(options.interface, options.port, options.filename)
    else:
        runStdOut(options.filename)

    sys.exit(0)
