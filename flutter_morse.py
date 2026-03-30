# Released under the MIT License (MIT)
# Copyright (c) 2026 adversarial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from flutter import flutter
import uasyncio as asyncio
from machine import Pin

class morse_character:
    
    alphabet = {
        'a': '.-'   , 'b': '-...' , 'c': '-.-.' , 'd': '-..'  , 'e': '.'    ,
        'f': '..-.' , 'g': '--.'  , 'h': '....' , 'i': '..'   , 'j': '.---' , 
        'k': '-.-'  , 'l': '.-..' , 'm': '--'   , 'n': '-.'   , 'o': '---'  ,
        'p': '.--.' , 'q': '--.-' , 'r': '.-.'  , 's': '...'  , 't': '-'    ,
        'u': '..-'  , 'v': '...-' , 'w': '.--'  , 'x': '-..-' , 'y': '-.--' ,
        'z': '--..' , 
        '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
        '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
        ' ': '       ',
        '.': '.-.-.-', ',': '--..--', '?': '..--..', '=': '-...-', '-': '-....-',
        '/': '-..-.', '@': '.--.-.'
    }

    STOP = '.-.-.' # end of message
    END = '...-.-' # end of tranmsission
    VERIFIED = '...-.'
    BREAK = '-...-'
    ATTENTION = '-.-.-'

    def __init__(self, c):
        self._c = morse_character.alphabet[c]

    def __iter__(self):
        return iter(self._c)

class flutter_morse(flutter):

    def __init__(self, led_pin = Pin("LED", Pin.OUT, value=0)):
        return super().__init__(led_pin)

    def emit(self, str, wpm = 20):
        pattern = [morse_character(c) for c in str if c in morse_character.alphabet]

    async def _blink_task(self, blink_sequence, wpm, count):
        dit_ms = int(1200 / wpm)
        dash_ms = dit_ms * 3
        between_letter_ms = dit_ms * 3
        
        try:
            await self._blink_lock.acquire()
            self._led.off()

            for z in range(count):
                for i, morse_char in enumerate(blink_sequence, start = 1):
                    for d in morse_char:
                        if d == '.':
                            self._led.on()
                            await asyncio.sleep_ms(dit_ms)
                            self._led.off()
                        elif d == '-':
                            self._led.on()
                            await asyncio.sleep_ms(dash_ms)
                            self._led.off()
                        elif d == ' ':
                            self._led.off()
                            await asyncio.sleep_ms(dit_ms)
    # all characters should have 3 dit length gap
                    if i != len(blink_sequence):
                        await asyncio.sleep(between_letter_ms)

        except asyncio.CancelledError as e:
            raise e
        finally:
            if self._blink_lock.locked():
                self._led.off()
                self._blink_lock.release()

    async def _blink(self, phrase = "sos", wpm = 20, count = 1, override = False):
        
        try:
            await self._schedule_lock.acquire()
            if override == True:
                self._clear_tasks()
            if not count:
                return
            # task is not guaranteed to execute immediately
            new_task = asyncio.create_task(self._blink_task(phrase, wpm, count))
            await asyncio.sleep(0) # allow task switch maybe
            self._current_tasks.appendleft(new_task)
        finally:
            if self._schedule_lock.locked():
                self._schedule_lock.release()