import numpy as np
from scipy.signal import find_peaks


class NAtoms:
    def calculate_Nat(self, cursor_times, times, trace, avg_photons=2, sensitivity=7081.1):
        """
        :param cursor_times: position of the cursors within which to estimate the number of atoms. Same units as 'times'
        :param times: x axis
        :param trace: data trace
        :param avg_photons: average number of scattered photon per atom. For sigma/pi on the 1->0', equals 1.5.
        :param sensitivity: Sensitivity of the photodetector in V/W
        :return: Absolute number of atoms in millions
        """
        if (cursor_times[1]-cursor_times[0] <= 0) or (cursor_times[3]-cursor_times[2] <= 0) or (cursor_times[2]-cursor_times[1] < 0):
            print("Cursors are wrongly positioned")
            return 0
        self.trig1_strt = np.where(times < cursor_times[0])[0][-1]
        self.trig1_end = np.where(times < cursor_times[1])[0][-1]
        self.trig2_strt = np.where(times < cursor_times[2])[0][-1]
        self.trig2_end = np.where(times < cursor_times[3])[0][-1]
        d1 = np.array(trace[self.trig1_strt:self.trig1_end])
        d2 = np.array(trace[self.trig2_strt:self.trig2_end])

        # sensitivity = 75263  # sensitivity in V/W
        h = 6.62607004e-34  # planck's constant
        THz = 1e12
        fl = 384.2304844685 * THz  # Laser frequency
        res = (np.average(d2)-np.average(d1))/sensitivity/avg_photons/h/fl * (cursor_times[1]-cursor_times[0])*1e-6
        return res


    def get_delay(self, data):
        datamax = data.max()
        datamin = data.min()
        dataclipped = np.array([max(min(el,datamax/2.0), datamin+(datamax-datamin)/8) for el in data])-(datamin+(datamax-datamin)/8)
        corr = np.correlate(dataclipped, dataclipped, mode='same')
        peaks, _ = find_peaks(corr, height=0)
        return peaks[1] - peaks[0]

