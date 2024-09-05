import requests
from io import StringIO
import pandas as pd
import streamlit as st

# Define the threshold for strong and gale-force winds in knots
STRONG_WIND_THRESHOLD = 41  # Approx. 41 km/h
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

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_warnings():
    url = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=warningInfo&lang=tc'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_typhoon_signal(warnings):
    signal_mapping = {
        'TC1': '一號戒備信號',
        'TC3': '三號強風信號',
        'TC8NE': '八號東北烈風或暴風信號',
        'TC8SE': '八號東南烈風或暴風信號',
        'TC8NW': '八號西北烈風或暴風信號',
        'TC8SW': '八號西南烈風或暴風信號',
        'TC9': '九號烈風或暴風風力增強信號',
        'TC10': '十號颶風信號',
        'CANCEL': '取消所有熱帶氣旋警告信號'
    }
    
    for warning in warnings.get('details', []):
        if warning.get('warningStatementCode') == 'WTCSGNL':
            subtype = warning.get('subtype', '')
            if subtype in signal_mapping:
                return subtype, signal_mapping[subtype]
    return 'CANCEL', signal_mapping['CANCEL']

def main():
    st.title("而家掛得八號風球未？")

    st.write("呢個 app 會 check 而家掛得八號風球未？天文台嘅 8 中 4 準則究竟有幾準？")
    st.markdown("""
    **注意：** 呢個 app 只係用嚟娛樂，唔係專業嘅氣象預測。

    > 自二零零七年起，天文台在考慮發出3號和8號熱帶氣旋警告信號時，會參考由八個涵蓋全港並接近海平面的參考測風站組成的網絡所錄得的風力資料。下圖顯示現時的參考測風站網絡。
    > 
    > 當參考網絡中半數或以上的測風站錄得或預料錄得的持續風速達到有關的風速限值，且風勢可能持續時，則會發出3號或8號信號。3號信號風速範圍為每小時41至62公里，而8號信號則為每小時63至117公里。
    
    準則來自：[香港天文台：發出 3 號和 8 號信號的參考指標](https://www.hko.gov.hk/tc/informtc/tcsignal3_ref.htm)
    """)

    if st.button("Check 八號風球"):
        with st.spinner("搵緊風速數據同警告信息..."):
            warnings = fetch_warnings()
            url = 'https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_10min_wind.csv'
            data = fetch_data(url)

        signal_code, signal_name = get_typhoon_signal(warnings)


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
        gale_force_wind_count = 0
        for i, row in df.iterrows():
            with eval(f"col{i%4+1}"):
                wind_speed = row['10-Minute Mean Speed(km/hour)']
                delta_color = "normal" if wind_speed >= GALE_FORCE_WIND_THRESHOLD else "off"
                st.metric(
                    label=station_mapping[row['Automatic Weather Station']],
                    value=f"{wind_speed:.1f} km/h",
                    delta_color=delta_color
                )
                if wind_speed >= GALE_FORCE_WIND_THRESHOLD:
                    gale_force_wind_count += 1
        # Display typhoon warning details if any signal is in force
        if signal_code != 'CANCEL':
            st.subheader("現時颱風警告")
            st.markdown(f"**{signal_name}**")
        # Compare wind speed data with actual warnings
        wind_speed_criteria_met = gale_force_wind_count >= 4
        st.subheader("風速分析")
        if wind_speed_criteria_met:
            st.warning(f"現時有 {gale_force_wind_count} 個測站錄得烈風或以上風速 (≥ 63 km/h)，達到發出八號風球的其中一項準則。")
        else:
            st.info(f"現時有 {gale_force_wind_count} 個測站錄得烈風或以上風速 (≥ 63 km/h)，未達到發出八號風球的準則。")

        if signal_code.startswith('TC8') and not wind_speed_criteria_met:
            st.warning("雖然風速未達標準，但天文台已發出八號風球。可能基於其他考慮因素，如預測風速增強等。")
        elif not signal_code.startswith('TC8') and wind_speed_criteria_met:
            st.warning("雖然風速已達八號風球標準，但天文台尚未發出八號風球。可能正在評估其他因素。")



if __name__ == '__main__':
    main()
