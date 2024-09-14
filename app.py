import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Constants
API_URL = "https://api.dhan.co/v2/charts/intraday"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "access-token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiY2Q2OWRiNmYiLCJleHAiOjE3MjYzNjI2MTYsInRva2VuQ29uc3VtZXJUeXBlIjoiUEFSVE5FUiIsImRoYW5DbGllbnRJZCI6IjExMDA0NDM0MzcifQ.Z3BcLbA_EBrffyzsgYe9L_AkX-dauYNsO8yb3UD_hh529J_PSr7OX_bZrG2i-nEHL0bxWA8EYW7nI3ruNBKFcA"  # You'll need to set this
}

# Streamlit app
st.title("Historical Data Retrieval and Visualization")
security_df=pd.read_csv('scrip_eq.csv')
def get_security_id(trading_symbol, exchange):
    # Load the CSV file
    df = security_df 
    
    # Convert trading symbol to uppercase for case-insensitive matching
    trading_symbol = trading_symbol.upper()
    
    # Map exchange segment to SEM_EXM_EXCH_ID
    exchange_map = {"NSE_EQ": "NSE", "BSE_EQ": "BSE"}
    exchange_id = exchange_map.get(exchange)
    
    # Find the row with the matching trading symbol and exchange
    match = df[(df['SEM_TRADING_SYMBOL'] == trading_symbol) & (df['SEM_EXM_EXCH_ID'] == exchange_id)]
    
    if not match.empty:
        # Return the security ID if a match is found
        return str(match.iloc[0]['SEM_SMST_SECURITY_ID'])
    else:
        # Return None if no match is found
        return None

# Input fields
df = security_df

# Get the list of unique trading symbols, excluding those with digits
trading_symbols = sorted([symbol for symbol in df['SEM_TRADING_SYMBOL'].unique() if not any(char.isdigit() for char in symbol)])

# Create dropdowns for security name and exchange segment selection
selected_symbol = st.selectbox("Security Name", trading_symbols)
exchange_segment = st.selectbox("Exchange Segment", ["NSE_EQ", "BSE_EQ"])

# Get the corresponding security ID
security_id = get_security_id(selected_symbol, exchange_segment)

if security_id is None:
    st.error("Security ID not found for the selected trading symbol and exchange.")
else:
    st.write(f"Selected Security ID: {security_id}")
instrument = st.selectbox("Instrument", ["EQUITY"])
interval = st.selectbox("Interval", ["1", "5", "15", "25", "60"])
from_date = st.date_input("From Date", datetime.now() - timedelta(days=5))
to_date = st.date_input("To Date", datetime.now())

if st.button("Retrieve Data"):
    # Prepare the request payload
    payload = {
        "securityId": security_id,
        "exchangeSegment": exchange_segment,
        "instrument": instrument,
        "interval": int(interval),
        "fromDate": from_date.strftime("%Y-%m-%d"),
        "toDate": to_date.strftime("%Y-%m-%d")
    }
    print(payload)

    # Make the API request
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if all(key in data for key in ['open', 'high', 'low', 'close', 'volume', 'timestamp']):
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['timestamp'], unit='s'),
                'open': data['open'],
                'high': data['high'],
                'low': data['low'],
                'close': data['close'],
                'volume': data['volume']
            })
            
            st.write("Data Preview:")
            st.write(df.head())

            # Plot selection
            # plot_type = st.selectbox("Select plot type", ['open', 'high', 'low', 'close'])

            # Create the plot
            # fig = go.Figure()
            # fig.add_trace(go.Scatter(x=df['timestamp'], y=df[plot_type], mode='lines', name=plot_type))
            # fig.update_layout(title=f'{plot_type.capitalize()} Price Over Time',
            #                   xaxis_title='Time',
            #                   yaxis_title='Price')
            # st.plotly_chart(fig)
            # Convert timestamp to IST by adding 5.5 hours
            df['timestamp'] = pd.to_datetime(df['timestamp']) + pd.Timedelta(hours=5, minutes=30)
            
            # Sort the DataFrame by timestamp
            df.sort_values(by='timestamp',inplace=True)
            
            csv = df.to_csv(index=False)
            filename = f"{security_id}_{exchange_segment}_{interval}min_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}.csv"
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
            )
            
        else:
            st.error("Unexpected data format in the response")
    else:
        st.error(f"Error: {response.status_code} - {response.text}")

# Note: Remember to set your access token in the HEADERS constant
st.warning("Don't forget to set your access token in the HEADERS constant!")
