import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rc_context


cc = plt.rcParams['axes.prop_cycle'].by_key()['color']
_TeX_size_dic = {'pt':72.27, 'mm':25.4, 'cm':2.54, 'ex':16.78534,
                 'em':7.22699, 'bp':72, 'dd':67.54151, 'pc':6.02250}

def candlestick(ax, df, dt, c_bear='r', c_bull='g'):
    color = np.where(df.close > df.open, c_bull, c_bear)
    for r in range(len(df)):
        if r < len(df)-1:
            x1, x3 = df.index[r], df.index[r+1]
        else:
            x1, x3 = df.index[-1], df.index[-1]+dt
        x2 = pd.DatetimeIndex([x1, x3]).mean()
        ax.plot([x2, x2], [df.low[r], df.high[r]],
                  lw=1.5, c='black', solid_capstyle='round', zorder=1)
        rect = mpl.patches.Rectangle((x1, df.open[r]), x3-x1,
                                     (df.close[r]-df.open[r]),
                                     facecolor=color[r], edgecolor='black',
                                     lw=1.5, zorder=2)
        ax.add_patch(rect)
    return


def x1_to_x2(x, x1, x2):
    x1 = np.asarray(x1).flatten()
    x2 = np.asarray(x2).flatten()
    if x in x1:
        return x2[x1.index(x)]
    index = bisect(x1, x)
    if index == len(x1):
        index -= 1
    if index == 0:
        index += 1
    b = x2[index-1]
    t = x-x1[index-1]
    m = (x2[index]-b)/(x1[index]-x1[index-1])
    return m*t+b


def set_figsize(width, height=None, unit='pt', ratio=(1+5.**0.5)/2.):
    """
    Arguments:
        width_in_pt: figure width in points

    Keyword arguments:
        ratio: the width over height ratio (default: golden ratio)
        height_in_pt: figure height in points (overrides ratio)
        unit: unit of width (pt [default], in, pc, cm, mm, px, or em)

    Notes:
        ^ 1 in = 72 pt

    Returns:
        tuple (fig_width, fig_height) in inches
    """
    # width in inches
    fig_width = width/_TeX_size_dic[unit]
    # height in inches
    if height is None:
        fig_height = fig_width/ratio
    else:
        fig_height = height/_TeX_size_dic[unit]
    return (fig_width, fig_height)

_fontsize0 = 10
_color0 = 'white'
_color1 = 'black'

_rcParams = {
    'mathtext.fontset': 'stix',
    'font.family':'sans-serif',
    'font.style':'normal',
    'font.weight':'bold',
    'font.size':_fontsize0,
    'axes.labelsize':_fontsize0,
    'axes.linewidth':1.5,
    'axes.titlesize':1.4*_fontsize0,
    'axes.labelweight':'bold',
    'figure.facecolor':_color0,
    'axes.facecolor':_color0,
    'axes.edgecolor':_color1,
    'axes.labelcolor':_color1,
    'text.color':_color1,
    'xtick.color':_color1,
    'ytick.color':_color1,
}
mpl.rcParams.update(_rcParams)