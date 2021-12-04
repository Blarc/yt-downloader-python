#!/usr/bin/env python
import PySimpleGUI as sg
import threading
import yt_dlp
import queue

queue_thread: threading.Thread
song_queue = queue.Queue()

data = []


class Logger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class Row:
    def __init__(self, url, status):
        self.url = url
        self.title = ''
        self.status = status
        self.color = 'LightYellow'


def my_hook(d):
    print(d['status'])
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': Logger(),
    'progress_hooks': [my_hook],
    'paths': {
        'home': ''
    }
}


def download_song(row: Row):
    print(f'Start downloading: {row.url}')
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(row.url, download=True)

            row.title = info['title']
            row.status = 'Completed'
            row.color = 'pale green'

            refresh_table()

    except:
        print(f'Can\'t download: {row.url}')
        row.status = 'Failed'
        row.color = 'misty rose'
        refresh_table()


def queue_loop():
    while True:
        if not song_queue.empty():
            row = song_queue.get()
            download_song(row)
            song_queue.task_done()


def refresh_table():
    window['TABLE'].update(
        values=list(map(lambda row: [row.url, row.title, row.status], data)),
        row_colors=tuple((index, row.color) for index, row in enumerate(data))
    )


# ------ Window Layout ------
sg.theme('DefaultNoMoreNagging')
headings = ['Url', 'Name', 'Progress']
layout = [
    [sg.Text('Input URL / Song ID / Playlist ID')],
    [
        sg.Input(key='INPUT', size=(50, 4)), sg.Button('Download', enable_events=True, key='DOWNLOAD')
    ],
    [sg.Table(
        values=[],
        headings=headings,
        max_col_width=25,
        auto_size_columns=False,
        col_widths=[50, 50, 20],
        display_row_numbers=True,
        justification='center',
        num_rows=10,
        alternating_row_color='lightgray',
        key='TABLE',
        row_height=35,
    )
    ],
    [
        sg.Text('Output folder')
    ],
    [
        sg.In(size=(50, 4), enable_events=True, key='OUTPUT_FOLDER'), sg.FolderBrowse()
    ]
]

# ------ Create Window ------
window = sg.Window('YouTube MP3 downloader', layout, font='Bahnschrift 10')

if __name__ == '__main__':
    for i in range(4):
        queue_thread = threading.Thread(target=queue_loop, daemon=True)
        queue_thread.start()

    # ------ Event Loop ------
    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED:
            break

        if event == 'DOWNLOAD':
            input_url = values['INPUT']
            if input_url != '':
                new_row = Row(input_url, 'Downloading')
                song_queue.put(new_row)
                data.insert(0, new_row)

                window.Element('INPUT').update('')
                refresh_table()
        elif event == 'OUTPUT_FOLDER':
            ydl_opts['paths']['home'] = values['OUTPUT_FOLDER']

    window.close()
