#!/usr/bin/env python
"""
    Utils
"""

# -*- coding: utf-8 -*-
import mimetypes
import urlparse
import re

BUFF_PERCENT = 5

def get_hash(magnet_):
    """
        return readable hash
    """
    magnet_p = urlparse.parse_qs(urlparse.urlparse(magnet_).query)
    return re.match('urn:btih:(.*)', magnet_p['xt'][0]).group(1)


def get_media_files(handle):
    """
        Get one only media file
    """
    def has_reserved_word(file_):
        """
            Check if has reserved words
        """
        reserved_words = ['sample']
        for reserved in reserved_words:
            if reserved in file_:
                return True
        return False

    def is_video(file_):
        """
            Check if is video in the mimetype
        """
        mime = mimetypes.guess_type(file_)
        if mime[0] and 'video' in mime[0]:
            return True
        return False

    def get_media_file(files):
        """
            Return files.
        """
        first_pass = [fil for fil in files if is_video(fil)]
        return filter(lambda x: not has_reserved_word(x), first_pass)[0]

    tinfo = handle.get_torrent_info()
    return get_media_file([fle.path for fle in tinfo.files()])


def make_status_readable(status):
    """
        Returns a readable status
    """
    if not status:
        return "None"
    return '%.2f%% (d: %.1f kb/s up: %.1f kB/s p: %d)\r' % (
        status.progress * 100, status.download_rate / 1000,
        status.upload_rate / 1000,
        status.num_peers
    )


def make_download_status(queue, pieces):
    """
        Make a queue readable.
    """
    def get_status(pieces, piece, downloading):
        """
            Nicely looking status.
        """
        status = "[ ]"
        if pieces[piece] is True:
            status = "[#]"
        if piece in downloading:
            status = "[D]"
        return status

    downloading = [piece['piece_index'] for piece in queue]
    pieces = dict(enumerate(pieces))
    return [get_status(pieces, piece, downloading) for piece in pieces]


def set_streaming_priorities(handle):
    """
        Set priorities for chunk
    """
    handle.set_sequential_download(True)
    pieces = dict(enumerate(handle.status().pieces))
    next_pieces = [key for key, val in pieces.iteritems() if val][:3]
    for piece in next_pieces:
        handle.piece_priority(piece, 7)


def is_playable(file_, handle):
    """
        Check if we've got 1/5th of the file
    """
    if not file_:
        return False
    status_ = make_status_readable(handle.status())
    return status_.progress > BUFF_PERCENT  # Wait until we have 1/5
