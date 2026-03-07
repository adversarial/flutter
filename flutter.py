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

import collections
import uasyncio as asyncio
from utime import ticks_ms, ticks_diff
from machine import Pin

class flutter:
    REFRESH_RATE = 250 # ms
    def __init__(self, led_pin = Pin("LED", Pin.OUT, value=0)):
        self._led = led_pin
        self._current_tasks = collections.deque((), 16)
        self._blink_lock = asyncio.Lock()
        self._schedule_lock = asyncio.Lock()
 
# period_ms: amount of time to blink light, should be lower than TICKS_MAX (undocumented)
# rate_ms: how often to toggle light
    async def _blink_task(self, period_ms, rate_ms):
        try:
            await self._blink_lock.acquire()
            self._led.off()
            begin_ticks = ticks_ms()
            while ticks_diff(ticks_ms(), begin_ticks) < period_ms or period_ms == -1:
                if rate_ms == 0:
                        self._led.on()
                        await asyncio.sleep_ms(period_ms if period_ms != -1 else flutter.REFRESH_RATE)
                elif rate_ms == -1:
                    self._led.off()
                    await asyncio.sleep_ms(period_ms if period_ms != -1 else flutter.REFRESH_RATE)
                else:
                    self._led.toggle()
                    await asyncio.sleep_ms(rate_ms)
        except asyncio.CancelledError as e:
            raise e
        finally:
            self._led.off()
            if self._blink_lock.locked():
                self._blink_lock.release()

    async def _blink(self, period_ms = 7500, rate_ms = 750, override = False):
        
        try:
            await self._schedule_lock.acquire()
            if override == True and len(self._current_tasks):
                for _ in range(0, len(self._current_tasks)):
                    t = self._current_tasks.pop()
                    t.cancel()
            if not period_ms:
                return
            # task is not guaranteed to execute immediately
            new_task = asyncio.create_task(self._blink_task(period_ms, rate_ms))
            await asyncio.sleep(0) # allow task switch
            self._current_tasks.appendleft(new_task)
        finally:
            if self._schedule_lock.locked():
                self._schedule_lock.release()

    def blink(self, period_ms = 7500, rate_ms = 750, override = False):
        asyncio.create_task(self._blink(period_ms, rate_ms, override))

    def on(self):
        asyncio.create_task(self._blink(-1, 0, True))

    def cancel(self):
        asyncio.create_task(self._blink(0, 0, True))

    def tasks(self):
        return self._current_tasks
    
# #test included:

async def test():
    from machine import reset
    
    onboard_led = flutter()
    # blink some morse code
    onboard_led.blink(1500, 300)
    onboard_led.blink(3000, -1)
    onboard_led.blink(3000, 700)
    onboard_led.blink(3000, -1)
    onboard_led.blink(1500, 300)
    onboard_led.blink(3000, -1)
    # near end, cancel 
    await asyncio.sleep(14)
    onboard_led.blink(-1, 100, True)
    await asyncio.sleep(5)
    onboard_led.on()
    await asyncio.sleep(5)
    onboard_led.cancel()
    onboard_led.blink(3000, 300, True)
    await asyncio.sleep(5)
    reset()

if __name__ == "__main__":
    asyncio.run(test())
