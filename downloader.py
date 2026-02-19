# downloader.py
"""
YouTube Downloader - Main orchestrator for music and video downloads.
"""

from music_downloader import MusicDownloader
from video_downloader import VideoDownloader


class YouTubeDownloader:
    """
    Facade class that provides a unified interface for downloading
    YouTube content as either audio (with optional MP3 conversion)
    or video.
    """

    def __init__(self, music_folder, convert_to_mp3=True):
        """
        Initialize the downloader with a target folder and audio conversion setting.

        :param music_folder: Path where downloaded files will be saved.
        :param convert_to_mp3: If True, audio downloads are converted to MP3.
        """
        self.music_folder = music_folder
        self.convert_to_mp3 = convert_to_mp3
        self._music_downloader = MusicDownloader(music_folder, convert_to_mp3)
        self._video_downloader = VideoDownloader(music_folder)

    def download_music(self, url):
        """
        Download audio from a YouTube URL.

        :param url: YouTube video or music URL.
        :return: Dictionary with download result (success, filename, title, ...).
        """
        return self._music_downloader.download(url)

    def download_video(self, url):
        """
        Download video from a YouTube URL.

        :param url: YouTube video URL.
        :return: Dictionary with download result (success, filename, title).
        """
        return self._video_downloader.download(url)