"""
MicroPython Waveshare 4.2" Black/White/Red GDEW042Z15 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# also works for black/white/yellow GDEW042C37?

from micropython import const
from time import sleep_ms

# Display resolution
EPD_WIDTH  = const(400)
EPD_HEIGHT = const(300)

# Display commands
PANEL_SETTING                  = const(0x00)
#POWER_SETTING                  = const(0x01)
POWER_OFF                      = const(0x02)
#POWER_OFF_SEQUENCE_SETTING     = const(0x03)
POWER_ON                       = const(0x04)
#POWER_ON_MEASURE               = const(0x05)
BOOSTER_SOFT_START             = const(0x06)
DEEP_SLEEP                     = const(0x07)
DATA_START_TRANSMISSION_1      = const(0x10)
#DATA_STOP                      = const(0x11)
DISPLAY_REFRESH                = const(0x12)
DATA_START_TRANSMISSION_2      = const(0x13)
#VCOM_LUT                       = const(0x20)
#W2W_LUT                        = const(0x21)
#B2W_LUT                        = const(0x22)
#W2B_LUT                        = const(0x23)
#B2B_LUT                        = const(0x24)
#PLL_CONTROL                    = const(0x30)
#TEMPERATURE_SENSOR_CALIBRATION = const(0x40)
#TEMPERATURE_SENSOR_SELECTION   = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51)
#TCON_SETTING                   = const(0x60)
#RESOLUTION_SETTING             = const(0x61)
#GSST_SETTING                   = const(0x65)
#GET_STATUS                     = const(0x71)
#AUTO_MEASURE_VCOM              = const(0x80)
#VCOM_VALUE                     = const(0x81)
#VCM_DC_SETTING                 = const(0x82)
#PARTIAL_WINDOW                 = const(0x90)
#PARTIAL_IN                     = const(0x91)
#PARTIAL_OUT                    = const(0x92)
#PROGRAM_MODE                   = const(0xA0)
#ACTIVE_PROGRAM                 = const(0xA1)
#READ_OTP_DATA                  = const(0xA2)
#POWER_SAVING                   = const(0xE3)

BUSY = const(0)  # 0=busy, 1=idle

class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.rotate = 0

    def _command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def init(self):
        self.reset()
        self._command(BOOSTER_SOFT_START, b'\x17\x17\x17') # 07 0f 17 1f 27 2F 37 2f
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PANEL_SETTING, b'\x0F') # LUT from OTP

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    # draw the current frame memory
    def display_frame(self, frame_buffer_black, frame_buffer_red):
        if (frame_buffer_black != None):
            self._command(DATA_START_TRANSMISSION_1)
            sleep_ms(2)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([frame_buffer_black[i]]))
            sleep_ms(2)
        if (frame_buffer_red != None):
            self._command(DATA_START_TRANSMISSION_2)
            sleep_ms(2)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([frame_buffer_red[i]]))
            sleep_ms(2)

        self._command(DISPLAY_REFRESH)
        self.wait_until_idle()

    # to wake call reset() or init()
    def sleep(self):
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\xF7') # border floating
        self._command(POWER_OFF)
        self.wait_until_idle()
        self._command(DEEP_SLEEP, b'\xA5') # check code

    def set_pixel(self, frame_buffer, x, y, colored):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == 0):
            self.set_absolute_pixel(frame_buffer, x, y, colored)



    def set_absolute_pixel(self, frame_buffer, x, y, colored):
        # To avoid display orientation effects
        # use EPD_WIDTH instead of self.width
        # use EPD_HEIGHT instead of self.height
        if (x < 0 or x >= EPD_WIDTH or y < 0 or y >= EPD_HEIGHT):
            return
        if (colored):
            frame_buffer[int((x + y * EPD_WIDTH) / 8)] &= ~(0x80 >> (x % 8))
        else:
            frame_buffer[int((x + y * EPD_WIDTH) / 8)] |= 0x80 >> (x % 8)


    def draw_char_at(self, frame_buffer, x, y, char, font, colored):
        char_offset = (ord(char) - ord(' ')) * font.height * (int(font.width / 8) + (1 if font.width % 8 else 0))
        offset = 0

        for j in range(font.height):
            for i in range(font.width):
                if font.data[char_offset+offset] & (0x80 >> (i % 8)):
                    self.set_pixel(frame_buffer, x + i, y + j, colored)
                if i % 8 == 7:
                    offset += 1
            if font.width % 8 != 0:
                offset += 1


    def display_string_at(self, frame_buffer, x, y, text, font, colored):
        refcolumn = x

        # Send the string character by character on EPD
        for index in range(len(text)):
            # Display one character on EPD
            self.draw_char_at(frame_buffer, refcolumn, y, text[index], font, colored)
            # Decrement the column position by 16
            refcolumn += font.width

    def draw_horizontal_line(self, frame_buffer, x, y, width, colored):
        for i in range(x, x + width):
            self.set_pixel(frame_buffer, i, y, colored)


    def draw_vertical_line(self, frame_buffer, x, y, height, colored):
        for i in range(y, y + height):
            self.set_pixel(frame_buffer, x, i, colored)


    def draw_rectangle(self, frame_buffer, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        self.draw_horizontal_line(frame_buffer, min_x, min_y, max_x - min_x + 1, colored)
        self.draw_horizontal_line(frame_buffer, min_x, max_y, max_x - min_x + 1, colored)
        self.draw_vertical_line(frame_buffer, min_x, min_y, max_y - min_y + 1, colored)
        self.draw_vertical_line(frame_buffer, max_x, min_y, max_y - min_y + 1, colored)


    def draw_filled_rectangle(self, frame_buffer, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        for i in range(min_x, max_x + 1):
            self.draw_vertical_line(frame_buffer, i, min_y, max_y - min_y + 1, colored)

    def clear_frame(self, frame_buffer_black, frame_buffer_red=None):
        for i in range(int(self.width * self.height / 8)):
            frame_buffer_black[i] = 0xFF
            if frame_buffer_red is not None:
                frame_buffer_red[i] = 0xFF
