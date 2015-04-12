#!/usr/bin/env python
"""
    Utils
"""

# -*- coding: utf-8 -*-
import mimetypes
import magnet


def get_hash(magnet_):
    """
        return readable hash
    """
    return magnet.url(magnet_).files[0]['hash']


def get_media_file(files):
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

    first_pass = [fil for fil in files if is_video(fil)]
    return filter(lambda x: not has_reserved_word(x), first_pass)[0]


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
