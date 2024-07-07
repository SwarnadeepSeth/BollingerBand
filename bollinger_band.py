import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Wide mode for better layout
st.set_page_config(layout="wide")

# Function to fetch stock data from Yahoo Finance
def fetch_data(symbol):
    start_date = datetime.today() - timedelta(days=700)
    end_date = datetime.today()
    df = yf.download(symbol, start=start_date, end=end_date)
    return df

# Function to calculate Bollinger Bands
def calculate_bollinger_bands(df, window=20):
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()
    df['Upper Band'] = df['SMA'] + (df['STD'] * 2)
    df['Lower Band'] = df['SMA'] - (df['STD'] * 2)
    return df

# Calculate MACD
def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
    # Calculate the Short EMA
    df['Short EMA'] = df['Close'].ewm(span=short_window, adjust=False).mean()
    
    # Calculate the Long EMA
    df['Long EMA'] = df['Close'].ewm(span=long_window, adjust=False).mean()
    
    # Calculate the MACD Line
    df['MACD'] = df['Short EMA'] - df['Long EMA']
    
    # Calculate the Signal Line
    df['Signal Line'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()
    
    return df

# Function to check relative strength
def relative_strength(stock_df, nifty_df, period):
    try:
        stock_return = (stock_df['Close'][-1] - stock_df['Close'][-period]) / stock_df['Close'][-period]
        nifty_return = (nifty_df['Close'][-1] - nifty_df['Close'][-period]) / nifty_df['Close'][-period]
        return stock_return > nifty_return
    except:
        return False
    
# Function to check self momentum
def self_momentum(stock_df):
    return stock_df['Close'][-1] > stock_df['Close'][0]

st.title('Stock Analysis with Bollinger Bands')

# File uploader for CSV
st.write('Upload a CSV file with stock symbols in a column named "Symbol"')
st.write('Example: Get Stock Symbols cs file from: https://chartink.com/screener/lower-bollinger-stock-screener')
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("DataFrame from uploaded CSV:")
    st.write(df)

    with st.sidebar:

        # Dropdown for stock momentum period
        period = st.selectbox("Select stock momentum period:", ['3months', '6 months', '9 months'])

        # Convert period to appropriate time delta
        period_dict = {'3months': 90, '6 months': 180, '9 months': 270}
        period_days = period_dict[period]

        # Checkboxes for criteria
        check_relative_strength = st.checkbox('Relative Strength (RS)')
        check_self_momentum = st.checkbox('Self Momentum')
        # Add tooltip to explain criteria
        st.write('Relative Strength (RS): Stock return > Nifty50 return')
        st.write('Self Momentum: Current price > Previous price (selected period)')

    if st.button('Analyze Stocks'):
        nifty50 = fetch_data('^NSEI')  # Fetch Nifty 50 data
        today = datetime.today()
        start_date = today - timedelta(days=period_days)

        for symbol in df['Symbol']:
            symbol = symbol + '.NS'
            stock_data = fetch_data(symbol)
            if not stock_data.empty:
                stock_data = calculate_bollinger_bands(stock_data)
                stock_data = calculate_macd(stock_data)

                # Apply criteria
                show_plot = True
                if check_relative_strength and not relative_strength(stock_data, nifty50, period_days):
                    show_plot = False
                if check_self_momentum and not self_momentum(stock_data):
                    show_plot = False

                if show_plot:
                    st.write(f"Bollinger Bands and MACD for {symbol}")
                    # Both Bollinger Bands and MACD in subplots add 50 EMA
                    fig, ax = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'hspace': 0.1, 'height_ratios': [3, 1]})

                    ax[0].plot(stock_data.index, stock_data['Close'], label='Close Price')
                    ax[0].plot(stock_data.index, stock_data['Upper Band'], label='Upper Bollinger Band', linestyle='--')
                    ax[0].plot(stock_data.index, stock_data['Lower Band'], label='Lower Bollinger Band', linestyle='--')
                    ax[0].fill_between(stock_data.index, stock_data['Lower Band'], stock_data['Upper Band'], color='grey', alpha=0.1)
                    # Add 50 EMA
                    ax[0].plot(stock_data.index, stock_data['Close'].ewm(span=50, adjust=False).mean(), label='50 EMA', color='purple')
                    ax[0].legend(loc='upper left', frameon = False)

                    ax[1].plot(stock_data.index, stock_data['MACD'], label='MACD', color='red')
                    ax[1].plot(stock_data.index, stock_data['Signal Line'], label='Signal Line', color='green')
                    # Add histogram for MACD color based on positive or negative
                    color = ['green' if x > 0 else 'red' for x in stock_data['MACD'] - stock_data['Signal Line']]
                    ax[1].bar(stock_data.index, stock_data['MACD'] - stock_data['Signal Line'], width=0.6, color=color)
            
                    # Add zero line
                    ax[1].axhline(y=0, color='grey', linestyle='--')
                    ax[1].legend(loc='upper left', frameon = False)

                    plt.suptitle(f'{symbol}')

                    st.pyplot(fig)
                    plt.close(fig)
 
