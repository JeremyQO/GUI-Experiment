from scipy import optimize,spatial
from scipy.signal import find_peaks

class multipleLorentziansFitter():
    def __init__(self, xData,yData, valleys = False, peak_distance = 20, peak_prominence = 0.002, peak_width = 5):
        self.xData = xData
        self.yData = yData if not valleys else (-yData)
        self.peaks_indices, self.peaks_properties = find_peaks(self.yData, distance=peak_distance,prominence=peak_prominence,width=peak_width)
        self.popt = self.fitMultipleLorentzians(xData, yData, self.peaks_indices, self.peaks_properties['widths'])
        print(self.multipleLorentziansParamsToText(self.popt))


    def fitMultipleLorentzians(self,xData,yData, peaks_indices ,peaks_init_width):
        # xData, yData = self.xData, self.yData
        # -- fit functions ---
        def lorentzian(x, x0, a, gam):
            return a * gam ** 2 / (gam ** 2 + (x - x0) ** 2)

        def multi_lorentz_curve_fit(x, *params):
            shift = params[0]  # Scalar shift
            paramsRest = params[1:]  # These are the atcual parameters.
            assert not (len(paramsRest) % 3)  # makes sure we have enough params
            return shift + sum([lorentzian(x, *paramsRest[i: i + 3]) for i in range(0, len(paramsRest), 3)])

        # -------- Begin fit: --------------
        pub = [0.5, 1.5]  # peak_uncertain_bounds
        startValues = []
        for k, i in enumerate(peaks_indices):
            startValues += [xData[i], yData[i], peaks_init_width[k] / 2]
        lower_bounds = [-20] + [v * pub[0] for v in startValues]
        upper_bounds = [20] + [v * pub[1] for v in startValues]
        bounds = [lower_bounds, upper_bounds]
        startValues = [min(yData)] + startValues  # This is the constant from which we start the Lorentzian fits - ideally, 0
        self.popt, self.pcov = optimize.curve_fit(multi_lorentz_curve_fit, xData, yData, p0=startValues, maxfev=50000)
        #ys = [multi_lorentz_curve_fit(x, popt) for x in xData]
        return (self.popt)

    def multipleLorentziansParamsToText(self, popt):
        text = ''
        params = popt[1:] # first param is a general shift
        for i in range(0, len(params), 3):
            text += 'X_0' +' = %.2f; ' % params[i]
            text += 'I = %.2f; ' % params[i +1]
            text += 'gamma' + ' = %.2f \n' %  params[i + 2]
        return (text)