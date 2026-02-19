# video_downloader.py
"""
Video downloader module. Downloads the best available video and audio streams,
then merges them into a single MP4 file using PyAV.
"""

import shutil
from pathlib import Path
import re

import yt_dlp
import av


class VideoDownloader:
    """
    Downloads YouTube videos by selecting the best video-only and audio-only formats,
    then merges them into a final MP4 file.
    """

    def __init__(self, output_folder):
        """
        :param output_folder: Directory where the final video will be saved.
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)

    def download(self, url):
        """
        Download the video from the given URL and merge into MP4.

        :param url: YouTube video URL.
        :return: Dictionary with keys:
                 - success (bool)
                 - filename (str) – name of the final file
                 - title (str)
                 - error (str, if success=False)
        """
        temp_dir = self.output_folder / "temp_video"
        temp_dir.mkdir(exist_ok=True)

        try:
            # First, extract info without downloading to select formats
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)

            # Separate video-only and audio-only formats
            video_formats = [
                f for f in info['formats']
                if f.get('vcodec') != 'none' and f.get('acodec') == 'none'
            ]
            if not video_formats:
                # Fallback to any format with video (may already include audio)
                video_formats = [f for f in info['formats'] if f.get('vcodec') != 'none']
            video_formats.sort(key=lambda f: (f.get('height', 0) or 0, f.get('tbr', 0) or 0), reverse=True)
            best_video = video_formats[0]

            audio_formats = [
                f for f in info['formats']
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none'
            ]
            if not audio_formats:
                audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none']
            audio_formats.sort(key=lambda f: f.get('abr', 0) or 0, reverse=True)
            best_audio = audio_formats[0]

            # Sanitize title for file name
            sanitized_title = re.sub(r'[\\/:*?"<>|]', '_', info['title'])

            # If video and audio are already in the same format, download directly
            if best_video['format_id'] == best_audio['format_id']:
                opts = {
                    'format': best_video['format_id'],
                    'outtmpl': str(temp_dir / 'combined.%(ext)s'),
                    'quiet': True,
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                combined_files = list(temp_dir.glob('combined.*'))
                if not combined_files:
                    raise Exception("Combined file not found")
                src = combined_files[0]
                dst = self.output_folder / f"{sanitized_title}.mp4"
                if dst.exists():
                    dst = self.output_folder / f"{sanitized_title}_1.mp4"
                shutil.move(str(src), str(dst))
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {
                    'success': True,
                    'filename': dst.name,
                    'title': info['title'],
                }

            # Download video and audio separately
            video_opts = {
                'format': best_video['format_id'],
                'outtmpl': str(temp_dir / 'video.%(ext)s'),
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                ydl.download([url])

            audio_opts = {
                'format': best_audio['format_id'],
                'outtmpl': str(temp_dir / 'audio.%(ext)s'),
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([url])

            video_file = next(temp_dir.glob('video.*'))
            audio_file = next(temp_dir.glob('audio.*'))

            dst = self.output_folder / f"{sanitized_title}.mp4"
            if dst.exists():
                dst = self.output_folder / f"{sanitized_title}_1.mp4"

            # Merge using PyAV
            self._merge_video_audio(str(video_file), str(audio_file), str(dst))

            shutil.rmtree(temp_dir, ignore_errors=True)

            return {
                'success': True,
                'filename': dst.name,
                'title': info['title'],
            }

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _merge_video_audio(video_path, audio_path, output_path):
        """
        Merge a video file and an audio file into a single MP4 container using PyAV.

        :param video_path: Path to video file (could be without audio).
        :param audio_path: Path to audio file.
        :param output_path: Path for the output MP4 file.
        """
        in_v = av.open(video_path)
        in_a = av.open(audio_path)
        out = av.open(output_path, 'w', format='mp4')

        # Copy video stream
        v_in_stream = in_v.streams.video[0]
        v_out_stream = out.add_stream_from_template(v_in_stream)

        # Copy audio stream
        a_in_stream = in_a.streams.audio[0]
        a_out_stream = out.add_stream_from_template(a_in_stream)

        # Mux video packets
        for packet in in_v.demux(v_in_stream):
            if packet.dts is None:
                continue
            packet.stream = v_out_stream
            out.mux(packet)

        # Mux audio packets
        for packet in in_a.demux(a_in_stream):
            if packet.dts is None:
                continue
            packet.stream = a_out_stream
            out.mux(packet)

        out.close()
        in_v.close()
        in_a.close()