# coding=utf-8

from ascii_telnet.ascii_movie_loader import load_movie_from_file
from ascii_telnet.ascii_movie import Movie
import os

TEST_FOLDER = "tests"

def test_max_line_length_is_treated_as_max_frame_width():
    movie = load_movie_from_file(os.path.join(TEST_FOLDER, "movie_frame_width_13_height_3.txt"))  # type: Movie
    assert movie.frame_width == 13


def test_frame_height_is_detected():
    movie = load_movie_from_file(os.path.join(TEST_FOLDER, "movie_frame_width_13_height_3.txt"))  # type: Movie
    assert movie.frame_height == 3


def test_spaces_dont_count_as_content_hence_frame_width_ignores_them():
    movie = load_movie_from_file(os.path.join(TEST_FOLDER, "movie_spaces_dont_count_as_content.txt"))  # type: Movie
    assert movie.frame_width == 3
