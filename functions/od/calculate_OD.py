from pgc_macro_with_OD import pgc
# import Instruments.RedPitaya.RedPitaya
import numpy as np
# from matplotlib import pyplot as plt


class OD_exp:
    def calculate_OD(self, beam_radius, times, trigger_times, OD_trace, wvlngth=780):
        """

        :param first_puulse_begin:
        :param first_pulse_end:
        :param second_pulse_begin:
        :param second_pulse_end:
        :return:
        """
        self.trig1_strt = np.where(times < trigger_times[0])[0][-1]
        self.trig1_end  = np.where(times < trigger_times[1])[0][-1]
        self.trig2_strt = np.where(times < trigger_times[2])[0][-1]
        self.trig2_end  = np.where(times < trigger_times[3])[0][-1]
        self.frst_plse_avg_pwr = np.mean(OD_trace[self.trig1_strt:self.trig1_end])
        self.scnd_plse_avg_pwr = np.mean(OD_trace[self.trig2_strt:self.trig2_end])
        self.OD = (2 * (np.pi ** 2) / 3) * ((beam_radius / wvlngth) ** 2) * np.log(self.frst_plse_avg_pwr / self.scnd_plse_avg_pwr)
        return self.OD

    def calculate_Nat(self, trigger_times, times, OD_trace):
        if (trigger_times[1]-trigger_times[0] <= 0) or (trigger_times[3]-trigger_times[2] <= 0) or (trigger_times[2]-trigger_times[1] < 0):
            print("Cursors are wrongly positioned")
            return 0
        self.trig1_strt = np.where(times < trigger_times[0])[0][-1]
        self.trig1_end = np.where(times < trigger_times[1])[0][-1]
        self.trig2_strt = np.where(times < trigger_times[2])[0][-1]
        self.trig2_end = np.where(times < trigger_times[3])[0][-1]
        d1 = np.array(OD_trace[self.trig1_strt:self.trig1_end])
        d2 = np.array(OD_trace[self.trig2_strt:self.trig2_end])
        s = 75263  # sensitivity in V/W
        h = 6.62607004e-34  # planck's constant
        THz = 1e12
        fl = 384.2304844685 * THz  # Laser frequency
        res = (np.average(d2)- np.average(d1))/s/2/h/fl * (trigger_times[1] - trigger_times[0])*1e-6
        return res

    def tominimizeNat(self, b, a, d, OD_trace):
        a=int(a)
        b=int(b)
        d=int(d)
        d1 = np.array(OD_trace[a:a+d])
        d2 = np.array(OD_trace[b:b+d])
        s = 75263  # sensitivity in V/W
        h = 6.62607004e-34  # planck's constant
        THz = 1e12
        fl = 384.2304844685 * THz  # Laser frequency
        res = (np.average(d2) - np.average(d1)) / s / 2 / h / fl * d / 125e6
        return np.abs(res)

