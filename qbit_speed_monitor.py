import time
import getpass
from urllib.error import HTTPError, URLError

from api import get_torrents
from monitor import TorrentMonitor


CHECK_INTERVAL = 30


def format_speed(speed):
    units = ["B/s", "KiB/s", "MiB/s", "GiB/s"]
    speed = float(speed)

    for unit in units:
        if speed < 1024:
            return f"{speed:.1f} {unit}"
        speed /= 1024

    return f"{speed:.1f} TiB/s"


def choose_torrent(torrents):
    if not torrents:
        print("No downloading torrents found.")
        return None

    print("\nDownloading torrents:\n")

    for i, torrent in enumerate(torrents, 1):
        print(
            f"{i}. {torrent['name']}\n"
            f"   Speed: {format_speed(torrent['dlspeed'])} | "
            f"Seeds: {torrent['num_seeds']}/{torrent['num_complete']} | "
            f"Peers: {torrent['num_leechs']}/{torrent['num_incomplete']}\n"
        )

    while True:
        try:
            choice = int(input("Select torrent number: "))
            if 1 <= choice <= len(torrents):
                return torrents[choice - 1]["hash"]
        except ValueError:
            pass

        print("Invalid selection.")


def main():
    print("=" * 60)
    print("qBittorrent Smart Speed Monitor")
    print("=" * 60)
    print()
    print("Threshold:       2 MiB/s")
    print("Low-speed time:  5 minutes")
    print("Cooldown:        15 minutes")
    print()

    api_key = getpass.getpass("Enter your qBittorrent API key: ")

    try:
        torrents = get_torrents(api_key)
    except Exception as e:
        print("\nCould not connect to qBittorrent.")
        print("Check that WebUI is enabled on 127.0.0.1:8080.")
        print(f"Error: {e}")
        input("\nPress Enter to exit...")
        return

    torrent_hash = choose_torrent(torrents)

    if not torrent_hash:
        input("\nPress Enter to exit...")
        return

    monitor = TorrentMonitor(torrent_hash, api_key)

    print("\nMonitoring started.")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            torrent = monitor.get_torrent()

            if torrent is None:
                print("\nTorrent is no longer downloading.")
                print("It may have finished.")
                break

            now = time.time()
            speed = torrent["dlspeed"]

            monitor.record_speed(speed, now)
            average_speed = monitor.get_average_speed()

            print(
                f"[{time.strftime('%H:%M:%S')}] "
                f"Current: {format_speed(speed):>12} | "
                f"5-min avg: {format_speed(average_speed):>12} | "
                f"Seeds: {torrent['num_seeds']}/{torrent['num_complete']} | "
                f"Peers: {torrent['num_leechs']}/{torrent['num_incomplete']}"
            )

            if monitor.should_reannounce(now):
                print("\n>>> Speed has been below 2 MiB/s for 5 minutes.")
                print(">>> Forcing tracker reannounce...")

                monitor.reannounce()

                print(">>> Reannounce sent.")
                print(">>> New peers will be allowed to connect normally.\n")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nStopped.")
            break

        except (HTTPError, URLError, Exception) as e:
            print(f"\nAPI error: {e}")
            print("Retrying in 30 seconds...\n")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()