# coding=utf-8
import pytest

from ascii_telnet_server.ascii_telnet_server import TimeBar


class TestTimeBar(object):
    def test_empty_timebar(self):
        tb = TimeBar(0, 10)
        assert tb._empty_timebar == "<        >"

    def test_long_timebar(self):
        tb = TimeBar(0, 100)
        assert tb._empty_timebar == "<                                " \
                                    "                                 " \
                                    "                                 >"

    def test_too_short_timebar(self):
        with pytest.raises(ValueError) as excinfo:
            TimeBar(0, 1)
            assert str(excinfo.values) == "This TimeBar is too short for these decorators: < o >"

    def test_short_timebar(self):
        tb = TimeBar(0, 3)
        assert tb._empty_timebar == "< >"

    def test_fancy_decorators(self):
        tb = TimeBar(0, 15, left_decorator="*~~*~~", right_decorator="Œ")
        assert tb._empty_timebar == "*~~*~~        Œ"

    def test_custom_spacer(self):
        tb = TimeBar(0, 15, spacer=".")
        assert tb._empty_timebar == "<.............>"

    def test_get_marker_position_easy(self):
        tb = TimeBar(100, 102)
        assert tb.get_marker_postion(0) == 0
        assert tb.get_marker_postion(1) == 1
        assert tb.get_marker_postion(10) == 10
        assert tb.get_marker_postion(20) == 20
        assert tb.get_marker_postion(30) == 30
        assert tb.get_marker_postion(40) == 40
        assert tb.get_marker_postion(50) == 50
        assert tb.get_marker_postion(99) == 99
        assert tb.get_marker_postion(100) == 100

    def test_get_marker_position_harder(self):
        tb = TimeBar(100, 100)
        assert tb.get_marker_postion(0) == 0
        assert tb.get_marker_postion(1) == 1
        assert tb.get_marker_postion(10) == 10
        assert tb.get_marker_postion(20) == 20
        assert tb.get_marker_postion(30) == 29
        assert tb.get_marker_postion(40) == 39
        assert tb.get_marker_postion(50) == 49
        assert tb.get_marker_postion(99) == 97
        assert tb.get_marker_postion(100) == 98

    def test_get_marker_position_small(self):
        tb = TimeBar(100, 10)
        assert tb.get_marker_postion(0) == 0
        assert tb.get_marker_postion(1) == 0
        assert tb.get_marker_postion(10) == 1
        assert tb.get_marker_postion(20) == 2
        assert tb.get_marker_postion(30) == 2
        assert tb.get_marker_postion(40) == 3
        assert tb.get_marker_postion(50) == 4
        assert tb.get_marker_postion(99) == 8
        assert tb.get_marker_postion(100) == 8

    def test_timebar_with_marker(self):
        tb = TimeBar(100, 102)

        assert len(tb.get_timebar(0)) == 102
        assert tb.get_timebar(0).index("o") == 1
        assert tb.get_timebar(0) == "<o                                                                                                   >"

        assert len(tb.get_timebar(10)) == 102
        assert tb.get_timebar(10).index("o") == 11
        assert tb.get_timebar(10) == "<          o                                                                                         >"

        assert len(tb.get_timebar(99)) == 102
        assert tb.get_timebar(99).index("o") == 100

        assert len(tb.get_timebar(100)) == 102
        assert tb.get_timebar(100).index("o") == 100

    def test_timebar_with_marker_short(self):
        tb = TimeBar(100, 8)

        assert len(tb.get_timebar(0)) == 8
        assert tb.get_timebar(0).index("o") == 1
        assert tb.get_timebar(0) == "<o     >"

        assert len(tb.get_timebar(10)) == 8
        assert tb.get_timebar(10).index("o") == 2
        assert tb.get_timebar(10) == "< o    >"

        assert len(tb.get_timebar(50)) == 8
        assert tb.get_timebar(50).index("o") == 4
        assert tb.get_timebar(50) == "<   o  >"

        assert len(tb.get_timebar(99)) == 8
        assert tb.get_timebar(99).index("o") == 6
        assert tb.get_timebar(99) == "<     o>"

        assert len(tb.get_timebar(100)) == 8
        assert tb.get_timebar(100).index("o") == 6
        assert tb.get_timebar(100) == "<     o>"

    def test_frame_num_larger_than_timebar_frame_count(self):
        tb = TimeBar(100, 102)
        bad_frame_timebar = tb.get_timebar(104)
        assert len(bad_frame_timebar) == 102
        assert bad_frame_timebar == "<                                                                                                   o>"


