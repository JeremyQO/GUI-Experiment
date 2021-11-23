from qm.qua import AnalogMeasureProcess


class Process(object):
    def __init__(self, process_type):
        self.loc = ""
        self._process_type = process_type

    def __new__(cls, process_type):
        if cls is Process:
            raise TypeError("base class may not be instantiated")
        return object.__new__(cls)

    def full(self, iw, target, element_output=""):
        analog_target = AnalogMeasureProcess.ScalarProcessTarget(self.loc, target)
        return self._process_type(self.loc, element_output, iw, analog_target)

    def sliced(self, iw, target, samples_per_chunk: int, element_output=""):
        analog_time_division = AnalogMeasureProcess.SlicedAnalogTimeDivision(self.loc, samples_per_chunk)
        analog_target = AnalogMeasureProcess.VectorProcessTarget(self.loc, target, analog_time_division)
        return self._process_type(self.loc, element_output, iw, analog_target)

    def accumulated(self, iw, target, samples_per_chunk: int, element_output=""):
        analog_time_division = AnalogMeasureProcess.AccumulatedAnalogTimeDivision(self.loc, samples_per_chunk)
        analog_target = AnalogMeasureProcess.VectorProcessTarget(self.loc, target, analog_time_division)
        return self._process_type(self.loc, element_output, iw, analog_target)

    def moving_window(self, iw, target, samples_per_chunk: int, chunks_per_window: int, element_output=""):
        analog_time_division = AnalogMeasureProcess.MovingWindowAnalogTimeDivision(self.loc,
                                                                                   samples_per_chunk,
                                                                                   chunks_per_window)
        analog_target = AnalogMeasureProcess.VectorProcessTarget(self.loc, target, analog_time_division)
        return self._process_type(self.loc, element_output, iw, analog_target)


class Demod(Process):
    __instance = None

    def __init__(self):
        super().__init__(AnalogMeasureProcess.DemodIntegration)

    def __new__(cls):
        if Demod.__instance is None:
            Demod.__instance = object.__new__(cls)
        return Demod.__instance


class BareIntegration(Process):
    __instance = None

    def __init__(self):
        super().__init__(AnalogMeasureProcess.BareIntegration)

    def __new__(cls):
        if BareIntegration.__instance is None:
            BareIntegration.__instance = object.__new__(cls)
        return BareIntegration.__instance


demod = Demod()
integration = BareIntegration()
