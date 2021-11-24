import scipy.signal
from scipy.io.wavfile import read
from matplotlib import pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import numpy as np

sample_rate, audio_data = read('SSTV_sample.wav')
#sample_rate, audio_data = read('sstv.wav')
length = audio_data.shape[0] / sample_rate
if len(audio_data.shape) == 1:
    n_of_channels = 1
else:
    n_of_channels = audio_data.shape[1]

if n_of_channels > 1:
    audio_data = np.array(audio_data[:, 0])
else:
    audio_data = audio_data

audio_data = scipy.signal.resample(audio_data, int(11025*length))
sample_rate = 11025
length = len(audio_data) / sample_rate

print(f"sample rate: {sample_rate / 1000} KHz")
print(f"samples amount: {len(audio_data)}")
print(f"number of channels = {n_of_channels}")
print(f"length = {length}s")


def show_spectrogram(x_limiter, y_limiter):
    plt.specgram(audio_data,
                 noverlap=150,
                 NFFT=256,
                 pad_to=2048,
                 Fs=sample_rate,
                 scale='linear',
                 cmap='magma')
    plt.xticks(np.arange(float(x_limiter[0]), float(x_limiter[1] + 0.1), (x_limiter[1] - x_limiter[0]) * (1 / 10), dtype=float))
    plt.xlim(x_limiter[0], x_limiter[1])
    plt.ylim(y_limiter[0], y_limiter[1])
    plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.2f s'))
    plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d Hz'))
    plt.xlabel("Time")
    plt.ylabel("Frequency")
    plt.title(f"spectrogram of audio data from {round(x_limiter[0], 2)}s to {round(x_limiter[1], 2)}s")
    plt.show()


show_spectrogram((0, length), (1000, 2500))
show_spectrogram((0, 2), (1000, 4000))
show_spectrogram((10, 12), (1000, 4000))
