from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QLabel,
    QApplication,
    QTextEdit,
    QDialog,
    QComboBox,
    QCheckBox,
)
from PyQt6 import uic
import sys
from yt_dlp import YoutubeDL
from pytube import YouTube, exceptions
from download_preference import *


def error_message(error_type):
    global global_error_msg
    global_error_msg = error_type


def video_exception_handler(url):
    error_passed = False
    try:
        single_video_obj = YouTube(url)

        video_info = {
            "Name": str(single_video_obj.title),
            "Author": str(single_video_obj.author),
            "Duration": str(single_video_obj.length),
        }

    except exceptions.RegexMatchError:
        error_message("Invalid video link.")

    except exceptions.VideoPrivate:
        error_message("The video is private.")

    except exceptions.MaxRetriesExceeded:
        error_message("Maximum number of retries exceeded.")

    except exceptions.VideoRegionBlocked:
        error_message("The video is region blocked.")

    except exceptions.VideoUnavailable:
        error_message("Unknown error")

    else:
        if video_info["Name"] == "age restricted":
            error_message("The video is age restricted.")

        elif video_info["Duration"] == 0:
            error_message("The video is a live strean.")
        else:
            error_passed = True
    finally:
        if error_passed:
            return url

        else:
            return False


# Create a worker class for video download(multi-threading)
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    progress_indication = 1

    def set_data(self, ydl_opts, url):
        self.ydl_opts = ydl_opts
        self.url = url

    def run(self):
        def download_progress_hook(hook_dict):
            if (
                hook_dict["status"] == "downloading"
                and hook_dict["total_bytes"]
                and hook_dict["downloaded_bytes"]
                and hook_dict["_percent_str"]
                and hook_dict["eta"]
                and hook_dict["speed"]
            ):
                global total_video_size
                global download_percentage
                global download_speed
                global total_downloaded
                global download_eta

                total_video_size = hook_dict["_total_bytes_str"]
                download_percentage = hook_dict["_percent_str"]
                download_speed = hook_dict["_speed_str"]
                total_downloaded = hook_dict["_downloaded_bytes_str"]
                download_eta = hook_dict["_eta_str"]

                self.progress.emit(self.progress_indication + 1)

        hook_config = {
            "progress_hooks": [download_progress_hook],
        }

        self.ydl_opts = self.ydl_opts | hook_config
        #  print(self.ydl_opts)
        with YoutubeDL(self.ydl_opts) as ydl:
            ydl.download(self.url)
        self.finished.emit()


class ErrorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("error.ui", self)
        self.error_panel = self.findChild(QLabel, "error_msg_label")
        self.error_panel.setText(f"{global_error_msg}")


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        # load the UI
        uic.loadUi("ydm.ui", self)

        # defining widgets
        self.textedit = self.findChild(QTextEdit, "url_box")
        self.button = self.findChild(QPushButton, "link_submit")
        self.subtitle_enabler = self.findChild(QCheckBox, "subtitle_choice")
        self.resoulution_dropdown = self.findChild(QComboBox, "resolution_picker")

        # download progress related widgets
        self.video_file_size_label = self.findChild(QLabel, "progress_hook_total_size")

        self.video_downloaded_size_label = self.findChild(
            QLabel, "progress_hook_downloaded_size"
        )

        self.download_speed_label = self.findChild(
            QLabel, "progress_hook_download_speed"
        )

        self.download_eta_label = self.findChild(QLabel, "progress_hook_remaining_time")

        self.download_percentage_label = self.findChild(
            QLabel, "progress_hook_download_percentage"
        )

        # do something
        self.button.clicked.connect(self.link_button_click_handler)
        self.hide_labels()
        # Show the app
        self.show()

    def hide_labels(self):
        self.video_file_size_label.hide()

        self.video_downloaded_size_label.hide()

        self.download_speed_label.hide()

        self.download_eta_label.hide()

        self.download_percentage_label.hide()

    def show_labels(self):
        self.video_file_size_label.show()

        self.video_downloaded_size_label.show()

        self.download_speed_label.show()

        self.download_eta_label.show()

        self.download_percentage_label.show()

    def link_button_click_handler(self):
        url = str(self.textedit.toPlainText())
        if url != "":
            pop_error_window = video_exception_handler(url)
            if not pop_error_window:
                self.err()
            else:
                self.video_downloader_func(url)

    def download_completion_func(self):
        self.hide_labels()
        self.statusBar().showMessage("Download complete", msecs=6000)
        self.button.setDisabled(False)
        self.subtitle_enabler.setDisabled(False)
        self.resoulution_dropdown.setDisabled(False)
        self.video_file_size_label.clear()
        self.video_downloaded_size_label.clear()
        self.download_speed_label.clear()
        self.download_eta_label.clear()
        self.download_percentage_label.clear()

    def download_progress_func(self, i):
        self.video_file_size_label.setText("Video size: " + total_video_size)
        self.video_downloaded_size_label.setText("Downloaded: " + total_downloaded)

        self.download_speed_label.setText("Download speed: " + download_speed)
        self.download_percentage_label.setText("Progress: " + download_percentage)
        self.download_eta_label.setText("Eta: " + download_eta)

    def video_downloader_func(self, url):

        subtile_yes_or_not = self.subtitle_enabler.isChecked()
        if subtile_yes_or_not:
            ydl_opts = video_with_subtitle()
        else:
            ydl_opts = video_without_subtitle()

        resolution_status = self.resoulution_dropdown.currentText()
        if resolution_status == "1080p":
            ydl_opts = video_with_1080p()
        elif resolution_status == "480p":
            ydl_opts = video_with_480p()

        self.statusBar().showMessage("Downloading...")
        self.statusBar().repaint()
        self.show_labels()
        self.thread = QThread()
        self.worker = Worker()
        self.worker.set_data(ydl_opts, url)
        # Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # Start the thread
        self.thread.start()
        self.worker.progress.connect(self.download_progress_func)
        # disable the main window buttons
        self.button.setDisabled(True)
        self.subtitle_enabler.setDisabled(True)
        self.resoulution_dropdown.setDisabled(True)
        self.thread.finished.connect(self.download_completion_func)

    def err(self):
        dialog = ErrorWindow()
        dialog.exec()


app = QApplication(sys.argv)
UIWindow = UI()
app.exec()
