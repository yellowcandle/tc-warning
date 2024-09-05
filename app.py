import requests
from io import StringIO
import pandas as pd
import streamlit as st

# Define the threshold for strong and gale-force winds in knots
STRONG_WIND_THRESHOLD = 22  # Approx. 41 km/h
GALE_FORCE_WIND_THRESHOLD = 63  # Approx. 63 km/h

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    csv_content = StringIO(response.text)
    df = pd.read_csv(csv_content)
    return df

def get_wind_speeds(df):
    selected_stations = ['Kai Tak', 'Tsing Yi', 'Cheung Chau', 'Sha Tin', 'Lau Fau Shan', 'Ta Kwu Ling', 'Chek Lap Kok', 'Sai Kung']
    df = df[df['Automatic Weather Station'].isin(selected_stations)]
    return df['10-Minute Mean Speed(km/hour)'].values  # Adjust 'WindSpeed' to the correct column name if necessary

def check_typhoon_signal(wind_speeds):
    gale_force_wind_count = sum(1 for speed in wind_speeds if speed >= GALE_FORCE_WIND_THRESHOLD)
    return gale_force_wind_count >= 4

def main():
    st.title("Hong Kong Typhoon Signal Checker")

    st.write("This app checks if the No. 8 typhoon signal is in effect based on current wind speeds.")

    if st.button("Check Typhoon Signal"):
        url = 'https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_10min_wind.csv'
        with st.spinner("Fetching wind data..."):
            data = fetch_data(url)
            wind_speeds = get_wind_speeds(data)

        if check_typhoon_signal(wind_speeds):
            st.error("The No. 8 typhoon signal is in effect.")
        else:
            st.success("The No. 8 typhoon signal is not in effect.")

        st.subheader("Wind Speeds at Selected Stations")
        df = data[data['Automatic Weather Station'].isin(['Kai Tak', 'Tsing Yi', 'Cheung Chau', 'Sha Tin', 'Lau Fau Shan', 'Ta Kwu Ling', 'Chek Lap Kok', 'Sai Kung'])]
        st.dataframe(df[['Automatic Weather Station', '10-Minute Mean Speed(km/hour)']])

if __name__ == '__main__':
    main()
