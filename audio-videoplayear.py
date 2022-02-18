from mutagen.mp3 import MP3
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt5.QtCore import pyqtSignal, QAbstractListModel, QSize, QUrl, Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import os
from create_beta import Ui_MainWindow_
from beta03 import Ui_MainWindow
import random
from PyQt5 import uic
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pydub import AudioSegment


# функция для преобразования длины файла(в секундах) в более привычный вид(hh:mm:ss)
def hhmmss(ms):
    h, r = divmod(ms, 3600)
    ms = ms - (h * 3600)
    m, r = divmod(ms, 60)
    ms = ms - (m * 60)
    s = ms
    if h >= 1:
        return "%d:%02d:%02d" % (h, m, s)
    else:
        h = 0
        return "%d:%02d:%02d" % (h, m, s)


# класс для окна, в котором можно просматривать видео
class ViewerWindow(QMainWindow):
    state = pyqtSignal(bool)

    def closeEvent(self, e):
        self.state.emit(False)


# класс для окна с информацией о программе
class About_program(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('about.ui', self)


# класс для работы с файлами(обрезка и склейка)
class Work_with_Files(QMainWindow, Ui_MainWindow_):
    def __init__(self, *args, **kwargs):
        super(Work_with_Files, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.get_file_ = None
        self.list_ = []
        self.file_ = None
        self.second_fle_ = None
        self.first_fle_ = None

        self.player_ = QMediaPlayer()

        self.player_.play()

        self.playlist_ = QMediaPlaylist()
        self.player_.setPlaylist(self.playlist_)
        # настройка окна, отображающего видео
        self.viewer_ = ViewerWindow(self)
        self.viewer_.setWindowFlags(self.viewer_.windowFlags() | Qt.WindowStaysOnTopHint)
        self.viewer_.setMinimumSize(QSize(480, 360))

        videoWidget_ = QVideoWidget()
        self.viewer_.setCentralWidget(videoWidget_)
        self.player_.setVideoOutput(videoWidget_)
        # подключение кнопок к функциям
        self.playButton_.pressed.connect(self.player_.play)
        self.pauseButton_.pressed.connect(self.player_.pause)
        self.stopButton_.pressed.connect(self.player_.stop)
        self.volumeSlider_.valueChanged.connect(self.player_.setVolume)

        self.viewButton_.toggled.connect(self.toggle_viewer)
        self.viewer_.state.connect(self.viewButton_.setChecked)

        self.previousButton_.pressed.connect(self.playlist_.previous)
        self.nextButton_.pressed.connect(self.playlist_.next)
        # выбор файла из плейлиста и установка длительности файла
        self.model_ = PlaylistModel(self.playlist_)
        self.playlistView_.setModel(self.model_)
        self.playlist_.currentIndexChanged.connect(self.playlist_position_changed)
        self.selection_model_ = self.playlistView_.selectionModel()
        self.selection_model_.selectionChanged.connect(self.playlist_selection_changed)

        self.player_.durationChanged.connect(self.update_duration)
        self.player_.positionChanged.connect(self.update_position)
        self.timeSlider_.valueChanged.connect(self.player_.setPosition)
        # подключение кнопок и пунктов меню к функциям
        self.select_first_file_button_.pressed.connect(self.first_file)
        self.select_second_file_button_.pressed.connect(self.second_file)
        self.connect_two_files_button_.pressed.connect(self.connection)

        self.help_action_.triggered.connect(self.help)

        self.timeSlider_.blockSignals(False)

        self.open_file_action_.triggered.connect(self.open_file)

        self.start_cut_button_.pressed.connect(self.cutting)

        self.timeSlider_.blockSignals(False)

        self.setAcceptDrops(True)

        self.show()

    # функция, открывающая окно с краткой информацией о программе
    def about(self):
        self.about_prog_ = About_program()
        self.about_prog_.show()

    # выбор первого файла для соединения двух файлов в один
    def first_file(self):
        self.first_fle_ = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', '',
            'Аудио (*.mp3);;Видео (*.mp4)')[0]
        self.label_7_.clear()

    # выбор второго файла для соединения двух файлов в один
    def second_file(self):
        self.second_fle_ = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', '',
            'Аудио (*.mp3);;Видео (*.mp4)')[0]

    # соединение двух файлов в один
    # file_1[-3:] - берутся последние 3 символа из имени файла - расширение
    def connection(self):
        if self.second_fle_ is not None and self.first_fle_ is not None:
            file_1 = self.first_fle_
            form_1 = file_1[-3:]
            file_2 = self.second_fle_
            form_2 = file_2[-3:]
            if form_1 == 'mp3' and form_2 == 'mp3':
                sound_1 = AudioSegment.from_mp3(self.first_fle_)
                sound_2 = AudioSegment.from_mp3(self.second_fle_)
                new_file = sound_1 + sound_2
                name = 'Новые файлы/' + self.name_connection_.text() + '.mp3'
                new_file.export(name, format="mp3")
            elif form_1 == 'mp4' and form_2 == 'mp4':
                clip1 = VideoFileClip(self.first_fle_, audio=True)
                clip2 = VideoFileClip(self.second_fle_, audio=True)
                final_clip = concatenate_videoclips([clip1, clip2], method="compose")
                name = 'Новые файлы/' + self.name_connection_.text() + '.mp4'
                final_clip.write_videofile(name)
            else:
                self.label_7_.setText('                                       ОШИБКА!!!  РАЗНЫЕ РАСШИРЕНИЯ')
        else:
            self.name_connection_.setText('Ошибка')

    # функция для открытия файла и занесения его в плейлист
    def open_file(self):
        self.get_file_ = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', '',
            'Аудио (*.mp3);;Видео (*.mp4)')[0]
        if self.get_file_:
            self.list_.append(self.get_file_)
            self.playlist_.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(self.get_file_)
                )
            )

        self.model_.layoutChanged.emit()

    # открытие инструкции
    def help(self):
        os.startfile("помощь.docx")

    # расчет длины файла и вывод этого значения( в totalTimeLabel)
    # file[-3:] - берутся последние 3 символа из имени файла - расширение
    # duration_l = duration_l * 1000 - перевод секунд в милисекунды( 1с = 1000мс)
    # if okrug >= 5: - округление
    def update_duration(self, lenght):
        file = self.file_
        form = file[-3:]
        if form == 'mp3':
            f = MP3(self.file_)
            duration = f.info.length
            duration_l = str(duration)
            a = duration_l.find('.')
            okrug = int(duration_l[a + 1])
            duration_l = duration_l[:a]
            if okrug >= 5:
                duration_l = int(duration_l)
                duration_l += 1
            else:
                duration_l = int(duration_l)
            duration_l = duration_l * 1000

            self.timeSlider_.setMaximum(duration_l)

            if duration >= 0:
                self.totalTimeLabel_.setText(hhmmss(duration))
        elif form == 'mp4':
            clip = VideoFileClip(self.file_)
            duration = clip.duration
            duration_l = str(duration)
            a = duration_l.find('.')
            okrug = int(duration_l[a + 1])
            duration_l = duration_l[:a]
            if okrug >= 5:
                duration_l = int(duration_l)
                duration_l += 1
            else:
                duration_l = int(duration_l)
            duration_l = duration_l * 1000

            self.timeSlider_.setMaximum(duration_l)

            if duration >= 0:
                self.totalTimeLabel_.setText(hhmmss(duration))
        else:
            self.label_7_.setText('                                       ОШИБКА!!!  НЕВЕРНЫЙ ФОРМАТ ФАЙЛА')

    # Обновление текущей позиции записи и перемотка
    # т.к. текущее местоположение "флажка" для перемотки берется в милисекундах, то условие elif position < 1000:
    # нужно для того чтобы программа смогла определит 0 секунду(начальную позицию)
    def update_position(self, position):
        if position > 999:
            pos = position / 1000
            pos = int(pos)
        elif position < 1000:
            pos = 0
        if pos >= 0:
            self.currentTimeLabel_.setText(hhmmss(pos))

        self.timeSlider_.blockSignals(True)
        self.timeSlider_.setValue(position)
        self.timeSlider_.blockSignals(False)

    # Обрезка файлов
    # file[-3:] - берутся последние 3 символа из имени файла - расширение
    # if len(fro_m) == 3 and len(t_o) == 3 - проверка того , что данные введены верно в формате h:mm:ss(т.е 3 разряда)
    #  if len(i) != 2: - проверка того что в разряде 2 цифры ( исключение часы - if fro_m.index(i) != 0:)
    def cutting(self):
        if self.file_ == None:
            self.point_duration_from_.setText('Файл не выбран')
            self.point_duration_to_.setText('Файл не выбран')
        else:
            file = self.file_
            form = file[-3:]
            if form == 'mp3':
                sound = AudioSegment.from_mp3(self.file_)
                if ':' in self.point_duration_from_.text() and ':' in self.point_duration_to_.text():
                    fro_m = self.point_duration_from_.text().split(':')
                    t_o = self.point_duration_to_.text().split(':')
                    if len(fro_m) == 3 and len(t_o) == 3:
                        for i in fro_m:
                            if len(i) != 2:
                                if fro_m.index(i) != 0:
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                            list_i = i.split()
                            for j in list_i:
                                if j[0] not in '0123456789' or j[-1] not in '0123456789':
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                        for i in t_o:
                            if len(i) != 2:
                                if t_o.index(i) != 0:
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                            list_i = i.split()
                            for j in list_i:
                                if j[0] not in '0123456789' or j[-1] not in '0123456789':
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                        # перевод часов , минут и секунд в милисекунды
                        h_1 = int(fro_m[0]) * 3600
                        h_2 = int(t_o[0]) * 3600
                        m_1 = int(fro_m[1]) * 60
                        m_2 = int(t_o[1]) * 60
                        s_1 = int(fro_m[2])
                        s_2 = int(t_o[2])
                        time_from = (h_1 + m_1 + s_1) * 1000
                        time_to = (h_2 + m_2 + s_2) * 1000
                        sound_cut = sound[time_from:time_to]
                        if self.name_cutting_.text() is None or self.name_cutting_.text() == '' or \
                                self.name_cutting_.text() == ' ':
                            name_cut = 'Новые файлы/' + file[:-3] + '_cut' + '.mp3'
                        else:
                            name_cut = 'Новые файлы/' + self.name_cutting_.text() + '.mp3'
                        sound_cut.export(name_cut, format="mp3")
                    else:
                        self.point_duration_from_.setText('Неверный формат')
                        self.point_duration_to_.setText('Неверный формат')
                else:
                    self.point_duration_from_.setText('Неверный формат')
                    self.point_duration_to_.setText('Неверный формат')
            elif form == 'mp4':
                if ':' in self.point_duration_from_.text() and ':' in self.point_duration_to_.text():
                    fro_m = self.point_duration_from_.text().split(':')
                    t_o = self.point_duration_to_.text().split(':')
                    if len(fro_m) == 3 and len(t_o) == 3:
                        for i in fro_m:
                            if len(i) != 2:
                                if fro_m.index(i) != 0:
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                            list_i = i.split()
                            for j in list_i:
                                if j[0] not in '0123456789' or j[-1] not in '0123456789':
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                        for i in t_o:
                            if len(i) != 2:
                                if t_o.index(i) != 0:
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                            list_i = i.split()
                            for j in list_i:
                                if j[0] not in '0123456789' or j[-1] not in '0123456789':
                                    self.point_duration_from_.setText('Ошибка')
                                    self.point_duration_to_.setText('Ошибка')
                        h_1 = int(fro_m[0]) * 3600
                        h_2 = int(t_o[0]) * 3600
                        m_1 = int(fro_m[1]) * 60
                        m_2 = int(t_o[1]) * 60
                        s_1 = int(fro_m[2])
                        s_2 = int(t_o[2])
                        time_from = (h_1 + m_1 + s_1)
                        time_to = (h_2 + m_2 + s_2)
                        if self.name_cutting_.text() is None or self.name_cutting_.text() == '' or \
                                self.name_cutting_.text() == ' ':
                            name_cut = 'Новые файлы/' + file[:-3] + '_cut' + '.mp4'
                        else:
                            name_cut = 'Новые файлы/' + self.name_cutting_.text() + '.mp4'
                        ffmpeg_extract_subclip(self.file_, time_from, time_to, targetname=name_cut)
                    else:
                        self.point_duration_from_.setText('Неверный формат')
                        self.point_duration_to_.setText('Неверный формат')
                else:
                    self.point_duration_from_.setText('Неверный формат')
                    self.point_duration_to_.setText('Неверный формат')

    # выбор файла из плейлиста
    def playlist_selection_changed(self, ix):
        i = ix.indexes()[0].row()
        self.playlist_.setCurrentIndex(i)

    # установление текущей позиции в плейлисте
    def playlist_position_changed(self, i):
        self.file_ = self.list_[i]
        if i > -1:
            ix = self.model_.index(i)
            self.playlistView_.setCurrentIndex(ix)

    # показ окна с видео
    def toggle_viewer(self, state):
        if state:
            self.viewer_.show()
        else:
            self.viewer_.hide()


