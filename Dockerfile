FROM		ubuntu:14.04

RUN			apt-get update 
RUN			apt-get -y upgrade

RUN			apt-get -y install python3 python3-pip python3-dev
RUN			apt-get -y install libxml2-dev libxslt-dev zlib1g-dev libffi-dev

RUN			apt-get -y install libxss1 libappindicator1 libindicator7

RUN			apt-get -y install wget chromium-browser

RUN			apt-get -y install libnss3-dev libgconf2-4 libasound2 libpango1.0-0 fonts-liberation libcurl3 xdg-utils

RUN			apt-get -y install xvfb

RUN			wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
RUN			apt-get -y install unzip
RUN			unzip chromedriver_linux64.zip

RUN			chmod +x chromedriver
RUN			mv -f chromedriver /usr/local/share/chromedriver
RUN			ln -s /usr/local/share/chromedriver /usr/bin/chromedriver
RUN			ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver

RUN			pip3 install --upgrade pip
