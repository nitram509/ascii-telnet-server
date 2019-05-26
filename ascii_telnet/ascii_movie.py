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


class Frame(object):
    def __init__(self, display_time=1):
        """
        One frame is typically 67 columns and 13 rows in effective size on screen.

        Use 'data' to get the lines.

        Args:
            display_time (int): the frame cycles this specific frame should be
                                 displayed (15 cycles per second).
        """
        self.display_time = display_time
        self.data = []  # frame lines


class TimeBar(object):
    height = 1

    def __init__(self, duration, length, left_decorator=u"<", spacer=u" ", right_decorator=u">", marker=u"o"):
        """
        TimeBar that appears at the bottom of the screen.

        Args:
            duration (int): Frame count that this bar will be tracking
            length (int): Length in characters that the TimeBar will be on the screen
            left_decorator (str): Decorator on the left side
            spacer (str): Spacer in between left and right decorators
            right_decorator (str): Decorator on the right side
            marker (str): Marker for position in Ascii Movie
        """
        self.length = length

        self.duration = duration

        self.spacer = spacer
        self.left_decorator = left_decorator
        self.right_decorator = right_decorator
        self.marker = marker

        self.internal_length = self.length - len(self.left_decorator) - len(self.right_decorator)

        if len(self.left_decorator + self.right_decorator + self.marker) > self.length:
            raise ValueError("This TimeBar is too short for these decorators: {0} {1} {2}".format(self.left_decorator,
                                                                                               self.marker,
                                                                                               self.right_decorator))

    @property
    def _empty_timebar(self):
        time_bar_internals = u"{0:{spacer}>{length}}".format(u"", spacer=self.spacer, length=self.internal_length)

        return u"{tb.left_decorator}{internals}{tb.right_decorator}".format(internals=time_bar_internals, tb=self)

    def get_marker_position(self, frame_num):
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
        marker_pos = self.get_marker_position(frame_num)

        if marker_pos >= self.internal_length:
            # Make sure we never overwrite the end decorator.
            marker_pos = self.internal_length - 1

        return self._empty_timebar[:marker_pos + len(self.left_decorator)] + \
               self.marker + \
               self._empty_timebar[marker_pos + len(self.right_decorator) + 1:]


class Movie(object):
    # TODO: screen width and height should be derived from frame size per default, no need for configuration
    # TODO: try to be smart and determine frame height and width as well automatically
    def __init__(self, screen_width=80, screen_height=24, frame_width=0, frame_height=0):
        """
        A Movie object consists of frames and is empty by default.

        Args:
            screen_width (int): Screen width
            screen_height (int): Screen height (Including the timebar)
            frame_width (int): Movie width, if value < 0  means auto determine frame width
            frame_height (int): Movie height
        """
        self.frames = []

        self.frame_width = frame_width  # type: int
        self.frame_height = frame_height  # type: int

        f = Frame()
        f.data.append("No movie yet loaded.")
        self.frames.append(f)

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.left_margin = (self.screen_width - self.frame_width) // 2
        self.top_margin = (self.screen_height - self.frame_height - TimeBar.height) // 2
