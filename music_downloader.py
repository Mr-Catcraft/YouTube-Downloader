# music_downloader.py
"""
Music (audio) downloader module. Handles downloading, metadata embedding,
optional conversion to MP3, and lyrics extraction from subtitles.
"""

import io
import os
from pathlib import Path

import requests
import yt_dlp
import av
from PIL import Image
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, USLT, APIC


class MusicDownloader:
    """
    Downloads audio from YouTube, embeds metadata (title, artist, album, cover, lyrics),
    and optionally converts to MP3.
    """

    def __init__(self, music_folder, convert_to_mp3=True):
        """
        :param music_folder: Directory where audio files will be saved.
        :param convert_to_mp3: If True, convert downloaded M4A to MP3 and delete the original.
        """
        self.music_folder = Path(music_folder)
        self.music_folder.mkdir(exist_ok=True)
        self.convert_to_mp3 = convert_to_mp3

        # yt-dlp options for audio download
        self.ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'noplaylist': True,
            'writethumbnail': False,          # we fetch thumbnail manually
            'writeautomaticsub': False,
            'writesubtitles': False,
            'outtmpl': str(self.music_folder / '%(title)s.%(ext)s'),
            'quiet': True,
        }

    def _get_final_path(self, info):
        """
        Generate the final file path using yt-dlp's filename template.

        :param info: info dictionary from yt-dlp.
        :return: Path object pointing to the downloaded file.
        """
        return self.music_folder / Path(
            yt_dlp.YoutubeDL({'outtmpl': self.ydl_opts['outtmpl']}).prepare_filename(info)
        ).name

    @staticmethod
    def _get_lyrics_text(info):
        """
        Extract lyrics from automatic captions or subtitles if available.

        :param info: info dictionary from yt-dlp.
        :return: Lyrics as a string, or None if not found.
        """
        lyrics_url = None
        # Try automatic captions first
        if 'automatic_captions' in info and 'en' in info['automatic_captions']:
            for fmt in info['automatic_captions']['en']:
                if fmt.get('ext') == 'vtt':
                    lyrics_url = fmt['url']
                    break
            if not lyrics_url and info['automatic_captions']['en']:
                lyrics_url = info['automatic_captions']['en'][0]['url']
        # Fallback to manual subtitles
        elif 'subtitles' in info and 'en' in info['subtitles']:
            for fmt in info['subtitles']['en']:
                if fmt.get('ext') == 'vtt':
                    lyrics_url = fmt['url']
                    break
            if not lyrics_url and info['subtitles']['en']:
                lyrics_url = info['subtitles']['en'][0]['url']

        if lyrics_url:
            try:
                resp = requests.get(lyrics_url, timeout=10)
                if resp.status_code == 200:
                    lines = []
                    for line in resp.text.splitlines():
                        # Skip timestamps and header lines
                        if '-->' not in line and line.strip() and not line.startswith(
                                ('WEBVTT', 'Kind:', 'Language:', 'NOTE')):
                            lines.append(line.strip())
                    return '\n'.join(lines)
            except Exception:
                pass
        return None

    def _embed_all(self, m4a_path, info):
        """
        Embed metadata (title, artist, album, year, cover, lyrics) into an M4A file.

        :param m4a_path: Path to the downloaded M4A file.
        :param info: info dictionary from yt-dlp.
        """
        try:
            audio = MP4(str(m4a_path))
            if not audio.tags:
                audio.add_tags()
            tags = audio.tags

            # Basic tags
            tags["\xa9nam"] = [info.get('title', 'Unknown')]
            tags["\xa9ART"] = [info.get('artist') or info.get('uploader', 'Unknown Artist')]
            tags["\xa9alb"] = [info.get('album', 'Unknown Album')]
            if 'upload_date' in info:
                tags["\xa9day"] = [info['upload_date'][:4]]

            # Cover art
            cover_data = None
            cover_fmt = None
            if info.get('thumbnails'):
                thumb_url = info['thumbnails'][-1]['url']
                resp = requests.get(thumb_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.content
                    # Check if thumbnail is WebP, convert to JPEG
                    if thumb_url.lower().endswith('.webp') or (data[:4] == b'RIFF' and b'WEBP' in data[:12]):
                        img = Image.open(io.BytesIO(data))
                        jpg_io = io.BytesIO()
                        img.convert('RGB').save(jpg_io, format='JPEG')
                        cover_data = jpg_io.getvalue()
                        cover_fmt = MP4Cover.FORMAT_JPEG
                    else:
                        cover_data = data
                        cover_fmt = MP4Cover.FORMAT_JPEG

            if cover_data:
                tags["covr"] = [MP4Cover(cover_data, imageformat=cover_fmt)]

            # Lyrics
            lyrics = self._get_lyrics_text(info)
            if lyrics:
                tags["\xa9lyr"] = [lyrics]

            audio.save()
        except Exception:
            # Silently fail on metadata errors; download still succeeded.
            pass

    @staticmethod
    def _copy_tags(m4a_path, mp3_path):
        """
        Copy metadata from an M4A file to an MP3 file.

        :param m4a_path: Path to source M4A file (with embedded tags).
        :param mp3_path: Path to target MP3 file.
        """
        try:
            m4a = MP4(m4a_path)
            if not m4a.tags:
                return

            title = m4a.get('\xa9nam', ['Unknown'])[0]
            artist = m4a.get('\xa9ART', ['Unknown Artist'])[0]
            album = m4a.get('\xa9alb', ['Unknown Album'])[0]
            date = m4a.get('\xa9day', [''])[0]
            lyrics = m4a.get('\xa9lyr', [None])[0]
            cover_list = m4a.get('covr', [])

            # Ensure MP3 has ID3 tags
            try:
                mp3 = MP3(mp3_path, ID3=ID3)
            except Exception:
                mp3 = MP3(mp3_path)
                mp3.add_tags()

            tags = mp3.tags

            tags.add(TIT2(encoding=3, text=title))
            tags.add(TPE1(encoding=3, text=artist))
            tags.add(TALB(encoding=3, text=album))
            if date:
                tags.add(TDRC(encoding=3, text=date))

            if lyrics:
                tags.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))

            if cover_list:
                cover_data = cover_list[0]
                # Detect image type
                if cover_data.startswith(b'\xff\xd8'):
                    mime = 'image/jpeg'
                elif cover_data.startswith(b'\x89PNG\r\n\x1a\n'):
                    mime = 'image/png'
                else:
                    mime = 'image/jpeg'

                tags.add(APIC(
                    encoding=3,
                    mime=mime,
                    type=3,          # front cover
                    desc='Cover',
                    data=cover_data
                ))

            mp3.save(v2_version=3)
        except Exception:
            pass

    def _convert_to_mp3(self, m4a_path):
        """
        Convert an M4A file to MP3 using PyAV.

        :param m4a_path: Path to the M4A file.
        :return: Path to the converted MP3 file, or None on failure.
        """
        mp3_path = m4a_path.with_suffix('.mp3')
        try:
            input_container = av.open(str(m4a_path))
            output_container = av.open(str(mp3_path), 'w', format='mp3')

            out_stream = output_container.add_stream('mp3', rate=44100)
            out_stream.options = {'b': '192k'}

            for frame in input_container.decode(audio=0):
                for packet in out_stream.encode(frame):
                    output_container.mux(packet)

            # Flush encoder
            for packet in out_stream.encode():
                output_container.mux(packet)

            output_container.close()
            input_container.close()

            if not mp3_path.exists():
                raise Exception("MP3 file not created")

            # Copy metadata from the original M4A to the new MP3
            self._copy_tags(m4a_path, mp3_path)
            return mp3_path
        except Exception:
            return None

    def download(self, url):
        """
        Download audio from the given URL, embed metadata, and optionally convert to MP3.

        :param url: YouTube URL.
        :return: Dictionary with keys:
                 - success (bool)
                 - filename (str) – name of the final file
                 - title (str)
                 - artist (str)
                 - album (str)
                 - duration (int)
                 - error (str, if success=False)
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                m4a_path = self._get_final_path(info)
                self._embed_all(m4a_path, info)

                final_path = m4a_path
                if self.convert_to_mp3:
                    mp3_path = self._convert_to_mp3(m4a_path)
                    if mp3_path and mp3_path.exists():
                        os.remove(m4a_path)
                        final_path = mp3_path

                return {
                    'success': True,
                    'filename': final_path.name,
                    'title': info.get('title', 'Unknown'),
                    'artist': info.get('artist') or info.get('uploader', 'Unknown Artist'),
                    'album': info.get('album', 'Unknown Album'),
                    'duration': info.get('duration', 0)
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}