import static_ffmpeg
import os




class VideoConfig:

    def __init__(self):
        self.ydl_opts = {
            'format': 'best',
            'quiet': True,
            'noplaylist': True,
            'noprogress': True,
            'consoletitle': False,
            'no_warnings': True,
            'allow_unplayable_formats': False,
            'outtmpl': './download/%(title)s.%(ext)s',
        }

    def setter(self, updater_dict):
        self.ydl_opts = self.ydl_opts | updater_dict

    def getter(self):
        return self.ydl_opts

    def add_subtitle_support(self):

        subtitle_support_config = {
            'writeautomaticsub': True,
            'subtitleslangs':  ['en']}

        self.ydl_opts = self.ydl_opts | subtitle_support_config

    def add_1080p(self):

        os.system("static_ffmpeg -version")
        os.system("static_ffprobe -version")

        config_1080p = {
            'format': 'bv[ext=mp4]+ba+mergeall',
        }

        self.ydl_opts = self.ydl_opts | config_1080p

    def add_480p(self):

        config_480p = {
            'format': 'height:480',
        }

        self.ydl_opts = self.ydl_opts | config_480p


def video_with_subtitle():
    config_obj = VideoConfig()
    config_obj.add_subtitle_support()
    return config_obj.getter()


def video_without_subtitle():
    config_obj = VideoConfig()
    return config_obj.getter()


def video_with_1080p():
    config_obj = VideoConfig()
    config_obj.add_1080p()
    return config_obj.getter()


def video_with_480p():
    config_obj = VideoConfig()
    config_obj.add_480p()
    return config_obj.getter()
