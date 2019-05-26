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

"""
The default frame rate to play a movie.
"""
DEFAULT_FRAMERATE = 15


class VT100Player(object):
    """
    Some escape codes used within VT100 Streams
    @see: http://ascii-table.com/ansi-escape-sequences-vt-100.php
    """
    ESC = chr(27)  # VT100 escape character constant
    JMPHOME = ESC + "[H"  # Move cursor to upper left corner
    CLEARSCRN = ESC + "[2J"  # Clear entire screen
    CLEARDOWN = ESC + "[J"  # Clear screen from cursor down

    def __init__(self, movie, framerate=DEFAULT_FRAMERATE):
        """
        Player class plays a movie.
        It also stores the current position.
        It exposes the all frame numbers in real values. Therefore not encoded.

        Args:
            movie (ascii_movie.Movie): Movie Object that the player will play.

        """
        self._movie = movie
        self._cursor = 0  # virtual cursor pointing to the current frame
        self._frame_count = 0
        self._framerate = int(framerate)  # type: int

        self._stopped = False

        self._clear_screen_setup_done = False

        for f in self._movie.frames:
            self._frame_count += f.display_time

        self.timebar = TimeBar(self._frame_count, self._movie.screen_width)

    def play(self):
        """
        Plays the movie

        The 'very long' 'if' condition is for the 
        stability of the frame rate

        If the actuall time(unpredictable) is not in the time window of the current frame,
        just skip this frame
        """
        self._stopped = False
        old_time = time.time()
        for frame in self._movie.frames:
            if self._stopped:
                return
            # now = time.time()
            # if (now - old_time) * self._framerate >= self._cursor and (
            #         now - old_time) * self._framerate < self._cursor + frame.display_time:
            self._cursor += frame.display_time
            self._load_frame(frame, self._cursor)
            time.sleep(frame.display_time / self._framerate)
            # else:
            #     """
            #     Skip playing this frame and continue as if
            #     it has been played
            #
            #     Due to 'time.sleep', the 'else' clause can only be reached
            #     when the second condition is violated
            #     """
            #     time.sleep(1/1000) # avoid high CPU load_movie_from_file
            #     self._cursor += frame.display_time

    def stop(self):
        """
        Stop the movie
        """
        self._stopped = True

    def _load_frame(self, frame, frame_cursor_pos):
        """
        Buffer the the frame and then call draw_frame to display it

        Args:
            frame (ascii_movie.Frame): frame data to display
            frame_cursor_pos (int):  what is the cursor position of the frame within the movie
        """
        screenbuf = BytesIO()
        if not self._clear_screen_setup_done:
            screenbuf.write(self.CLEARSCRN.encode())
            self._clear_screen_setup_done = True

        # center vertical, with respect to the time bar (like letter boxing)
        screenbuf.write(self._move_cursor(1, self._movie.top_margin))
        for line in frame.data:
            screenbuf.write((line + "\r\n").encode())

        self._update_timebar(screenbuf, frame_cursor_pos)

        # now rewind the internal buffer and fire the public event
        screenbuf.seek(0)
        self.draw_frame(screenbuf)

    def draw_frame(self, screen_buffer):
        """
        Public event method, which can be used to get new Screens.
        This must be implemented by the user.

        Args:
            screen_buffer:  its a file like object containing the VT100 screen buffer

        """
        raise NotImplementedError("You must specify how to draw the frame.")

    def _update_timebar(self, screen_buffer, frame_cursor_pos):
        """
        Writes at the bottom of the screen a line like this
        <.......o.....................>
        It should visualize a timeline with 'o' is the current position.

        Args:
            screen_buffer: file like object, where the data is written to
            frame_cursor_pos (int): current frame cursor position within the movie

        """
        # Move cursor to the bottom of the screen
        screen_buffer.write(self._move_cursor(1, self._movie.screen_height))

        screen_buffer.write(self.timebar.get_timebar(frame_cursor_pos).encode())

    def _move_cursor(self, x, y):
        """
        Send VT100 commands: go to position X,Y

        Args:
            x (int): x coordinate (starting at 1)
            y (int): y coordinate (starting at 1)

        Returns:
            str: the VT100 code as a string

        """
        if 0 >= x > self._movie.screen_width or 0 >= y > self._movie.screen_height:
            sys.stderr.write("Warning, coordinates out of range. ({0}, {1})\n".format(x, y))
            return "".encode()
        else:
            return (self.ESC + "[{0};{1}H".format(y, x)).encode()
