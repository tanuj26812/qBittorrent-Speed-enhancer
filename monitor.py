from collections import deque
import time

from api import api_post, get_torrents


CHECK_INTERVAL = 30
LOW_SPEED_THRESHOLD = 2 * 1024 * 1024
LOW_SPEED_DURATION = 5 * 60
REANNOUNCE_COOLDOWN = 15 * 60


class TorrentMonitor:

    def __init__(self, torrent_hash, api_key):
        self.torrent_hash = torrent_hash
        self.api_key = api_key

        self.speed_history = deque()
        self.last_reannounce = 0

    def get_torrent(self):
        torrents = get_torrents(self.api_key)

        return next(
            (torrent for torrent in torrents
             if torrent["hash"] == self.torrent_hash),
            None
        )

    def record_speed(self, speed, now=None):
        if now is None:
            now = time.time()

        self.speed_history.append((now, speed))

        while (
            self.speed_history
            and now - self.speed_history[0][0] > LOW_SPEED_DURATION
        ):
            self.speed_history.popleft()

    def get_average_speed(self):
        if not self.speed_history:
            return 0

        return sum(
            speed for _, speed in self.speed_history
        ) / len(self.speed_history)

    def should_reannounce(self, now=None):
        if now is None:
            now = time.time()

        if not self.speed_history:
            return False

        average_speed = self.get_average_speed()

        return (
            len(self.speed_history) >= 5
            and now - self.speed_history[0][0] >= LOW_SPEED_DURATION
            and average_speed < LOW_SPEED_THRESHOLD
            and now - self.last_reannounce >= REANNOUNCE_COOLDOWN
        )

    def reannounce(self):
        api_post(
            "torrents/reannounce",
            {"hashes": self.torrent_hash},
            self.api_key
        )

        self.last_reannounce = time.time()
        self.speed_history.clear()