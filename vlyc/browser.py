"""
----------------------------------------------------------------------
- vlyc::browser : The Browser that displays the Youtube HP
----------------------------------------------------------------------
- Copyright (C) 2011-2013 Orochimarufan
-                Authors: Orochimarufan <orochimarufan.x3@gmail.com>
-
- This program is free software: you can redistribute it and/or modify
- it under the terms of the GNU General Public License as published by
- the Free Software Foundation, either version 3 of the License, or
- (at your option) any later version.
-
- This program is distributed in the hope that it will be useful,
- but WITHOUT ANY WARRANTY; without even the implied warranty of
- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
- GNU General Public License for more details.
-
- You should have received a copy of the GNU General Public License
- along with this program.  If not, see <http://www.gnu.org/licenses/>.
----------------------------------------------------------------------
"""
from __future__ import absolute_import, unicode_literals, division

import os
import logging

from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit

from libyo.youtube.url import regexp as watch_regexp

from . import vlyc2png

logger = logging.getLogger(__name__)


class WebBrowser(QtGui.QWidget):
    watch = QtCore.Signal("QString")
    
    def __init__(self, parent=None):
        super(WebBrowser, self).__init__(parent)
        
        self.m_jar = CookieJar(None, os.path.join(
            QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.CacheLocation),
            "cookies.txt"))
        if os.path.exists(self.m_jar.m_cookieFile):
            self.m_jar.load()
            self.m_jar.clean()
        else:
            d = os.path.dirname(self.m_jar.m_cookieFile)
            if not os.path.exists(d):
                os.makedirs(d)
        
        self.m_nam = QtNetwork.QNetworkAccessManager()
        self.m_nam.setCookieJar(self.m_jar)
        
        self.webview = QtWebKit.QWebView(self)
        self.webview.setObjectName("webview")
        
        self.webview.page().setNetworkAccessManager(self.m_nam)
        self.webview.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        
        QtGui.QHBoxLayout(self)
        self.layout().addWidget(self.webview)
        
        icon_pixmap = QtGui.QPixmap.fromImage(QtGui.QImage.fromData(vlyc2png.data))
        self.setWindowIcon(QtGui.QIcon(icon_pixmap))
        self.setWindowTitle("[VLYC Browser]")
        
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.resize(1080, 600)
    
    def on_webview_linkClicked(self, url):
        if watch_regexp.match(url.toString()):
            self.watch.emit(url.toString())
        else:
            self.webview.load(url)
    
    def on_webview_titleChanged(self, new):
        self.setWindowTitle("%s - [VLYC Browser]" % new)
    
    def saveCookies(self):
        self.m_jar.save()
    
    def load(self, url):
        qurl = QtCore.QUrl(url)
        self.webview.load(qurl)
    
    def forceStopNetwork(self):
        QtNetwork.QNetworkSession(self.m_nam.configuration()).stop()


class CookieJar(QtNetwork.QNetworkCookieJar):
    """ Simple File-based QNetworkCookieJar """
    def __init__(self, parent, cookieFile):
        super(CookieJar, self).__init__(parent)
        
        self.m_cookieFile = cookieFile
    
    def clean(self):
        cookies = self.allCookies()
        
        now = QtCore.QDateTime.currentDateTime()
        for cookie in cookies:
            if cookie.expirationDate() < now:
                logger.getChild("CookieJar").info("Cookie Expired: %s (%s)" %
                    (cookie.toRawForm(QtNetwork.QNetworkCookie.NameAndValueOnly),
                     cookie.expirationDate().toString()))
                cookies.remove(cookie)
        
        self.setAllCookies(cookies)
    
    def save(self):
        self.clean()
        
        with open(self.m_cookieFile, "wb") as fp:
            for cookie in self.allCookies():
                fp.write(cookie.toRawForm())
                fp.write(b"\n")
    
    def load(self):
        cookies = list()
        
        with open(self.m_cookieFile, "rb") as fp:
            for line in fp:
                if not line[:-1]:
                    continue
                cookies.extend(QtNetwork.QNetworkCookie.parseCookies(line[:-1]))
        
        self.setAllCookies(cookies)
