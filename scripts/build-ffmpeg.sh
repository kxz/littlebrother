#!/bin/sh

pkg-config --exists libavformat
if [ $? != 0 ]; then
    apt-get build-dep ffmpeg
    FFMPEG_SRC=$(mktemp -d)
    cd $FFMPEG_SRC
    curl -s http://ffmpeg.org/releases/ffmpeg-2.7.2.tar.bz2 | tar xj
    cd ffmpeg-2.7.2
    ./configure
    make
    make install
else
    echo 'libavformat found; skipping ffmpeg build'
fi
