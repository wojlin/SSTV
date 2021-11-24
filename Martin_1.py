from tqdm import tqdm
from PIL import Image
import numpy as np

import sstv_utils


class Martin_1:
    def __init__(self, audio_class, start, path, quality, cast):
        self.COLOR_MODE = 'RGB'
        self.COLOR_RANGE = (1500, 2300)
        self.SCAN_SEQUENCE = 'GBR'
        self.NUMBER_OF_LINES = 256
        self.NORMAL_DISPLAY_RES = (320, 256)
        self.TRANSMISSION_TIME = 114.3  # s
        self.COLOR_SCAN_TIME = 146.432  # ms

        print("converting using martin 1 mode")

        MARGIN = 0.01
        self.n_m = (self.COLOR_SCAN_TIME / 1000) * 3 - MARGIN
        self.p_m = (self.COLOR_SCAN_TIME / 1000) * 3 + MARGIN

        self.bp_FREQ = 1200
        self.bp_FREQ_DEV = 100
        self.bp_LEN = 0.05
        self.bp_LEN_DEV = 0.1

        self.separator_LEN = 0.0005

        break_pulse_start = start

        self.audio_class = audio_class

        current_line = 0

        img = Image.new('RGB', (self.NORMAL_DISPLAY_RES[0], self.NORMAL_DISPLAY_RES[1]), color='black')

        cast_img = Image.new('RGBA', (self.NORMAL_DISPLAY_RES[0], self.NORMAL_DISPLAY_RES[1]), color=(0, 0, 0, 255))

        bar = tqdm(total=self.NORMAL_DISPLAY_RES[1] - 1,
                   bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}',
                   desc='image decoding',
                   unit='lines', )

        for y in range(self.NORMAL_DISPLAY_RES[1] - 1):  # foreach scan line
            last_start = break_pulse_start

            break_pulse_start, break_pulse_end = self.find_break_pulse(break_pulse_start, debug=False)
            line = (break_pulse_end - last_start)
            line_strip = self.generate_line(line, last_start, quality, debug=False)

            for x in range(self.NORMAL_DISPLAY_RES[0]):
                img.putpixel([x, y], (line_strip[2][x], line_strip[0][x], line_strip[1][x]))

                if cast:
                    cast_img.putpixel([x, y], (line_strip[2][x], line_strip[0][x], line_strip[1][x], 255))
            if cast:
                cast_img.save('static/temp/cast.png')
            bar.update()
            current_line += 1

        if path is not None and path != '':
            img.save(path, exif=sstv_utils.exif('Martin 1'))
            print(f'file saved as "{str(path).split("/")[-1]}"')
        else:
            print('incorrect path! saving to script location as "out.png"')
            img.save('out.png', exif=sstv_utils.exif('Martin 1'))

    def find_break_pulse(self, start, debug=False):
        audio = sstv_utils.audio_part(start + self.n_m, start + self.p_m, self.audio_class, (30, 32, 4096))

        tones = sstv_utils.find_tones(audio, 100)

        found_tone = False

        end = None

        for x in reversed(range(len(tones))):
            if sstv_utils.acceptable_tone(tones[x], self.bp_FREQ, self.bp_FREQ_DEV, self.bp_LEN, self.bp_LEN_DEV):
                end = tones[x].start
                start = tones[x].end
                found_tone = True

                margin = 10

                #####   matching break tone on the left side   #####
                for point in reversed(range(len(audio.points))):
                    if audio.corrected_times[point] <= end and audio.points[point] >= self.COLOR_RANGE[0] - margin:
                        end = audio.corrected_times[point]
                        break
                    elif audio.corrected_times[point] <= end:
                        end = audio.corrected_times[point]
                ####################################################

                ####   matching break tone on the right side   #####
                for point in range(len(audio.points)):
                    if audio.corrected_times[point] >= start and audio.points[point] >= self.COLOR_RANGE[0] - margin:
                        start = audio.corrected_times[point]
                        break
                    elif audio.corrected_times[point] >= start:
                        start = audio.corrected_times[point]
                ####################################################

                break

        if not found_tone:
            end = start + self.n_m
            start = start + self.p_m

        if debug:
            audio.plot([start, end, 'b'])

        return start, end

    def generate_line(self, line, c_s, quality, debug=False):
        segment = line / 3

        if debug:
            audio = sstv_utils.audio_part(c_s, c_s + segment * 3, self.audio_class, (17, 22, pow(2, quality + 4)))
            audio.plot([c_s, c_s + segment, 'green'],
                       [c_s + segment + self.separator_LEN, self.separator_LEN + c_s + segment * 2, 'blue'],
                       [c_s + self.separator_LEN * 2 + segment * 2, self.separator_LEN * 2 + c_s + segment * 3, 'red'])

        line_strip = []
        for c in range(3):
            #                                                      noverlap, nperseg, nfft
            audio = sstv_utils.audio_part(c_s + (segment * c) + (self.separator_LEN * c),
                                          c_s + (segment * (c + 1)) + (self.separator_LEN * c), self.audio_class,
                                          (17, 22, pow(2, quality + 4)))

            line_strip.append(
                [int(((point - self.COLOR_RANGE[0]) * 255) / (self.COLOR_RANGE[1] - self.COLOR_RANGE[0])) for
                 point in audio.points])

        for c in range(3):
            for x in range(self.NORMAL_DISPLAY_RES[0] - len(line_strip[c])):
                line_strip[c].append(0)
            line_strip[c] = np.array(line_strip[c])[:self.NORMAL_DISPLAY_RES[0]]

        return line_strip
