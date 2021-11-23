
import numpy as np

class SimulatorSamples(object):
    def __init__(self, controllers):
        for k, v in controllers.items():
            self.__setattr__(k, v)

    @staticmethod
    def from_np_array(arr: np.ndarray):
        controllers = dict()
        for col in arr.dtype.names:
            parts = col.split(":")
            controller = controllers.setdefault(parts[0], {'analog': dict(), 'digital': dict()})
            controller[parts[1]][parts[2]] = arr[col]
        res = dict()
        for item in controllers.items():
            res[item[0]] = SimulatorControllerSamples(item[1]['analog'], item[1]['digital'])
        return SimulatorSamples(res)


class SimulatorControllerSamples(object):
    def __init__(self, analog, digital):
        self.analog = analog
        self.digital = digital

    def plot(self, analog_ports=None, digital_ports=None):
        import matplotlib.pyplot as plt
        for port, samples in self.analog.items():
            if analog_ports is None or port in analog_ports:
                plt.plot(samples, label=f"Analog {port}")
        for port, samples in self.digital.items():
            if digital_ports is None or port in digital_ports:
                plt.plot(samples, label=f"Digital {port}")
        plt.xlabel("Time [ns]")
        plt.ylabel("ADC")
        plt.legend()

