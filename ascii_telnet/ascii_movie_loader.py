# coding=utf-8
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Copyright (c) 2019, Martin W. Kirst All rights reserved.
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

from ascii_movie import Frame, Movie


def load_movie_from_file(filepath):
    """
    Loads the ASCII movie from given text file into memory
    using an textual encoded format, like described on web site
    http://www.asciimation.co.nz/asciimation/ascii_faq.html

    TL;DR:

    - web site states frame size is 67x14 chars -- this loader does auto-detect width and height
    - lines are separated with \n
    - first line must be a number telling delay in number of frames

    Args:
        filepath (str): Path to Ascii Movie Data
    """
    movie = Movie()
    current_frame = Frame()
    max_line_length = 0
    lines_per_frame = 0
    left_margin = 0
    _frame_width = 0
    found_first_time_marker = False
    found_first_time_marker_line_num = 0
    with open(filepath) as f:
        for line_num, line in enumerate(f):
            # First strip every white character from the right
            # The amount of white space can be variable
            line = line.rstrip()
            max_line_length = max(max_line_length, len(line))
            if lines_per_frame == 0:
                if line.isdigit():
                    if not found_first_time_marker:
                        found_first_time_marker = True
                        current_frame = Frame(int(line))
                        found_first_time_marker_line_num = line_num
                    else:
                        lines_per_frame = line_num - found_first_time_marker_line_num

            time_metadata = None
            if lines_per_frame > 0 and line_num % lines_per_frame == 0:
                time_metadata = int(line)

            if time_metadata is not None:
                current_frame = Frame(display_time=time_metadata)
                movie.frames.append(current_frame)
            else:
                # Second fill line out with blanks so that any previous
                # characters are overwritten
                line = line.ljust(_frame_width)
                # Third center the frame on the screen
                line = line.rjust(left_margin + _frame_width)
                current_frame.data.append(line)
    movie.frame_width = max_line_length
    movie.frame_height = lines_per_frame - 1
    return movie
