"""
yf_price.py
    Contains price_data which is the object that contains the price data
    and contains analysis methods.
"""
import numpy as np
import pandas as pd

from yf_fetcher import yf_fetcher
from utils import *
from plot_utils import candlestick


class price_data:
    def __init__(self, symbols, period1, period2, interval,
                 PrePost=False, div=False, split=False):
        """
        Description:
            Fetches the price data from yahoo finance and returns the
            results in a pandas dataframe. Class contains a few basic
            analysis tools. Capable of running analysis over multiple
            securities.

        Arguments:
            symbols: list of stock tickers to fetch prices of
            period1: first date to fetch prices
            period2: last date to fetch prices
            interval: one of YF's data intervals, e.g., '1d'

        Keyword arguments:
            PrePost: include pre and post market data (boolean)
            div: include dividend data (boolean)
            split: include split data (boolean)
        """
        if (type(symbols) is list and
            all(type(symbol) is str for symbol in symbols)):
            self.multiple = True
        else:
            self.multiple = False
        self.symbols = symbols
        self.period1 = period1
        self.period2 = period2
        self.interval = interval
        self.PrePost = PrePost
        self.div = div
        self.split = split
        self.fethcer = yf_fetcher()
        self.meta, self.data = self.fethcer.fetch_price_history(
            symbols, period1, period2, interval,
            PrePost=PrePost, div=div, split=split
        )
        self.pivot_meta, self.pivot_data = None, None
        self.ddt = pd.to_timedelta(self.fethcer._seconds_in_interval[interval],
                                   unit='s')
        return


    def OBV(self, normalize=True):
        """
        Description:
            On Balance Volume (OBV) is added to dataframe.

        Keyword arguments:
            normalize: normalize OBV between [-1, 1] (boolean)

        Reference:
            https://www.investopedia.com/terms/o/onbalancevolume.asp
        """
        if self.multiple:
            for sym in self.symbols:
                self.data[sym]['OBV'] = np.zeros(len(self.data[sym]))
                yesterday_close = self.data[sym]['close'].iloc[0]
                for d, date in enumerate(self.data[sym].index[1:], start=1):
                    self.data[sym]['OBV'].iat[d] = (
                        self.data[sym]['OBV'].iloc[d-1])
                    if self.data[sym]['close'].iloc[d] > yesterday_close:
                        self.data[sym]['OBV'].iat[d] += (
                            self.data[sym]['volume'].iloc[d])
                    elif self.data[sym]['close'].iloc[d] < yesterday_close:
                        self.data[sym]['OBV'].iat[d] -= (
                            self.data[sym]['volume'].iloc[d])
                if normalize:
                    self.data[sym]['OBV'] /= self.data[sym].OBV.abs().max()
        else:
            self.data['OBV'] = np.zeros(len(self.data))
            yesterday_close = self.data['close'].iloc[0]
            for d, date in enumerate(self.data.index[1:], start=1):
                self.data['OBV'].iat[d] = self.data['OBV'].iloc[d-1]
                if self.data['close'].iloc[d] > yesterday_close:
                    self.data['OBV'].iat[d] += self.data['volume'].iloc[d]
                elif self.data['close'].iloc[d] < yesterday_close:
                    self.data['OBV'].iat[d] -= self.data['volume'].iloc[d]
            if normalize:
                self.data['OBV'] /= self.data.OBV.abs().max()
        return


    def MA(self, window, var='close', win_type=None, **win_kwargs):
        """
        Description:
            Moving Average (MA) is added to dataframe.

        Arguments:
            window: number of lagging points used in average

        Keyword arguments:
            var: variable to calcualte MA
            win_type: scipy window type (None is Simple Moving Average)
            win_kwargs: arguments for window type
        """
        self.MA_window = window
        if self.multiple:
            for sym in self.symbols:
                self.data[sym]['MA'] = (
                    self.data[sym][var].rolling(window, win_type=win_type)
                    .mean(**win_kwargs))
        else:
            self.data['MA'] = self.data[var].rolling(
                window, win_type=win_type).mean(**win_kwargs)
        return


    def EMA(self, span, var='close'):
        """
        Description:
            Exponential Moving Average (EMA) is added to dataframe.

        Arguments:
            span: smoothing factor is 2/(span+1)

        Keyword arguments:
            var: variable to calcualte EMA
        """
        self.EMA_span = span
        if self.multiple:
            for sym in self.symbols:
                self.data[sym]['EMA'] = (
                    self.data[sym][var].ewm(span=span).mean())
        else:
            self.data['EMA'] = self.data[var].ewm(span=span).mean()
        return


    def MACD(self, short_span=12, long_span=26, signal_span=9, normalize=True):
        """
        Description:
            Moving Average Convergence/Divergence (MACD) added to dataframe.

        Keyword arguments:
            short_span: short-term span
            long_span: long-term span
            signal_span: signal span
            normalize: normalize MACD-signal between [-1, 1] (boolean)

        Notes:
            ^smoothing factor of EMA is 2/(span+1)

        Reference:
            https://www.investopedia.com/terms/m/macd.asp
        """
        if self.multiple:
            for sym in self.symbols:
                self.data[sym]['MACD'] = (
                    self.data[sym]['close'].ewm(span=short_span).mean()
                    -self.data[sym]['close'].ewm(span=long_span).mean()
                )
                self.data[sym]['MACD_EMA'+str(signal_span)] = (
                    self.data[sym]['MACD'].ewm(span=signal_span).mean())
                self.data[sym]['MACD_sig'] = (
                    self.data[sym]['MACD']
                    -self.data[sym]['MACD_EMA'+str(signal_span)])
                if normalize:
                    self.data[sym]['MACD_sig'] /= (
                        self.data[sym].MACD_sig.abs().max())
        else:
            self.data['MACD'] = (self.data['close'].ewm(span=short_span).mean()
                                 -self.data['close'].ewm(span=long_span).mean())
            self.data['MACD_EMA'+str(signal_span)] = (
                self.data['MACD'].ewm(span=signal_span).mean())
            self.data['MACD_sig'] = (self.data['MACD']
                                     -self.data['MACD_EMA'+str(signal_span)])
            if normalize:
                self.data['MACD_sig'] /= self.data.MACD_sig.abs().max()
        return


    def ROI(self):
        """
        Description:
            Return On Investment (ROI) added to dataframe. Assumes zero
            commission.
        """
        if self.multiple:
            for sym in self.symbols:
                if 'adjclose' in self.data[sym].columns:
                    self.data[sym]['ROI'] = (
                        self.data[sym].close/self.data[sym].adjclose[0]-1)
                else:
                    self.data[sym]['ROI'] = (
                        self.data[sym].close/self.data[sym].close[0]-1)
        else:
            if 'adjclose' in self.data.columns:
                self.data['ROI'] = self.data.close/self.data[sym].adjclose[0]-1
            else:
                self.data['ROI'] = self.data.close/self.data.close[0]-1
        return


    def RC(self, var='close'):
        """
        Description:
            Relative Change (RC) added to dataframe. Calculates the relative
            change between intervals.

        Keyword arguments:
            var: variable to calcualte RC
        """
        if self.multiple:
            key = list(self.meta.keys())[0]
            var_i = list(self.data[key].columns).index(var)
            for sym in self.symbols:
                self.data[sym]['RC'] = (
                    [0]+list((self.data[sym].iloc[1:,var_i].values
                              -self.data[sym].iloc[:-1,var_i].values)
                             /self.data[sym].iloc[1:,var_i].values)
                )
        else:
            var_i = list(self.data.columns).index(var)
            self.data['RC'] = (
                [0]+list((self.data.iloc[1:,var_i].values
                          -self.data.iloc[:-1,var_i].values)
                         /self.data.iloc[1:,var_i].values)
            )
        return


    def pivot_points(self, pivot_interval=None, pivot_kind='HLC'):
        """
        Description:
            7-point pivot system is calculated based on pivoting interval.
            Pivot interval can be set or guessed from data interval. A
            secondary dataframe with the pivot price history is generated,
            and contains pivot, support, and resistance points.

        Keyword arguments:
            pivot_interval: Set the interval used for pivot calualtion
            pivot_kind: String of variables averaged for pivot point

        Notes:
            ^pivot_kind string uses: H = high, L = low, O = open,
             and C = close
        """
        if pivot_interval is None:
            if self.interval in self.fethcer._valid_subday_intervals:
                self.pivot_interval = '1d'
                self.pivot_ddt = pd.to_timedelta(1, unit='d')
            elif self.interval in self.fethcer._valid_subweek_intervals:
                self.pivot_interval = '1wk'
                self.pivot_ddt = pd.to_timedelta(1, unit='w')
            elif self.interval in self.fethcer._valid_submonth_intervals:
                self.pivot_interval = '1mo'
                self.pivot_ddt = pd.to_timedelta(30, unit='d') # Ehh
            else:
                print('ERROR: Month interval and longer have no default '
                      'pivot interval.\n'
                      '        Must specify pivot_interval')
                return
        else:
            if pivot_interval not in self.fethcer.valid_intervals():
                print('ERROR: Pivot interval not part of YF data\n'
                      '       Might have to compile it yourself.')
                return
            s2i_dict = self.fethcer._seconds_in_interval
            if s2i_dict[pivot_interval] <= s2i_dict[self.interval]:
                print('WARNING: Pivot interval shorter than data interval.')
            self.pivot_interval = pivot_interval
            self.pivot_ddt = pd.to_timedelta(s2i_dict[pivot_interval], unit='s')
        # Grab pivot data
        self.pivot_meta, self.pivot_data = self.fethcer.fetch_price_history(
            self.symbols, self.period1, self.period2, self.pivot_interval,
            PrePost=self.PrePost, div=self.div, split=self.split
        )
        self.pivot_kind = pivot_kind
        self.pivot_dict = {'H':'high', 'h':'high', 'L':'low', 'l':'low',
                           'O':'open', 'o':'open', 'C':'close', 'c':'close'}
        
        if self.multiple:
            for sym in self.symbols:
                self.pivot_data[sym]['pivot'] = np.zeros(len(self.pivot_data[sym]))
                for c in self.pivot_kind:
                    self.pivot_data[sym]['pivot'] += (
                        self.pivot_data[sym][self.pivot_dict[c]])
                self.pivot_data[sym]['pivot'] /= len(self.pivot_kind)
                # Prediction times
                t1 = self.pivot_data[sym].index[-1]+self.pivot_ddt
                t2 = t1+self.pivot_ddt
                self.pivot_data[sym]['start'] = (
                    (self.pivot_data[sym].index[1:].append(
                        pd.DatetimeIndex([t1])))
                )
                self.pivot_data[sym]['end'] = (
                    (self.pivot_data[sym].index[2:]).append(
                        pd.DatetimeIndex([t1, t2]))
                )
                self.pivot_data[sym]['S1'] = (2*self.pivot_data[sym]['pivot']
                                              -self.pivot_data[sym]['high'])
                self.pivot_data[sym]['S2'] = (self.pivot_data[sym]['pivot']
                                              +self.pivot_data[sym]['low']
                                              -self.pivot_data[sym]['high'])
                self.pivot_data[sym]['S3'] = (self.pivot_data[sym]['S1']
                                              +self.pivot_data[sym]['low']
                                              -self.pivot_data[sym]['high'])
                self.pivot_data[sym]['R1'] = (2*self.pivot_data[sym]['pivot']
                                              -self.pivot_data[sym]['low'])
                self.pivot_data[sym]['R2'] = (self.pivot_data[sym]['pivot']
                                              -self.pivot_data[sym]['low']
                                              +self.pivot_data[sym]['high'])
                self.pivot_data[sym]['R3'] = (self.pivot_data[sym]['R1']
                                              -self.pivot_data[sym]['low']
                                              +self.pivot_data[sym]['high'])
        else:
            self.pivot_data['pivot'] = np.zeros(len(self.pivot_data))
            for c in self.pivot_kind:
                self.pivot_data['pivot'] += self.pivot_data[self.pivot_dict[c]]
            self.pivot_data['pivot'] /= len(self.pivot_kind)
            # Prediction times
            t1 = self.pivot_data.index[-1]+self.pivot_ddt
            t2 = t1+self.pivot_ddt
            self.pivot_data['start'] = (self.pivot_data.index[1:]).append(
                pd.DatetimeIndex([t1]))
            self.pivot_data['end'] = (self.pivot_data.index[2:]).append(
                pd.DatetimeIndex([t1, t2]))
            self.pivot_data['S1'] = (2*self.pivot_data['pivot']
                                     -self.pivot_data['high'])
            self.pivot_data['S2'] = (self.pivot_data['pivot']
                                     +self.pivot_data['low']
                                     -self.pivot_data['high'])
            self.pivot_data['S3'] = (self.pivot_data['S1']
                                     +self.pivot_data['low']
                                     -self.pivot_data['high'])
            self.pivot_data['R1'] = (2*self.pivot_data['pivot']
                                     -self.pivot_data['low'])
            self.pivot_data['R2'] = (self.pivot_data['pivot']
                                     -self.pivot_data['low']
                                     +self.pivot_data['high'])
            self.pivot_data['R3'] = (self.pivot_data['R1']
                                     -self.pivot_data['low']
                                     +self.pivot_data['high'])
        return


    def plot(self, fig, ax, var, npivots=0, **kwargs):
        """
        Description:
            Adds variable to axis of the figure. Attempts to label lines
            and y-axis (nothing gaurenteed).

        Arguments:
            fig: figure of plot
            ax: axis for plotting
            var: variable to be plotted

        Keyword arguments:
            npivots: Number of pivots to overlay (max 3)
            kwargs: kwargs passed to pd.plot() or candlestick()

        Notes:
            ^var can be 'candle' to plot a candle plot with low/high wicks
             and open/close body
        """
        # Plot with pandas dataframe plot method
        if var == 'candle':
            if self.multiple:
                for sym in self.symbols:
                    candlestick(ax, self.data[sym], self.ddt, **kwargs)
            else:
                candlestick(ax, self.data, self.ddt, **kwargs)
        else:
            if self.multiple:
                for sym in self.symbols:
                    self.data[sym][var].plot(ax=ax, label=sym, **kwargs)
            else:
                self.data[var].plot(ax=ax, **kwargs)
        # If currency based variable add currency ylabel
        if var in ['open', 'close', 'adjclose', 'low', 'high', 'candle']:
            if self.multiple:
                key = list(self.meta.keys())[0]
                ax.set_ylabel(self.meta[key]['currency'])
            else:
                ax.set_ylabel(self.meta['currency'])
        elif self.multiple:
            ax.set_ylabel(var)
        # If single ticker, add ticker as title
        if not self.multiple:
            fig.suptitle(self.symbols, y=0.95, fontweight='bold')
        # Plot pivots
        if npivots:
            if self.pivot_data is None:
                print('ERROR: Must first calculate pivots.')
                return
            color_r = ['#fb6a4a', '#de2d26', '#a50f15']
            color_s = ['#74c476', '#31a354', '#006d2c']
            df = self.pivot_data
            for start, end, sup, res in zip(df.start, df.end,
                                            zip(df.S1, df.S2, df.S3),
                                            zip(df.R1, df.R2, df.R3)):
                for i, s in enumerate(sup):
                    if i < npivots:
                        ax.hlines(s, start, end, lw=1, color=color_s[i],
                                  alpha=1, zorder=-1)
                for i, r in enumerate(res):
                    if i < npivots:
                        ax.hlines(r, start, end, lw=1, color=color_r[i],
                                  alpha=1, zorder=-1)
        # Fix up x-axis dates nicely
        fig.autofmt_xdate()
        return