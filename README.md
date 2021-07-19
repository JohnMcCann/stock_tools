# Security Scraper
Fetches [Yahoo Fianance](https://finance.yahoo.com)'s (YF) prices, and fundamental data for publically traded securities via the YF API. Properly parses time intervals to trading market time. Timeseries data is stored in a pandas dataframe for techincal analysis. Capable of running analysis on multiple tickers simultaneously. While YF has option data, it has not yet been implimented.

### Technical analysis aviable:
- [On-Balance Volume](https://en.wikipedia.org/wiki/On-balance_volume) (OBV)
- [Moving Average](https://en.wikipedia.org/wiki/Moving_average) (MA)
- [Exponential Moving Average](https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average) (EMA)
- [Moving Average Convergence/Divergence](https://en.wikipedia.org/wiki/MACD) (MACD)
- [Return On Investment](https://en.wikipedia.org/wiki/Return_on_investment) (ROI)
- [Relative Change](https://en.wikipedia.org/wiki/Relative_change_and_difference) (RC)
- [Pivot points](https://en.wikipedia.org/wiki/Pivot_point_(technical_analysis))

### Getting started
A Jupyter Notebook is provide with example of how basic functions of the module are used. The project is meant to serve as a starting point for more detail analysis, or basic free analysis for hobbist traders.

### Exmaple analysis plots
![LMT candle plot](https://github.com/JohnMcCann/stock_tools/wiki/images/LMT_candle.png)

![PLTR support/resistence line](https://github.com/JohnMcCann/stock_tools/wiki/images/PLTR_pivots.png)

![PLTR MACD statistic](https://github.com/JohnMcCann/stock_tools/wiki/images/PLTR_MACD.png)
