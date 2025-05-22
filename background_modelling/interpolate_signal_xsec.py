import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# compute xsec, selection efficiency interpolation
masses = np.array([1, 3.1, 5, 5.5, 6, 6.5])
effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550]) # %
effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])
xsecs = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
xsecs_err = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

# fit effs vs masses with polynomial
def poly(x, *args):
    """
    Polynomial function for curve fitting.
    """
    return np.polyval(args, x)

# effs
popt, _ = curve_fit(lambda x, a, b, c, d : poly(x, a, b, c, d), masses, effs, sigma=effs_err, absolute_sigma=True)
# plot data and fit curve
x = np.linspace(np.min(masses), np.max(masses), 1000)
y = poly(x, *popt)
# plot
plt.errorbar(masses, effs, yerr=effs_err, fmt='o', markersize=3, label='data with error bars', capsize=3)
plt.plot(x, y, '-', label='fit')
# plot error bars

plt.xlabel('mass [GeV]')
plt.ylabel('efficiency [%]')
plt.legend()
plt.title("Selection efficiency vs mass")
plt.savefig(f"signal_efficiency_fit.png")
plt.close()

# fit xsecs vs masses with polynomial
popt2, _ = curve_fit(lambda x, a, b, c, d, e : poly(x, a, b, c, d, e), masses, xsecs, sigma=xsecs_err, absolute_sigma=True)
# plot data and fit curve
x2 = np.linspace(np.min(masses), np.max(masses), 1000)
y2 = poly(x2, *popt2)
# plot
plt.errorbar(masses, xsecs, yerr=xsecs_err, fmt='o', markersize=3, label='data with error bars', capsize=3)
plt.plot(x2, y2, '-', label='fit')
# plot error bars
plt.xlabel('mass [GeV]')
plt.ylabel('xsec [pb]')
plt.legend()
plt.title("Cross section vs mass")
plt.savefig(f"signal_xsec_fit.png")