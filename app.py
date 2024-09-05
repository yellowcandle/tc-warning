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
    st.title("而家掛得八號風球未？")

    st.write("呢個 app 會 check 而家有冇八號風球。")

    if st.button("Check 八號風球"):
        url = 'https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_10min_wind.csv'
        with st.spinner("搵緊風速數據..."):
            data = fetch_data(url)
            wind_speeds = get_wind_speeds(data)

        if check_typhoon_signal(wind_speeds):
            st.error("而家掛八號風球啦！")
        else:
            st.success("而家未掛八號風球。")

        st.subheader("而家嘅風速")
        station_mapping = {
            'Kai Tak': '啟德',
            'Tsing Yi': '青衣',
            'Cheung Chau': '長洲',
            'Sha Tin': '沙田',
            'Lau Fau Shan': '流浮山',
            'Ta Kwu Ling': '打鼓嶺',
            'Chek Lap Kok': '赤鱲角',
            'Sai Kung': '西貢'
        }
        df = data[data['Automatic Weather Station'].isin(station_mapping.keys())]
        col1, col2, col3, col4 = st.columns(4)
        for i, row in df.iterrows():
            with eval(f"col{i%4+1}"):
                st.metric(
                    label=station_mapping[row['Automatic Weather Station']],
                    value=f"{row['10-Minute Mean Speed(km/hour)']:.1f} km/h"
                )

if __name__ == '__main__':
    main()
