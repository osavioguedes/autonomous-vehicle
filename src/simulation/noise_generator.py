import random
import math

class NoiseGenerator:
    
    def __init__(self, std_dev: float = 0.1, seed: int = None):
        self._std_dev = std_dev
        if seed is not None:
            random.seed(seed)
    
    def add_noise(self, value: float) -> float:
        noise = random.gauss(0.0, self._std_dev)
        return value + noise
    
    def add_noise_array(self, values: list) -> list:
        return [self.add_noise(v) for v in values]
    
    def set_std_dev(self, std_dev: float) -> None:
        self._std_dev = std_dev
    
    def get_std_dev(self) -> float:
        return self._std_dev

class MultiChannelNoise:
    
    def __init__(self, std_devs: dict):
        self._generators = {
            channel: NoiseGenerator(std_dev) 
            for channel, std_dev in std_devs.items()
        }
    
    def add_noise(self, channel: str, value: float) -> float:
        if channel not in self._generators:
            return value
        return self._generators[channel].add_noise(value)
    
    def add_noise_dict(self, values: dict) -> dict:
        return {
            channel: self.add_noise(channel, value)
            for channel, value in values.items()
        }