# класс для отображения имен файлов, которые были загруженны
class PlaylistModel(QAbstractListModel):
    def __init__(self, playlist, *args, **kwargs):
        super(PlaylistModel, self).__init__(*args, **kwargs)
        self.playlist = playlist

    def data(self, index, role):
        if role == Qt.DisplayRole:
            media = self.playlist.media(index.row())
            return media.canonicalUrl().fileName()

    def rowCount(self, index):
        return self.playlist.mediaCount()


# основной класс
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.get_file = None
        self.list = []
        self.file = None

        self.player = QMediaPlayer()

        self.player.play()

        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        # настройка окна, отображающего видео
        self.viewer = ViewerWindow(self)
        self.viewer.setWindowFlags(self.viewer.windowFlags() | Qt.WindowStaysOnTopHint)
        self.viewer.setMinimumSize(QSize(480, 360))

        videoWidget = QVideoWidget()
        self.viewer.setCentralWidget(videoWidget)
        self.player.setVideoOutput(videoWidget)
        # подключение кнопок к функциям
        self.playButton.pressed.connect(self.player.play)
        self.pauseButton.pressed.connect(self.player.pause)
        self.stopButton.pressed.connect(self.player.stop)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)

        self.viewButton.toggled.connect(self.toggle_viewer)
        self.viewer.state.connect(self.viewButton.setChecked)

        self.previousButton.pressed.connect(self.playlist.previous)
        self.nextButton.pressed.connect(self.playlist.next)

        self.random_file_button.pressed.connect(self.random_file)
        # выбор файла из плейлиста и установка длительности файла
        self.model = PlaylistModel(self.playlist)
        self.playlistView.setModel(self.model)
        self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        self.selection_model = self.playlistView.selectionModel()
        self.selection_model.selectionChanged.connect(self.playlist_selection_changed)

        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.timeSlider.valueChanged.connect(self.player.setPosition)
        # подключение кнопок и пунктов меню к функциям
        self.open_file_action.triggered.connect(self.open_file)

        self.help_action.triggered.connect(self.help)

        self.create_new_file_action.triggered.connect(self.new_file)

        self.timeSlider.blockSignals(False)

        self.info_about_action.triggered.connect(self.about)

        self.setAcceptDrops(True)

        self.show()

    # функция, открывающая окно с краткой информацией о программе
    def about(self):
        self.about_prog = About_program()
        self.about_prog.show()

    # функция для открытия файла и занесения его в плейлист
    def open_file(self):
        self.get_file = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', '',
            'Аудио (*.mp3);;Видео (*.mp4)')[0]
        if self.get_file:
            self.list.append(self.get_file)
            self.playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(self.get_file)
                )
            )

        self.model.layoutChanged.emit()

    # выбор случайного файла из плейлиста и его проигрывание
    def random_file(self):
        if self.list != []:
            random_file = random.choice(self.list)
            random_number = self.list.index(random_file)
            self.playlist.setCurrentIndex(random_number)
            self.player.play()
        else:
            pass

    # открытие инструкции
    def help(self):
        os.startfile("помощь.docx")

    # открытие нового окна для работы с файлами
    def new_file(self):
        self.work_with_file = Work_with_Files()
        self.work_with_file.show()

    # расчет длины файла и вывод этого значения( в totalTimeLabel)
    # if okrug >= 5: - округление
    # file[-3:] - берутся последние 3 символа из имени файла - расширение
    # duration_l = duration_l * 1000 - перевод секунд в милисекунды( 1с = 1000мс)
    def update_duration(self, lenght):
        self.label_warning.clear()
        file = self.file
        form = file[-3:]
        if form == 'mp3':
            f = MP3(self.file)
            duration = f.info.length
            duration_s = duration * 1000
            duration_s = str(duration_s)
            a = duration_s.find('.')
            okrug = int(duration_s[a + 1])
            duration_s = duration_s[:a]
            if okrug >= 5:
                duration_s = int(duration_s)
                duration_s += 1
            else:
                duration_s = int(duration_s)

            self.timeSlider.setMaximum(duration_s)

            if duration >= 0:
                self.totalTimeLabel.setText(hhmmss(duration))
        elif form == 'mp4':
            clip = VideoFileClip(self.file)
            duration = clip.duration
            duration_s = duration * 1000
            duration_s = str(duration_s)
            a = duration_s.find('.')
            okrug = int(duration_s[a + 1])
            duration_s = duration_s[:a]
            if okrug >= 5:
                duration_s = int(duration_s)
                duration_s += 1
            else:
                duration_s = int(duration_s)

            self.timeSlider.setMaximum(duration_s)

            if duration >= 0:
                self.totalTimeLabel.setText(hhmmss(duration))
        else:
            self.label_warning.setText('                                       ОШИБКА!!!  НЕВЕРНЫЙ ФОРМАТ ФАЙЛА')

    # Обновление текущей позиции записи и перемотка
    # т.к. текущее местоположение "флажка" для перемотки берется в милисекундах, то условие elif position < 1000:
    # нужно для того чтобы программа смогла определит 0 секунду(начальную позицию)
    def update_position(self, position):
        if position > 999:
            pos = position / 1000
            pos = int(pos)
        elif position < 1000:
            pos = 0
        if pos >= 0:
            self.currentTimeLabel.setText(hhmmss(pos))

        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)

    # выбор файла из плейлиста
    def playlist_selection_changed(self, ix):
        i = ix.indexes()[0].row()
        self.playlist.setCurrentIndex(i)

    # установление текущей позиции в плейлисте
    def playlist_position_changed(self, i):
        self.file = self.list[i]
        if i > -1:
            ix = self.model.index(i)
            self.playlistView.setCurrentIndex(ix)

    # показ окна с видео
    def toggle_viewer(self, state):
        if state:
            self.viewer.show()
        else:
            self.viewer.hide()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec_()
