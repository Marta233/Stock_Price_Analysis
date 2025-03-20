import pandas as pd
# import plotly.graph_objs as go
from plotly.subplots import make_subplots
import talib as ta
import yfinance as yf
import matplotlib.pyplot as plt
import os
import time
import plotly.graph_objs as go
import matplotlib.dates as mdates

class StockPrice:
    def __init__(self, tickers, start_date, end_date):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.data = {}
        self.merged_data={}


    def download_data(self):
        """
        Downloads historical data for the specified tickers and date range.
        """
        for ticker in self.tickers:
            self.data[ticker] = yf.download(ticker, start=self.start_date, end=self.end_date)
        print("Data downloaded successfully!")

    def save_to_files(self, directory="financial_data"):
        """
        Saves each ticker's data as a separate CSV file in the specified directory,
        ensuring the correct format by removing unnecessary rows and adding a Ticker column.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

        for ticker, df in self.data.items():
            df = df.copy()  # Avoid modifying the original dictionary data
            df.reset_index(inplace=True)  # Ensure 'Date' is a column, not the index
            
            # Remove any extra header row (if present)
            if isinstance(df.columns, pd.MultiIndex):  # If headers are multi-level, flatten them
                df.columns = df.columns.get_level_values(0)
            
            # Ensure columns are correctly named
            expected_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[expected_columns]  # Keep only these columns to remove any unwanted extra headers
            
            # Add a Ticker column
            df['Ticker'] = ticker
            
            # Save cleaned data to a CSV file
            df.to_csv(f"{directory}/{ticker}.csv", index=False)

        print(f"Cleaned data saved to directory: {directory}")

    
    def save_to_merged_file(self, directory="financial_data"):
        """
        Merges all tickers' data into one DataFrame and saves it as a single CSV file.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.merged_data = pd.DataFrame()  # Create an empty DataFrame to store the merged data

        # Loop through each ticker's data and add the 'Ticker' column
        for ticker, df in self.data.items():
            df.reset_index(inplace=True)  # Ensure 'Date' is a column, not the index
            df['Ticker'] = ticker  # Add a new column for the ticker name
            # Ensure columns are correctly named and structured
            df.columns = [ 'Date', 'Open','High','Low', 'Close', 'Volume','Ticker']
            self.merged_data = pd.concat([self.merged_data, df], ignore_index=True)  # Merge the data
            self.merged_data
        # Save the merged data to a CSV file
        self.merged_data.to_csv(f"{directory}/merged_financial_data.csv", index=False)
        print(f"Data merged and saved to {directory}/merged_financial_data.csv")
        return self.merged_data

    def calcu_info(self):
        """Returns information about the merged DataFrame."""
        return self.merged_data.info()

    def plot_stock_subplots(self):
        """Plots subplots for Close, Open, High, and Low prices for each symbol."""
        for symbol in self.tickers:
            symbol_df = self.merged_data[self.merged_data['Ticker'] == symbol]
            fig = make_subplots(rows=1, cols=4, subplot_titles=[
                f'{symbol} Close', f'{symbol} Open', f'{symbol} High', f'{symbol} Low'
            ])
            # Create traces for each price type
            fig.add_trace(go.Scatter(x=symbol_df['Date'], y=symbol_df['Close'], name=f'{symbol} Close'), row=1, col=1)
            fig.add_trace(go.Scatter(x=symbol_df['Date'], y=symbol_df['Open'], name=f'{symbol} Open'), row=1, col=2)
            fig.add_trace(go.Scatter(x=symbol_df['Date'], y=symbol_df['High'], name=f'{symbol} High'), row=1, col=3)
            fig.add_trace(go.Scatter(x=symbol_df['Date'], y=symbol_df['Low'], name=f'{symbol} Low'), row=1, col=4)
            # Update layout
            fig.update_layout(title_text=f'{symbol} Stock Prices Over Time', showlegend=False)
            fig.show()
    def calculate_indicators(self):
        """Calculates various stock indicators and updates the merged DataFrame."""
        for symbol in self.tickers:
            symbol_df = self.merged_data[self.merged_data['Ticker'] == symbol].copy()
            # Calculate indicators
            symbol_df['SMA'] = ta.SMA(symbol_df['Close'], timeperiod=20)
            symbol_df['RSI'] = ta.RSI(symbol_df['Close'], timeperiod=14)
            symbol_df['EMA'] = ta.EMA(symbol_df['Close'], timeperiod=14)
            macd, macd_signal, _ = ta.MACD(symbol_df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
            symbol_df['MACD'] = macd
            symbol_df['MACD_Signal'] = macd_signal
            # Update main DataFrame with calculated indicators
            for indicator in ['SMA','RSI', 'EMA', 'MACD', 'MACD_Signal']:
                self.merged_data.loc[self.merged_data['Ticker'] == symbol, indicator] = symbol_df[indicator]
        # Sort by Date in ascending order
        # self.merged_data.sort_values(by='Date', inplace=True)
        return self.merged_data
    def plot_indicator(self, indicator, title):
        """Plots stock prices along with a specified indicator."""
        self.calculate_indicators()
        symbols = self.merged_data['Ticker'].unique()
        num_symbols = len(symbols)

        fig, axes = plt.subplots(nrows=num_symbols, ncols=1, figsize=(14, 5 * num_symbols), sharex=True)

        for i, symbol in enumerate(symbols):
            symbol_data = self.merged_data[self.merged_data['Ticker'] == symbol].copy()

            # Ensure Date column is in datetime format
            symbol_data['Date'] = pd.to_datetime(symbol_data['Date'])

            # Drop NA values for Close and indicator
            symbol_data = symbol_data.dropna(subset=['Close', indicator])
            ax1 = axes[i]

            ax1.plot(symbol_data['Date'], symbol_data['Close'], label='Close Price', color='blue')
            ax1.set_title(f'Stock Price and {title} for {symbol}')
            ax1.set_ylabel('Price', color='blue')
            ax1.tick_params(axis='y', labelcolor='blue')

            ax2 = ax1.twinx()  # Create a second y-axis for the indicator
            ax2.plot(symbol_data['Date'], symbol_data[indicator], label=indicator, color='orange')
            ax2.set_ylabel(indicator, color='orange')
            ax2.tick_params(axis='y', labelcolor='orange')

            ax1.legend(loc='upper left')
            ax2.legend(loc='upper right')

            # 🔹 Format x-axis to show readable date labels
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # Format as YYYY-MM
            ax1.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto-adjust date intervals
            fig.autofmt_xdate()  # Rotate labels for better readability

        plt.show()

    def calculate_returns(self):
        """Calculates daily and cumulative returns."""
        self.merged_data['Daily_Return'] = self.merged_data.groupby('Ticker')['Close'].pct_change()
        self.merged_data['Cumulative_Return'] = (1 + self.merged_data['Daily_Return']).groupby(self.merged_data['Ticker']).cumprod() - 1

    def calculate_volatility(self, period=30):
        """Calculates rolling volatility."""
        volatility = self.merged_data.groupby('Ticker')['Daily_Return'].rolling(window=period).std().reset_index(level=0, drop=True)
        self.merged_data['Volatility'] = volatility

    def calculate_sharpe_ratio(self, risk_free_rate=0.0):
        """Calculates the Sharpe Ratio for each symbol."""
        def sharpe_ratio(group):
            returns = group['Daily_Return'].dropna()
            return (returns.mean() - risk_free_rate) / returns.std() if returns.std() != 0 else pd.NA

        sharpe_ratios = self.merged_data.groupby('Ticker').apply(sharpe_ratio).reset_index(name='Sharpe_Ratio')
        self.merged_data = self.merged_data.merge(sharpe_ratios, on='Ticker', how='left')

    def calculate_max_drawdown(self):
        """Calculates the maximum drawdown for each symbol."""
        self.merged_data['Cumulative_Max'] = self.merged_data.groupby('Ticker')['Close'].cummax()
        self.merged_data['Drawdown'] = self.merged_data['Close'] / self.merged_data['Cumulative_Max'] - 1
        self.merged_data['Max_Drawdown'] = self.merged_data.groupby('Ticker')['Drawdown'].cummin()

    def calculate_all_metrics(self):
        """Calculates all financial metrics."""
        self.calculate_indicators()
        self.calculate_returns()
        self.calculate_volatility()
        self.calculate_sharpe_ratio()
        self.calculate_max_drawdown()
        return self.merged_data
    def plot_metric(self, metric, title):
        """Plots a specified metric for all symbols."""
        fig = make_subplots(rows=len(self.tickers), cols=1, shared_xaxes=True, vertical_spacing=0.02,
                            subplot_titles=[f'{symbol} {title}' for symbol in self.tickers])

        for i, symbol in enumerate(self.tickers):
            symbol_df = self.merged_data[self.merged_data['Ticker'] == symbol]
            fig.add_trace(go.Scatter(x=symbol_df['Date'], y=symbol_df[metric], mode='lines', name=f'{symbol} {title}'), row=i + 1, col=1)

        fig.update_layout(title_text=title, showlegend=False)
        fig.show()