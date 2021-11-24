from PIL.TiffImagePlugin import ImageFileDirectory_v2
from matplotlib.ticker import FormatStrFormatter
from matplotlib import pyplot as plt
from scipy.io.wavfile import read
from PIL.ExifTags import TAGS
from io import BytesIO
import scipy.signal
import numpy as np


class audio:
    """
    desc: class containing vaw file data

    Arguments
    ----------
    filepath: filepath to audio file

    Attributes
    ----------
    sample_rate: samples per second
    length: length of file in seconds
    n_of_channels: number of channels (script will choose channel 0 if more than one present)
    data: audio data

    Methods
    -------
    info(): this function prints out information's about audio file
    """

    def __init__(self, filepath):
        self.sample_rate, data = read(filepath)
        self.length = data.shape[0] / self.sample_rate
        if len(data.shape) == 1:
            self.n_of_channels = 1
        else:
            self.n_of_channels = data.shape[1]

        if self.n_of_channels > 1:
            self.data = np.array(data[:, 0])
        else:
            self.data = data

        if self.sample_rate != 11025:
            print(f"resampling audio data from {round(self.sample_rate / 1000, 2)} KHz to 11.025 KHz")
            self.data = scipy.signal.resample(self.data, int(11025 * self.length))
            self.sample_rate = 11025
            self.length = len(self.data) / self.sample_rate

    def info(self):
        print(f"sample rate: {self.sample_rate / 1000} KHz")
        print(f"samples amount: {len(self.data)}")
        print(f"number of channels = {self.n_of_channels}")
        print(f"length = {round(self.length, 2)}s")


class audio_part:
    """
    this class contains data about frequency of audio clip at given time

    Arguments
    ----------
    start: starting timestamp in seconds
    end: ending timestamp in seconds
    audio_class: class 'audio'

    Attributes
    ----------
    start: starting timestamp in seconds
    end: ending timestamp in seconds
    points : information about dominating frequency over time
    time_span: length of audio part
    """

    def __init__(self, part_start, part_end, audio_class, res):
        self.start = part_start
        self.end = part_end

        self.data = audio_class.data[int(self.start * audio_class.sample_rate):int(self.end * audio_class.sample_rate)]
        self.frequencies, self.times, self.spectrogram = scipy.signal.spectrogram(self.data, fs=audio_class.sample_rate,
                                                                                  noverlap=res[0], nperseg=res[1],
                                                                                  nfft=res[2])
        self.corrected_times = [t + part_start for t in self.times]

        self.points = [self.frequencies[np.argmax(entry)] for entry in self.spectrogram.transpose()]

        self.time_span = self.times[-1] - self.times[0]
        self.one_hop_len = self.time_span / len(self.points)

    def info(self):
        print(f"### PART {round(self.start, 2)}s-{round(self.end, 2)}s ###")
        print(f"time span: {round(self.time_span, 2)}s")
        print(f"one hop len: {round(self.one_hop_len, 2)}s")
        print("")

    def plot(self, *args):
        plt.clf()

        for arg in args:
            start = arg[0]
            end = arg[1]
            color = arg[2]
            plt.axvline(x=start, c=color)
            plt.axvline(x=end, c=color)
            plt.axvspan(start, end, alpha=0.3, color=color)

        plt.scatter(self.corrected_times, self.points, s=5, c='r')
        plt.xticks(np.linspace(self.start, self.end, 15))
        plt.yticks(np.linspace(0, max(self.points) + 100, 50))
        plt.xlim(self.start, self.end)
        plt.grid()
        plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.3f s'))
        plt.show()


class tone:
    def __init__(self, freq, start, end, duration):
        self.freq = freq
        self.start = start
        self.end = end
        self.duration = duration

    def info(self):
        print()
        print("$$$$$$$$$$$$$")
        print(f"tone freq: {int(self.freq)} Hz")
        print(f"tone span: {round(self.start, 2)}s - {round(self.end, 2)}s")
        print(f"tone length: {round(self.duration, 2)}s")
        print("$$$$$$$$$$$$$")


def find_tones(part, allowed_deviation):
    captured_tones = []

    tone_freq = 0
    tones_avg = []
    tone_start_time = 0
    tone_current_len = 0

    for p in range(len(part.points)):
        if tone_freq - allowed_deviation < part.points[p] < tone_freq + allowed_deviation:
            tone_current_len += part.one_hop_len
            tones_avg.append(part.points[p])
        else:
            if len(tones_avg) >= 2:
                freq = np.average(tones_avg)
                start = tone_start_time
                end = tone_start_time + tone_current_len
                duration = tone_current_len
                captured_tones.append(tone(freq, start, end, duration))

            tones_avg.clear()
            tone_current_len = 0

            tone_start_time = part.times[p] + part.start
            tone_freq = part.points[p]
            tones_avg.append(part.points[p])
            tone_current_len += part.one_hop_len

    return captured_tones


def acceptable_tone(tone_obj, desired_freq, freq_dev, desired_freq_len, freq_len_dev):
    freq = tone_obj.freq
    freq_len = tone_obj.duration
    if desired_freq - freq_dev < freq < desired_freq + freq_dev:
        if desired_freq_len - freq_len_dev < freq_len < desired_freq_len + freq_len_dev:
            return True
    return False


def exif(mode):
    ifd = ImageFileDirectory_v2()
    _TAGS_r = dict(((v, k) for k, v in TAGS.items()))
    ifd[_TAGS_r["Artist"]] = 'www.github.com/wojlin'
    ifd[_TAGS_r["Software"]] = 'sstv decoder v1.0'
    ifd[_TAGS_r["ImageDescription"]] = f'mode: {mode}'
    out = BytesIO()
    ifd.save(out)

    return b"Exif\x00\x00" + out.getvalue()
