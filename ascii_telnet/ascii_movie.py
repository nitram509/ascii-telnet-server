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


class Frame(object):
    """
    One frame is 67 columns and 13 rows in effective size on screen.
    Use 'displayTime' to get the frame cycles this specific frame should
    be displayed.
    Use 'data' to get the 13 lines.
    """

    def __init__(self):
        self.displayTime = 1  # number of frame cycles to display this frame, default 1
        self.data = []  # 13 lines


class TimeBar(object):
    """
    TimeBar that appears at the bottom of the screen.
    """

    def __init__(self, duration, length, left_decorator="<", spacer=" ", right_decorator=">", marker="o"):
        """

        Args:
            duration (int): Frame count that this bar will be tracking
            length (int): Length in characters that the TimeBar will be on the screen
            left_decorator:
            spacer:
            right_decorator:
            marker:
        """
        self.length = length
        self.height = 1

        self.duration = duration

        self.spacer = spacer
        self.left_decorator = left_decorator
        self.right_decorator = right_decorator
        self.marker = marker

        self.internal_length = self.length - len(self.left_decorator) - len(self.right_decorator)

        if len(self.left_decorator + self.right_decorator + self.marker) > self.length:
            raise ValueError("This TimeBar is too short for these decorators: {} {} {}".format(self.left_decorator,
                                                                                               self.marker,
                                                                                               self.right_decorator))

    @property
    def _empty_timebar(self):
        time_bar_internals = "{0:{spacer}>{length}}".format("", spacer=self.spacer, length=self.internal_length)

        return "{tb.left_decorator}{internals}{tb.right_decorator}".format(internals=time_bar_internals, tb=self)

    def get_marker_postion(self, frame_num):
        """
        Return the index for the marker position on the TimeBar's internal length
        Args:
            frame_num: The Frame Number that the movie that the TimeBar marker should reflect

        Returns:
            int: index number for marker

        """

        return int(round(self.internal_length / self.duration * frame_num, 0))

    def get_timebar(self, frame_num):
        """
        Args:
            frame_num: The Frame Number that the movie that the TimeBar marker should reflect

        Returns:
            str: String representation of the TimeBar at the given Frame Number
                Example:  "<    o               >"
        """
        marker_pos = self.get_marker_postion(frame_num)

        if marker_pos >= self.internal_length:
            # Make sure we never overwrite the end decorator.
            marker_pos = self.internal_length - 1

        return self._empty_timebar[:marker_pos + len(self.left_decorator)] + \
               self.marker + \
               self._empty_timebar[marker_pos + len(self.right_decorator) + 1:]


class Movie(object):
    """
    A movie consists of frames and is empty by default.
    Movies are loaded from text files.
    Use 'dimension' to get the dimension of the movie.
    A movie only can be loaded once. A second try will fail.
    """

    def __init__(self, max_x, max_y):
        self._frames = []
        self._loaded = False
        self.dimension = (67, 13)
        f = Frame()
        f.data.append("No movie yet loaded.")
        self._frames.append(f)
        self.max_x = max_x
        self.max_y = max_y

    def loadMovie(self, filepath):
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
        if self._loaded:
            # we don't want to be loaded twice.
            return False
        self._frames = []
        current_frame = None
        max_lines_per_frame = self.dimension[1] + 1  # incl. meta data (time information)
        max_width = self.dimension[0]

        with open(filepath) as f:
            for counter, line in enumerate(f):
                time_metadata = -1
                if (counter % max_lines_per_frame) == 0:
                    time_metadata = int(line[0:3])
                if 0 < time_metadata <= 999:
                    current_frame = Frame()
                    current_frame.displayTime = time_metadata
                    self._frames.append(current_frame)
                else:
                    if current_frame:
                        # first strip every white character from the right
                        line = line.rstrip()
                        # second fill them with blanks, that they later
                        # automatically clear old lines from screen
                        line = line.ljust(max_width)
                        # to center the frame on the screen, we also add some
                        # BLANKs on the left side
                        line = line.rjust(max_width + (self.max_x - max_width) // 2)
                        current_frame.data.append(line)
        self._loaded = True
        return True

    def getEncFrames(self):
        """
        return a list with frames.
        Each frame carries its own display time, thats why it's 'encoded'.
        """
        return self._frames
