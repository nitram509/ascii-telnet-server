# coding=utf-8
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
from __future__ import division, print_function

import sys
import time
from io import BytesIO

from ascii_telnet.ascii_movie import TimeBar


class VT100Player(object):
    """
    Player class plays a movie. Offers higher methods for play, stop,
    fast forward and rewind on the movie. It also stores the current
    position.
    It exposes the all frame numbers in real values. Therefore not encoded.
    """

    """
    Some escape codes used within VT100 Streams
    @see: http://ascii-table.com/ansi-escape-sequences-vt-100.php
    """
    ESC = chr(27)  # VT100 escape character constant
    JMPHOME = ESC + "[H"  # Move cursor to upper left corner
    CLEARSCRN = ESC + "[2J"  # Clear entire screen
    CLEARDOWN = ESC + "[J"  # Clear screen from cursor down

    def __init__(self, movie):
        self._movie = movie
        self._movCursor = 0  # virtual cursor pointing to the current frame
        self._maxFrames = 0

        self._stopped = False

        for f in self._movie.getEncFrames():
            self._maxFrames += f.displayTime

        self.timebar = TimeBar(self._maxFrames, self._movie.maxX)

    def getDuration(self):
        """
        return the number of seconds this movie is playing
        """
        return self._maxFrames // 15  # 15 frames per second

    def play(self):
        """
        plays the movie
        """
        for frame in self._movie.getEncFrames():
            if self._stopped:
                return
            self._movCursor += frame.displayTime
            self._onNextFrameInternal(frame, self._movCursor)
            time.sleep(frame.displayTime / 15)

    def stop(self):
        self._stopped = True

    def _onNextFrameInternal(self, frame, frame_pos):
        """
        internal event, happen when next frame should be drawn
        """
        screenbuf = BytesIO()
        if frame_pos <= 1:
            screenbuf.write(self.CLEARSCRN)
        # center vertical, with respect to the time bar
        y = (self._movie.maxY - self._movie.dimension[1] - self.timebar.height) // 2

        screenbuf.write(self._move_cursor(1, y))
        for line in frame.data:
            screenbuf.write((line + "\r\n").encode())

        self._update_timebar(screenbuf, frame_pos)

        # now rewind the internal buffer and fire the public event
        screenbuf.seek(0)
        self.onNextFrame(screenbuf)

    def onNextFrame(self, screen_buffer):
        """
        Public event method, which can be used to get new Screens.

        Args:
            screen_buffer:  its a file like object containing the VT100 screen buffer

        Returns:

        """
        pass

    def _update_timebar(self, screen_buffer, current_frame_pos):
        """
        Writes at the bottom of the screen a line like this
        <.......o.....................>
        It should visualize a timeline with 'o' is the current position.

        Args:
            screen_buffer: file like object, where the data is written to
            current_frame_pos: current cursor position on frame

        Returns:

        """
        screen_buffer.write(self._move_cursor(1, self._movie.maxY))
        screen_buffer.write(self.timebar.get_timebar(current_frame_pos).encode())

    def _move_cursor(self, x, y):
        """
        Send VT100 commands: goto position X,Y

        Args:
            x (int): x coordinate (starting at 1)
            y (int): y coordinate (starting at 1)

        Returns:
            str: the VT100 code as a string

        """
        if 0 >= x > self._movie.maxX or 0 >= y > self._movie.maxY:
            sys.stderr.write("Warning, coordinates out of range. ({}, {})\n".format(x, y))
            return
        else:
            return (self.ESC + "[{0};{1}H".format(y, x)).encode()
