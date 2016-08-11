FROM		ubuntu:14.04

RUN			apt-get update 
RUN			apt-get -y upgrade

RUN			apt-get -y install xvfb vim wget chromium-browser x11vnc

RUN			wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
RUN			apt-get -y install unzip
RUN			unzip chromedriver_linux64.zip

RUN			chmod +x chromedriver
RUN			mv -f chromedriver /usr/local/share/chromedriver
RUN			ln -s /usr/local/share/chromedriver /usr/bin/chromedriver
RUN			ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver

RUN apt-get update -y && \
    apt-get install -y git python python-numpy unzip openbox geany menu && \
    cd /root && git clone https://github.com/kanaka/noVNC.git && \
    cd noVNC/utils && git clone https://github.com/kanaka/websockify websockify && \
    cd /root && \
    chmod 0755 /startup.sh && \
    apt-get autoclean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*
