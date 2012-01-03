ASCII art movie Telnet player
=============================

Can stream an ~20 minutes ASCII movie via Telnet emulation
as stand alone server or via xinetd daemon. 

Tested with Python 2.3, Python 2.5, Python 2.7

Original art work : Simon Jansen [http://www.asciimation.co.nz/](http://www.asciimation.co.nz/)
Telnetification & Player coding   : Martin W. Kirst

Command line parameters
-----------------------

See program output:

	$ python ascii-telnet-server.py --help


Run as stand alone server
-------------------------

Simple call this Python script by using the sample movie file:

    $> python ascii-telnet-server.py --standalone -f sw1.txt
    Running TCP server on 0.0.0.0:23
    Playing movie sw1.txt
   

Run as xinetd program
---------------------

bar