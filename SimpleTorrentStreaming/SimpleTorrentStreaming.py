#!/usr/bin/env python

"""
    Simple torrent streaming module
"""

from futures import ThreadPoolExecutor
from . utils import get_hash, get_media_file, make_status_readable, \
    make_download_status
import libtorrent as lt
import ConfigParser
import subprocess
import threading
import logging
import time
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] (%(threadName)-10s) %(message)s'
)


class TorrentStreamer(object):
    """
        Torrent Streaming service
    """
    def __init__(self, cfg):
        """
            Read config. Start session listening on default ports 6881, 6891
        """
        self.config = ConfigParser.ConfigParser()
        self.config.read([os.path.expanduser(cfg)])

        self.default_params = {'save_path': '/tmp'}

        self.session = getattr(lt, 'session')()
        self.session.listen_on(6881, 6891)
        self.session.start_dht()

        self.threaded_magnets = {}

    def get_blocking_magnet(self, magnet_, params=False):
        """
            Start downloading a magnet link
        """

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
            downloaded = handle.get_download_queue()
            total = handle.status().pieces
            return len(downloaded) > len(total) / 5  # Wait until we have 1/5

        if not params:
            params = self.default_params

        params['allocation'] = lt.storage_mode_t.storage_mode_sparse
        handle = lt.add_magnet_uri(self.session, str(magnet_), params)
        is_playing = False

        while not handle.is_seed():
            time.sleep(1)
            status_ = make_status_readable(handle.status())
            download_status = make_download_status(
                handle.get_download_queue(),
                handle.status().pieces
            )
            logging.debug(download_status)
            if handle.has_metadata():
                tinfo = handle.get_torrent_info()
                self.threaded_magnets[get_hash(magnet_)]['status'] = status_
                logging.debug(status_)

                file_ = get_media_file([fle.path for fle in tinfo.files()])
                self.threaded_magnets[get_hash(magnet_)]['file'] = file_
                stream_opt = self.threaded_magnets[get_hash(magnet_)]['stream']

                if stream_opt and file_:
                    set_streaming_priorities(handle)
                    if not is_playing:
                        is_playing = True
                        subprocess.Popen(['mplayer', '/tmp/{}'.format(file_)])

                if self.threaded_magnets[get_hash(magnet_)]['play'] \
                        and is_playable(file_, handle) and not is_playing:
                    is_playing = True
                    subprocess.Popen(['mplayer', '/tmp/{}'.format(file_)])

    def get_parallel_magnets(self, magnets, play=False, stream=False):
        """
            Parallelize magnet downloading.
        """
        for magnet_ in magnets:
            logging.info("Adding {} to download queue".format(magnet_))
            thread_ = threading.Thread(
                name="Downloading {}".format(get_hash(magnet_)),
                target=self.get_blocking_magnet,
                args=[str(magnet_)]
            )

            self.threaded_magnets[get_hash(magnet_)] = {
                'thread': thread_,
                'status': None,
                'file': None,
                'play': play,
                'stream': stream
            }

        with ThreadPoolExecutor(max_workers=4) as executor:
            for _, thread_ in self.threaded_magnets.items():
                executor.submit(thread_['thread'].run)

        return True

    def play_torrent(self, magnets):
        """
            Play a torrent file with mplayer
        """
        self.get_parallel_magnets(magnets, play=True)

    def stream_torrent(self, magnets):
        """
            Play a torrent file with mplayer
        """
        self.get_parallel_magnets(magnets, stream=True)
