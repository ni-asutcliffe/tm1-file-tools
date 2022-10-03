from pathlib import Path

from tm1filetools.files.text import TM1TextFile


def test_read_and_write(test_folder):

    f = TM1TextFile(Path.joinpath(test_folder, "platypus.sub"))

    assert f.read() == ""

    f.write("some text")

    assert f.read() == "some text"
