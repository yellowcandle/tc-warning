import requests
from io import StringIO
import pandas as pd
import streamlit as st

# Define the threshold for strong and gale-force winds in km/h (directly, not converted from knots)
STRONG_WIND_THRESHOLD = 41  # Lower threshold for No.3 signal
GALE_FORCE_WIND_THRESHOLD = 63  # Lower threshold for No.8 signal
MAX_WIND_THRESHOLD = 117  # Upper threshold for No.8 signal

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def get_wind_speeds(df):
    if df is None:
        return []
    
    # The 8 reference stations according to HKO
    reference_stations = [
        'Chek Lap Kok', 'Cheung Chau', 'Kai Tak',
        'Lau Fau Shan', 'Sha Tin', 'Sai Kung',
        'Ta Kwu Ling', 'Tsing Yi'
    ]
    df = df[df['Automatic Weather Station'].isin(reference_stations)]
    return df['10-Minute Mean Speed(km/hour)'].tolist()

def check_typhoon_signal(wind_speeds):
    if len(wind_speeds) == 0:
        return None, 0
    
    # Count stations with winds in No.8 range (63-117 km/h)
    gale_force_count = sum(1 for speed in wind_speeds 
                          if GALE_FORCE_WIND_THRESHOLD <= speed <= MAX_WIND_THRESHOLD)
    
    # Count stations with winds in No.3 range (41-62 km/h)
    strong_wind_count = sum(1 for speed in wind_speeds 
                           if STRONG_WIND_THRESHOLD <= speed < GALE_FORCE_WIND_THRESHOLD)
    
    # Need at least 4 stations (half of 8) to meet criteria
    if gale_force_count >= 4:
        return 8, gale_force_count
    elif strong_wind_count >= 4:
        return 3, strong_wind_count
    return None, max(strong_wind_count, gale_force_count)

def main():
    st.title("而家掛得八號風球未？")

    st.write("呢個 app 會 check 而家掛得八號風球未？。")
    st.markdown("**注意：** 呢個 app 只係用嚟娛樂，唔係專業嘅氣象預測。準則來自：[香港天文台：發出 3 號和 8 號信號的參考指標](https://www.hko.gov.hk/tc/informtc/tcsignal3_ref.htm)")

    if st.button("Check 八號風球"):
        url = 'https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_10min_wind.csv'
        with st.spinner("搵緊風速數據..."):
            data = fetch_data(url)
            if data is not None:
                wind_speeds = get_wind_speeds(data)
                signal, station_count = check_typhoon_signal(wind_speeds)
                
                if signal == 8:
                    st.error("而家掛得八號風球啦！")
                    st.info(f"有 {station_count} 個測站錄得烈風或以上風力 (63-117 km/h)")
                elif signal == 3:
                    st.warning("而家掛得三號風球。")
                    st.info(f"有 {station_count} 個測站錄得強風 (41-62 km/h)")
                else:
                    st.success("而家未掛得八號風球。")
                    if station_count > 0:
                        st.info(f"只有 {station_count} 個測站錄得強風或以上風力")
                
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
                        speed = row['10-Minute Mean Speed(km/hour)']
                        color = (
                            "🔴" if speed >= GALE_FORCE_WIND_THRESHOLD else
                            "🟡" if speed >= STRONG_WIND_THRESHOLD else
                            "🟢"
                        )
                        st.metric(
                            label=f"{color} {station_mapping[row['Automatic Weather Station']]}",
                            value=f"{speed:.1f} km/h"
                        )

if __name__ == '__main__':
    main()
