from tqdm import tqdm
import numpy as np
from PIL import Image

import sstv_utils


class Martin_1:
    def __init__(self, audio_class, start, end):
        self.COLOR_MODE = 'RGB'
        self.COLOR_RANGE = (1500, 2300)
        self.SCAN_SEQUENCE = 'GBR'
        self.NUMBER_OF_LINES = 256
        self.NORMAL_DISPLAY_RES = (320, 256)
        self.TRANSMISSION_TIME = 114.3
        self.COLOR_SCAN_TIME = 146.432  # ms

        result = ''

        print("converting using martin 1 mode")

        MARGIN = 0.2
        whole_t = (self.COLOR_SCAN_TIME / 1000) * 3 + MARGIN

        BREAK_BASE_FREQ = 1200
        BREAK_BASE_FREQ_DEV = 200
        BREAK_BASE_LEN = 0.05
        BREAK_BASE_LEN_DEV = 0.1

        end_time = 0
        next_start = start

        current_line = 0

        img = Image.new('RGB', (self.NORMAL_DISPLAY_RES[0], self.NORMAL_DISPLAY_RES[1]), color='black')

        bar = tqdm(total=self.NORMAL_DISPLAY_RES[1],
                   bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}',
                   desc='image decoding',
                   unit='lines', )

        for i in range(self.NORMAL_DISPLAY_RES[1] - 1):
            c_s = next_start
            audio = sstv_utils.audio_part(next_start, next_start + whole_t, audio_class,
                                          (10, 32, self.NORMAL_DISPLAY_RES[0]))
            tones = sstv_utils.find_tones(audio, 150)

            found_tone = False
            for x in range(len(tones)):
                if sstv_utils.acceptable_tone(tones[x], BREAK_BASE_FREQ, BREAK_BASE_FREQ_DEV, BREAK_BASE_LEN,
                                              BREAK_BASE_LEN_DEV):
                    end_time = tones[x].start
                    next_start = tones[x].end
                    found_tone = True
                    break

            if not found_tone:
                result += f"the file ended before it was expected to end for this mode {i}/{self.NORMAL_DISPLAY_RES[1]} frames scanned\n"
                break

            if end_time != 0:
                #                                                      noverlap, nperseg, nfft
                audio = sstv_utils.audio_part(c_s, end_time, audio_class, (None, 16, 8192))

                colors_parts = np.array_split(audio.points, 3)
                print()
                print(len(audio.points))
                #audio.plot()

                converted_part = []
                for part in colors_parts:
                    converted_part.append(
                        [int(((point - self.COLOR_RANGE[0]) * 255) / (self.COLOR_RANGE[1] - self.COLOR_RANGE[0])) for
                         point in part])
                for x in range(self.NORMAL_DISPLAY_RES[0]):
                    try:
                        img.putpixel([x, i], (converted_part[2][x], converted_part[0][x], converted_part[1][x]))
                    except Exception:
                        pass
            else:
                result += "audio data does not contain horizontal synchronization pulse in acceptable margin\n"
                break

            bar.update()
            current_line += 1

        img.save('output.png')
        if result == '':
            result = 'image decoded successfully'
        print(result)
