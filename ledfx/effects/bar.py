from ledfx.effects.audio import AudioReactiveEffect
from ledfx.effects.gradient import GradientEffect
from ledfx.color import GRADIENTS
import voluptuous as vol
import numpy as np

class BarAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Bar"
    CONFIG_SCHEMA = vol.Schema({
        vol.Optional('gradient_name', description='Color scheme of bar', default = 'Spectral'): vol.In(list(GRADIENTS.keys())),
        vol.Optional('mode', description='Movement of bar', default = 'wipe'): vol.In(list(["bounce", "wipe", "in-out"])),
        vol.Optional('ease_method', description='Acceleration profile of bar', default='ease_out'): vol.In(list(["ease_in_out", "ease_in", "ease_out", "linear"])),
    })

    def config_updated(self, config):
        self.phase = 0
        self.color_idx = 0

    def audio_data_updated(self, data):
        # Run linear beat oscillator through easing method
        if self._config["ease_method"] == "ease_in_out":
            x = 0.5*np.sin(np.pi*(data.beat_oscillator-0.5))+0.5
        elif self._config["ease_method"] == "ease_in":
            x = data.beat_oscillator**2
        elif self._config["ease_method"] == "ease_out":
            x = -(data.beat_oscillator-1)**2+1
        elif self._config["ease_method"] == "linear":
            x = data.beat_oscillator

        # Compute position of bar start and stop
        if self._config["mode"] == "wipe":
            if data.beat_now:
                self.phase = 1-self.phase # flip flop 0->1, 1->0
                if self.phase == 0:
                    self.color_idx += 0.125 # 8 colours, 4 beats to a bar
                    self.color_idx = self.color_idx % 1 # loop back to zero
            if self.phase == 0:
                bar_end = x
                bar_start = 0
            elif self.phase == 1:
                bar_end = 1
                bar_start = x

        elif self._config["mode"] == "bounce":
            bar_len = 0.3
            if data.beat_now:
                self.phase = 1-self.phase # flip flop 0->1, 1->0
                self.color_idx += 0.125 # 8 colours, 4 beats to a bar
                self.color_idx = self.color_idx % 1 # loop back to zero
            x = x*(1-bar_len)
            if self.phase == 0:
                bar_end = x+bar_len
                bar_start = x
            elif self.phase == 1:
                bar_end = 1-x
                bar_start = 1-(x+bar_len)

        elif self._config["mode"] == "in-out":
            if data.beat_now:
                self.phase = 1-self.phase # flip flop 0->1, 1->0
                if self.phase == 0:
                    self.color_idx += 0.125 # 8 colours, 4 beats to a bar
                    self.color_idx = self.color_idx % 1 # loop back to zero
            if self.phase == 0:
                bar_end = x
                bar_start = 0
            elif self.phase == 1:
                bar_end = 1-x
                bar_start = 0
        
        # Construct the bar
        color = self.get_gradient_color(self.color_idx)
        p = np.zeros(np.shape(self.pixels))
        p[int(self.pixel_count*bar_start):int(self.pixel_count*bar_end), :] = color

        # Update the pixel values
        self.pixels = p