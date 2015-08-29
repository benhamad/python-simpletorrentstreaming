#!/usr/bin/env python

"""
    Simple torrent streaming module
"""

from concurrent.futures import ThreadPoolExecutor
from . utils import *
import libtorrent as lt
import subprocess
import threading
import logging
import time
import sys


logging.basicConfig(
        level=logging.DEBUG,
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
        self.default_params = {'save_path': '/tmp'}

        self.session = getattr(lt, 'session')()
        self.session.listen_on(6881, 6891)
        self.session.start_dht()

        self.threaded_magnets = {}

    def get_blocking_magnet(self, magnet_, params=False, player="mplayer"):
        """
            Start downloading a magnet link
        """

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
                file_ = get_media_files(handle)
                stream_opt = self.threaded_magnets[get_hash(magnet_)]['stream']

                self.threaded_magnets[get_hash(magnet_)]['status'] = status_
                self.threaded_magnets[get_hash(magnet_)]['file'] = file_

                logging.debug(self.threaded_magnets[get_hash(magnet_)])

                if not file_ or is_playing or not stream_opt:
                    return

                if stream_opt:
                    set_streaming_priorities(handle)

                is_playing = True
                subprocess.Popen([player, '/tmp/{}'.format(file_)])

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


def main():
    import argparse
    parser = argparse.ArgumentParser("stream_torrent")
    parser.add_argument('magnet', metavar='magnet', type=str, nargs='+',
                               help='Magnet link to stream')
    args = parser.parse_args()
    
    """
        Play a torrent.
    """
    streamer = TorrentStreamer('')
    for magnet in args.magnet:
        streamer.stream_torrent(magnet)

if __name__ == "__main__":
    main()
