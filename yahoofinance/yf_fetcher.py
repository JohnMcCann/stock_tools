"""
yf_fetcher.py
    Contains yf_fetcher object, object stores no stock information, simply
    fetches and returns the data.

Useful resources used in project:
    * https://github.com/JECSand/yahoofinancials
    * http://quant.caltech.edu/historical-stock-data.html
    * https://stackoverflow.com/a/47505102/2367317
    * https://help.yahoo.com/kb/finance-for-web/adjusted-close-sln28256.html
"""

import textwrap
import requests
import numpy as np
import pandas as pd

from utils import *


class yf_fetcher:
    """
    Yahoo Finance Fetcher (yff)
        Object that interfaces with the Yahoo Finance API to fetch data.
    """
    
    _yahoo_url = 'https://query1.finance.yahoo.com'
    _options_url = _yahoo_url+'/v7/finance/options/'
    _price_url = _yahoo_url+'/v8/finance/chart/'
    _fundamental_url = _yahoo_url+'/v10/finance/quoteSummary/'
    
    _valid_subday_intervals = ['1m', '2m', '5m', '15m',
                               '30m', '60m', '90m', '1h']
    _valid_subweek_intervals = _valid_subday_intervals+['1d', '5d']
    _valid_submonth_intervals = _valid_subweek_intervals+['1wk']
    _valid_subyear_intervals = _valid_submonth_intervals+['1mo', '3mo']
    
    _seconds_in_interval = {'1m':60, '2m':120, '5m':300, '15m':900, '30m':1800,
                            '60m':3600, '90m':5400, '1h':3600, '1d':86400,
                            '5d':432000, '1wk':604800, '1mo':2592000,
                            '3mo':7776000}
    
    _valid_modules = ['assetProfile', 'summaryProfile', 'summaryDetail',
                      'esgScores', 'price', 'incomeStatementHistory',
                      'incomeStatementHistoryQuarterly', 'balanceSheetHistory',
                      'balanceSheetHistoryQuarterly',
                      'cashflowStatementHistory',
                      'cashflowStatementHistoryQuarterly',
                      'defaultKeyStatistics', 'financialData', 'calendarEvents',
                      'secFilings', 'recommendationTrend',
                      'upgradeDowngradeHistory', 'institutionOwnership',
                      'fundOwnership', 'majorDirectHolders',
                      'majorHoldersBreakdown', 'insiderTransactions',
                      'insiderHolders', 'netSharePurchaseActivity', 'earnings',
                      'earningsHistory', 'earningsTrend', 'industryTrend',
                      'indexTrend', 'sectorTrend']

    
    def __init__(self):
        return

    
    def valid_modules(self):
        return self._valid_modules


    def valid_intervals(self):
        return self._valid_subyear_intervals


    def wraprint(self, *args, width=72, indent='  '):
        wrapper = textwrap.TextWrapper(width=width, subsequent_indent=indent)
        text = ''
        for arg in args:
            text += str(arg)+' '
        text = text[:-1]
        paragraph = wrapper.wrap(text=text)
        print(paragraph[0])
        for line in paragraph[1:]:
            print(line) 
        
        
    def error(self, *args):
        self.wraprint('Error:',  *args)
        return 0
        
        
    def fetch_price_history(self, symbols, period1, period2, interval,
                            PrePost=False, div=False, split=False):
        """
        Description:
            Fetches the price history of stocks between two dates at some
            cadance.

        Arguments:
            symbols: list of stock tickers to fetch prices of
            period1: first date to fetch prices
            period2: last date to fetch prices
            interval: one of YF's data intervals, e.g., '1d'

        Keyword arguments:
            PrePost: include pre and post market data (boolean)
            div: include dividend data (boolean)
            split: include split data (boolean)

        Returns:
            tuple of meta data, and pandas dataframe of prices
        """
        if (type(period1) is not int or
            type(period2) is not int or
            type(interval) is not str):
            self.error('')
            return 1

        if type(symbols) is str:
            return self._fetch_price_history(symbols, period1, period2,
                                             interval, PrePost=PrePost, div=div,
                                             split=split)
        elif (type(symbols) is list and
              all(type(symbol) is str for symbol in symbols)):
            meta = {}
            data = {}
            for symbol in symbols:
                m, d = self._fetch_price_history(symbol, period1, period2,
                                                 interval, PrePost=PrePost,
                                                 div=div, split=split)
                if m is None and d is None:
                    continue
                meta.update({symbol: m})
                data.update({symbol: d})
            return meta, data
        else:
            self.error('')
            return 1
        
    def _fetch_price_history(self, symbol, period1, period2, interval,
                             PrePost=False, div=False, split=False,
                             market_tz='America/New_York'):
        """
        Description:
            Fetches the price history of a single stocks between two dates
            at some cadance.

        Arguments:
            symbols: list of stock tickers to fetch prices of
            period1: first date to fetch prices
            period2: last date to fetch prices
            interval: one of YF's data intervals, e.g., '1d'

        Keyword arguments:
            PrePost: include pre and post market data (boolean)
            div: include dividend data (boolean)
            split: include split data (boolean)
            
        Todo:
            -divide nand split data not handled

        Returns:
            tuple of meta data, and pandas dataframe of prices
        """
        # Prevent improper request for intervals yahoo doesn't provide
        if interval not in self._valid_subyear_intervals:
            self.error('interval not valid, must pick from',
                       self._valid_subyear_intervals)
            return None, None
        # Prevent improper request of durations smaller than subday interval
        if (interval in self._valid_subday_intervals and
            period2-period1 < self._seconds_in_interval[interval]):
            self.error('period too short ({:n} s) for given interval timescale'
                       ' ({:n} s)'.format(period2-period1,
                                        self._seconds_in_interval[interval]))
            return None, None
        # Ensure duration bound at least one FTDM for month intervals
        # We have to assume a timezone for the market
        if (interval in ['1mo', '3mo'] and not
            (period1-UT_to_FTDM_UT(period1, timezone=market_tz) < 86400 or
             period2-UT_to_FTDM_UT(period2, timezone=market_tz) >= 0)):
            self.error('interval does not enclose any first trading '
                       'days of the month')
            return None, None
        # Build request url
        xurl = self._price_url
        xurl += ('{:s}?symbol={:s}&period1={:d}&period2={:d}&interval={:s}'
                 .format(symbol, symbol, period1, period2, interval))
        if PrePost:
            xurl += '&includePrePost=true'
        if div or split:
            xurl += '&events='
            if div and split:
                xurl += 'div%2Csplit'
            elif div:
                xurl += 'div'
            else:
                xurl += 'split'
        # send request and check for errors
        try:
            response = requests.get(xurl)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        if response.status_code != 200:
            self.error('{:s} request reponse not okay ({:d} {:s})'
                       .format(symbol, response.status_code,
                        requests.status_codes._codes[response.status_code][0]))
        reponse_json = response.json()
        if list(reponse_json.keys()) != ['chart']:
            self.error(symbol, "return unexpected keys for response:",
                       reponse_json.keys())
            return None, None
        chart = reponse_json['chart']
        if list(chart.keys()) != ['result', 'error']:
            self.error(symbol, "return unexpected keys for chart:",
                       chart.keys())
            return None, None
        if chart['error'] is not None:
            self.wraprint('{:s}: {:s}'
                  .format(chart['error']['code'],
                          chart['error']['description']))
            return None, None
        # If no request errors then grab results
        if len(chart['result']) > 1:
            self.error(symbol, "return more results then expected:",
                       len(chart['result']), " results")
            return None, None
        result = chart['result'][0]
        if not all(elem in list(result.keys())
                   for elem in ['meta', 'timestamp', 'indicators']):
            self.error(symbol, "return unexpected keys for result:",
                       result.keys())
            return None, None
        meta = result['meta']
        exchangeTZ = meta['exchangeTimezoneName']
        timestamp = result['timestamp']
        # Convert unix timestamps to human read dates based on dataGranularity
        if meta['dataGranularity'] in self._valid_subday_intervals:
            date = pd.to_datetime(
                UT_to_str(timestamp, fmt='%Y-%m-%d %H:%M:%S',
                          timezone=exchangeTZ))
        else:
            date = pd.to_datetime(
                UT_to_str(timestamp, fmt='%Y-%m-%d',
                          timezone=meta['exchangeTimezoneName']))
        # If returning dividends or splits check if any occured in time frame
        if div or split:
            if 'events' not in list(result.keys()):
                self.wraprint('Warning {:s}: no events between {:s} and {:s}'
                              .format(symbol,
                                      UT_to_str(period1, timezone=exchangeTZ),
                                      UT_to_str(period2, timezone=exchangeTZ)))
            else:
                events = result['events']
                event_keys = list(events.keys())
                if div and 'dividends' not in event_keys:
                    self.wraprint('Warning {:s}: no dividends events between'
                                  '{:s} and {:s}'.format(symbol,
                                      UT_to_str(period1, timezone=exchangeTZ),
                                      UT_to_str(period2, timezone=exchangeTZ)))
                if split and 'splits' not in event_keys:
                    self.wraprint('Warning {:s}: no split events between'
                                  '{:s} and {:s}'.format(symbol,
                                      UT_to_str(period1, timezone=exchangeTZ),
                                      UT_to_str(period2, timezone=exchangeTZ)))
                if ((div and 'dividends' in event_keys)
                    and (split and 'splits' in event_keys)):
                    dividends = events['dividends']
                    splits = events['splits']
                elif (div and 'dividends' in event_keys):
                    dividends = events['dividends']
                elif (split and 'splits' in event_keys):
                    splits = events['splits']
                else:
                    self.error('Unrecognized event:', event_keys)
        indicators = result['indicators']
        if 'quote' not in list(indicators.keys()):
            self.error('')
            return None, None
        if len(indicators['quote']) > 1:
            self.error(symbol, "return more quotes then expected:",
                       len(indicators['quote']), " quotes")
            return None, None
        quote = indicators['quote'][0]
        if not all(elem in list(quote.keys())
                   for elem in ['high', 'low', 'volume', 'open', 'close']):
            self.error('')
            return None, None
        q_high = quote['high']
        q_low = quote['low']
        q_volume = quote['volume']
        q_open = quote['open']
        q_close = quote['close']
        if 'adjclose' not in list(indicators.keys()):
            # Only issue warning if expected adjclose (superday intervals)
            if interval not in self._valid_subday_intervals:
                self.wraprint('Warning {:s}: expected adjclose on interval {:s}'
                              .format(symbol, interval))
            data = pd.DataFrame(np.column_stack([q_open, q_close, q_low, q_high,
                                                 q_volume]),
                                columns=['open', 'close','low', 'high',
                                         'volume'],
                                index=date)
        else:
            adjclose = indicators['adjclose'][0]['adjclose']
            data = pd.DataFrame(np.column_stack([q_open, q_close, adjclose,
                                                 q_low, q_high, q_volume]),
                                columns=['open', 'close', 'adjclose',
                                         'low', 'high', 'volume'],
                                index=date)
        # subday intervals fetch current price as last data point, we drop that
        if interval in self._valid_subday_intervals:
            data.drop(data.tail(1).index, inplace=True)
        # subday intervals return timestamps uptil current time with null results
        # for data outside period1 and period2, drop these or any other null rows
        data.dropna(inplace=True)
        
        return meta, data

    
    def fetch_fundamentals(self, symbol, modules):
        """
        Description:
            

        Arguements:
            symbol: stock ticker
            modules:

        Notes:
            incomeStatementHistory limited to last 3 years without yahoo premium

        Returns:
            Fundamentals requested
        """
        xurl = self._fundamental_url+symbol+'?modules='
        if type(modules) is str:
            xurl += modules
        elif (type(modules) is list and
              all(type(module) is str for module in modules)):
            for module in modules:
                xurl += '{:s}%2C'.format(module)
        else:
            self.wraprint('modules must be a string or list of strings.')
            return
        response = requests.get(xurl)
        if response.status_code != 200:
            print(response.status_code)
            return
        quoteSummary = response.json()['quoteSummary']
        if quoteSummary['error'] is not None:
            self.wraprint(quoteSummary['error'])
            return
        result = quoteSummary['result'][0]
        return result

    
    def fetch_options(self, symbol, expiration=None):
        """
        NOT WORKING, options_url no good?
        """
        xurl = self._options_url+symbol
        if type(expiration) is int:
            xurl += '?date={:d}'.format(expiration)
        response = requests.get(xurl)
        if response.status_code != 200:
            self.wraprint(response.status_code)
            return
        return response.json() 