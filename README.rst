==================================
Simple libtorrent streaming module
==================================

Simple libtorrent-based bittorrent streaming module

This is a small-as-it-gets python library able to handle
multiple bittorrent downloads and bittorrent streaming
(even multiple bittorrent streaming, theoretically, but who whould want that?)

Dependences
-----------
Requires libtorrent for python2 to be installed.

In debian and derivatives, this is accomplished by:

::

    apt-get install python-libtorrent

* Free software: GPL 2+
* Documentation: https://SimpleTorrentStreaming.readthedocs.org.

Features
--------

* Play torrents in stream with mplayer
* Very few lines of code
* Multiple download of torrents

Usage
-----

::

    from SimpleTorrentStreaming import SimpleTorrentStreaming 

Or, if you only want to play a torrent with mplayer:

::

    stream_torrent "<magnet_link>"
