Contents
========

AntiFlashPlayer
---------------
File: `antiflashplayer.py`  
A tool to playback Youtube Videos w/o Flash Player

YouFeed
-------
File: `youfeed.py`  
A tool to batch-download Playlists for later viewing.  
This tool was NOT created to pirate Youtube content.

VLYC
----
File: `vlyc2.py`  
A libvlc based MediaPlayer that supports Youtube Videos and Quality Selection

### Future Plans
* \[maybe\] annotations
* playlist playback
* Youtube search interface
* Youtube User Login (rate/comment/subscribe)

Others
------
File: `old/*`  
Old Stuff and tests

File: `testPlayer.py`  
commandline MediaPlayer using the libvlc api and vlyc Player class

Dependencies
============

Required
--------
* python (3.2+ recommended, **SHOULD** work on other versions)
* libyo (http://github.com/Orochimarufan/libyo/)

Required for VLYC:
------------------
* PyQt4
* libvlc

#### Note:
The Ubuntu libvlc 1.1 seems to have some problem.  
Please use latest 2.0 builds (Ubuntu PPA: 'ppa:videolan/stable-daily')

Recommended
-----------
* lxml (http://lxml.de)
* readline support (Included in Linux Python; Windows: http://github.com/pyreadline/pyreadline)
* regex (http://pypi.python.prg/pypi/regex)

Official Stuff
==============

Copyright
---------
This Software is &copy; 2010-2012 by Orochimarufan  
Parts of VLYC are taken from VLC Sources (c) by the VideoLAN Team  

License
-------

<div style="font-family: monospace">
Youtube Tools, including AFP, VLYC, YouFeed and others<br>
Copyright (C) 2011-2012 Orochimarufan<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
1996-2012 the VideoLan Team (parts of VLYC)<br>
<br>
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.<br>
<br>
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.<br>
<br>
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.<br>
</div>
