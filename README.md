VideoLan YouTube Client
=======================
An installed YouTube Client  
With Media Playback based on libvlc  

### Features
* Watch YouTube Videos
* Supports Quality selection
* Supports Subtitles
* Plays local media, too
* VLC-like interface

### Future Plans
* \[maybe\] Annotation support
* Playlists
* YouTube Video Search
* YouTube User Login
* YouTube Subscriptions
* Rate/Comment/Subscribe

#### Files
*vlyc2.py* is the main entry-point. (you can also use vlyc.\_\_main\_\_ or -m vlyc)  
*freeze.py* is used to build executables.  
*misc/* contains testing and misc stuff

Dependencies
------------

### Required
* python (3.2+ recommended, **SHOULD** work on other versions)
* libyo (http://github.com/Orochimarufan/libyo/)
* PyQt4
* libvlc

#### Note:
The Ubuntu libvlc 1.1 seems to have some problem.  
Please use latest 2.0 builds (Ubuntu PPA: 'ppa:videolan/stable-daily')  

### Recommended
* lxml (http://lxml.de)
* readline support (Included in Linux Python; Windows: http://github.com/pyreadline/pyreadline)
* regex (http://pypi.python.prg/pypi/regex)

Copyright & License
-------------------
I'd rather not have to deal with it...

### Copyright
This Software is &copy; 2010-2013 by Orochimarufan  
This Software contains parts of VLC Media Player code &copy; by the VideoLAN Team  

### License
    VideoLan Youtube Client
    Copyright (C) 2010-2013 Orochimarufan
                  1996-2013 the VideoLAN Team
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

