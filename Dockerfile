FROM		ubuntu:14.04

RUN			apt-get update 
RUN			apt-get -y upgrade

RUN			apt-get -y install xvfb vim wget chromium-browser

RUN			wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
RUN			apt-get -y install unzip
RUN			unzip chromedriver_linux64.zip

RUN			chmod +x chromedriver
RUN			mv -f chromedriver /usr/local/share/chromedriver
RUN			ln -s /usr/local/share/chromedriver /usr/bin/chromedriver
RUN			ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver

