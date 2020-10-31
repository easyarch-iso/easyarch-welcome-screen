# Author: Asif Mahmud Shimon
# Date: 21 Oct 2020
# License: GPLv2

CP=cp -rfv
MKDIR=mkdir -pv
MKEXE=chmod +x
DESTDIR=

all:
	@echo Run make install to install the package

install:
	$(MKDIR) $(DESTDIR)/usr/bin
	$(MKDIR) $(DESTDIR)/usr/share/easyarch-welcome
	$(MKDIR) $(DESTDIR)/usr/share/icons/hicolor/48x48/apps
	$(MKDIR) $(DESTDIR)/usr/share/applications
	$(MKDIR) $(DESTDIR)/etc/skel/.config/autostart
	$(CP) WelcomeScreen.py $(DESTDIR)/usr/bin/welcome-screen
	$(MKEXE) $(DESTDIR)/usr/bin/welcome-screen
	$(CP) images $(DESTDIR)/usr/share/easyarch-welcome/
	$(CP) images/icon-48x48.png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps/welcome-screen.png
	$(CP) ui $(DESTDIR)/usr/share/easyarch-welcome/
	$(CP) welcome-screen.desktop $(DESTDIR)/usr/share/applications/
	$(CP) welcome-screen.desktop $(DESTDIR)/etc/skel/.config/autostart/
	$(MKEXE) $(DESTDIR)/usr/share/applications/welcome-screen.desktop
	$(MKEXE) $(DESTDIR)/etc/skel/.config/autostart/welcome-screen.desktop
	$(CP) LICENSE $(DESTDIR)/usr/share/easyarch-welcome/
	$(CP) requirements.txt $(DESTDIR)/usr/share/easyarch-welcome/
	$(CP) README.org $(DESTDIR)/usr/share/easyarch-welcome/
