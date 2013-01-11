"""
/*****************************************************************************
 * vlyc :: auth.py : youtube auth
 ****************************************************************************
 * Copyright (C) 2012-2013 Orochimarufan
 *
 * Authors:  Orochimarufan <orochimarufan.x3@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/
"""

from libyo.youtube import auth as yauth
from PyQt4 import QtCore, QtWebKit, QtGui
from libyo.util.util import sdict_parser
import os
import logging
logger = logging.getLogger(__name__)


def init():
    global path, ok
    path = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DataLocation)
    logger.info("Login data stored in %s" % path)
    
    client_secrets = os.path.join(path, "client_secrets.json")
    if not os.path.exists(client_secrets):
        logger.warning("client secrets not found: %s" % client_secrets)
        return 2
    yauth.init(client_secrets)
    ok = yauth.login(os.path.join(path, "lastlogin"))
    if ok:
        logger.info("Found credentials in %s" % yauth._cache)
        return 0
    return 1


def auth(parent):
    url = yauth.beginAuth()
    window = QtGui.QDialog(parent)
    window.resize(800, 600)
    web = QtWebKit.QWebView(window)
    u = QtCore.QUrl(url)
    #logger.info("Url in: '%s'\nUrl enc: '%s'\nUrl str: '%s'" % (url, u.toEncoded(), u.toString()))
    web.load(u)
    
    def load_callback(ok):
        if not ok:
            return
        if web.title().startswith("Success"):
            window.close()
            _, dct = web.title().rsplit(" ", 1)
            data = sdict_parser(dct)
            if "code" in data:
                yauth.finishAuth(data["code"])
            window.destroy()
    
    web.loadFinished.connect(load_callback)
    window.show()
