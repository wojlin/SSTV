import numpy as np
import importlib
import sstv_utils


class sstv:
    def __init__(self, filename):

        def find_header(tones_list):

            if len(tones_list) < 3:
                return None

            HEADER_BASE_FREQ = 1900
            HEADER_BASE_FREQ_DEV = 50
            HEADER_BASE_LEN = 0.3
            HEADER_BASE_LEN_DEV = 0.1

            HEADER_BREAK_FREQ = 1200
            HEADER_BREAK_FREQ_DEV = 50
            HEADER_BREAK_LEN = 0.1
            HEADER_BREAK_LEN_DEV = 0.1

            header_data = None

            for x in range(len(tones_list) - 2):
                if sstv_utils.acceptable_tone(tones_list[x], HEADER_BASE_FREQ, HEADER_BASE_FREQ_DEV, HEADER_BASE_LEN,
                                              HEADER_BASE_LEN_DEV):
                    if sstv_utils.acceptable_tone(tones_list[x + 1], HEADER_BREAK_FREQ, HEADER_BREAK_FREQ_DEV,
                                                  HEADER_BREAK_LEN,
                                                  HEADER_BREAK_LEN_DEV):
                        if sstv_utils.acceptable_tone(tones_list[x + 2], HEADER_BASE_FREQ, HEADER_BASE_FREQ_DEV,
                                                      HEADER_BASE_LEN,
                                                      HEADER_BASE_LEN_DEV):
                            header_data = (tones_list[x].start, tones_list[x + 2].end)
                            break
            return header_data

        def find_vis_part(header, tones):
            VIS_START_FREQ = 1200
            VIS_FREQ_DEV = 50
            VIS_BIT_LEN = 0.03
            VIS_BIT_LEN_DEV = 0.01

            VIS_start = header[1]

            VIS_bits_start = None
            VIS_bits_end = None
            img_data_start = None

            for x in range(len(tones)):
                if tones[x].start >= VIS_start:
                    if sstv_utils.acceptable_tone(tones[x], VIS_START_FREQ, VIS_FREQ_DEV, VIS_BIT_LEN, VIS_BIT_LEN_DEV):
                        if VIS_bits_start is None:
                            VIS_bits_start = tones[x].end
                        else:
                            VIS_bits_end = tones[x].start
                            img_data_start = tones[x].end

            if VIS_bits_start is not None and VIS_bits_end is not None and img_data_start is not None:
                return VIS_bits_start, VIS_bits_end, img_data_start
            else:
                return None

        class vis:
            def __init__(self, VIS_part_data):
                VIS_ZERO_FREQ = 1300
                VIS_ONE_FREQ = 1100

                k, m = divmod(len(VIS_part_data.points), 8)
                VIS_bits_freq = [int(np.average(VIS_part_data.points[i * k + min(i, m):(i + 1) * k + min(i + 1, m)]))
                                 for i
                                 in range(8)]
                VIS_converted_bits = ""
                for freq in VIS_bits_freq:
                    if abs(VIS_ZERO_FREQ - freq) > abs(VIS_ONE_FREQ - freq):
                        VIS_converted_bits += "1"
                    else:
                        VIS_converted_bits += "0"

                self.VIS_converted_bits = VIS_converted_bits

            def raw(self):
                return self.VIS_converted_bits

            def int(self):
                inverted = self.VIS_converted_bits[::-1][1:]
                parity = 1 - int(self.VIS_converted_bits[-1])
                int_val = int(inverted, 2)

                if (int_val % 2) == parity:
                    return int_val
                else:
                    return "broken vis code"

            def mode(self):
                modes = {60: "Scottie 1",
                         56: "Scottie 2",
                         76: "Scottie DX",
                         44: "Martin 1",
                         40: "Martin 2",
                         8: "Robot 36",
                         12: "Robot 72",
                         55: "Wrasse SC2-180",
                         113: "Pasokon P3",
                         114: "Pasokon P5",
                         115: "Pasokon P7",
                         93: "PD50",
                         99: "PD90",
                         95: "PD120",
                         98: "PD160",
                         96: "PD180",
                         97: "PD240",
                         94: "PD290"}
                if self.int() == "broken vis code":
                    return "unknown mode"
                return modes[self.int()] if self.int() in modes else "unknown mode"

        self.audio_class = sstv_utils.audio(filename)

        current_time = 0

        while current_time < self.audio_class.length:
            clip_part = sstv_utils.audio_part(current_time, current_time + 1.2, self.audio_class, (10, 80, 128))
            #clip_part.plot()
            tones = sstv_utils.find_tones(clip_part, 220)
            #for tone in tones:
                #print(tone.info())
            self.header_data = find_header(tones)
            if self.header_data is not None:
                tones = sstv_utils.find_tones(clip_part, 60)
                try:
                    self.VIS_part = find_vis_part(self.header_data, tones)
                    self.VIS_data = vis(sstv_utils.audio_part(self.VIS_part[0],
                                                                   self.VIS_part[1],
                                                                   self.audio_class,
                                                                   (50, 100, 128)))
                    break
                except Exception:
                    pass
            current_time += 0.1

        if self.header_data is None:
            raise Exception(f"no sstv header found in file: '{filename}'")

    def decode(self, path, quality, cast=False):
        if 1 < quality > 10:
            raise Exception("quality need to be in range 1-10")
        mod_name, func_name = (
                self.VIS_data.mode().replace(' ', '_') + '.' + self.VIS_data.mode().replace(' ', '_')).rsplit('.',                                                                                                            1)
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            raise Exception(f"'{self.VIS_data.mode()}' mode not supported yet")
        func = getattr(mod, func_name)
        func(self.audio_class, self.VIS_part[2], path, quality, cast)

    def info(self):
        print("########################")
        self.audio_class.info()
        print(f"header found from {round(self.header_data[0], 2)}s to {round(self.header_data[1], 2)}s")
        print(f"vis found from: {round(self.VIS_part[0], 2)}s to {round(self.VIS_part[1], 2)}s")
        print(f"vis binary data: {self.VIS_data.raw()}")
        print(f"vis decimal value: {self.VIS_data.int()}")
        print(f"SSTV mode: {self.VIS_data.mode()}")
        print(f"image data starts from {round(self.VIS_part[2], 2)}s")
        print("########################")
        print()


if __name__ == "__main__":
    #decoder = sstv('SSTV_sample.wav')
    #decoder = sstv('card.wav')
    #decoder = sstv('sstv.wav')
    decoder = sstv('card_martin.wav')
    decoder.info()
    #               path      quality level (1-10)
    decoder.decode('output.png', 5, cast=True)
