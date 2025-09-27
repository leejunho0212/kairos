import pandas as pd
import streamlit as st

# 호선별 색상
line_colors = {
    "1호선": "navy",
    "2호선": "green",
    "3호선": "orange",
    "4호선": "skyblue",
    "5호선": "purple",
    "6호선": "brown",
    "7호선": "olive",
    "8호선": "pink",
}

st.title("지하철 혼잡도 추천 시간 조회")

# CSV 읽기
df = pd.read_csv("지하철혼잡도.csv", encoding="cp949")
time_cols = df.columns[5:45]

# Streamlit 입력
station = st.text_input("조회할 역명을 입력하세요")
time_input = st.text_input("시간을 입력하세요 (HH:MM)")

if station and time_input:
    df_station = df[df['출발역'] == station]

    if df_station.empty:
        st.error(f"'{station}'에 해당하는 데이터가 없습니다.")
    else:
        try:
            hour, minute = map(int, time_input.split(":"))
        except:
            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요.")
        else:
            # 시간 반올림, ±30분 범위 선택
            if minute >= 45:
                hour += 1
                minute = 0
            elif minute >= 15:
                minute = 30
            else:
                minute = 0
            hour %= 24
            input_minutes = hour * 60 + minute

            def time_str_to_minutes(t):
                h, m = t.replace("시", ":").replace("분", "").split(":")
                h, m = int(h), int(m)
                if h == 24:
                    h = 0
                return h * 60 + m

            selected_times = []
            for t in time_cols:
                t_min = time_str_to_minutes(t)
                diff = abs(t_min - input_minutes)
                diff = min(diff, 1440 - diff)
                if diff <= 30:
                    selected_times.append(t)

            if not selected_times:
                st.warning("해당 시간대 ±30분 범위에 데이터가 없습니다.")
            else:
                df_melted = df_station.melt(
                    id_vars=['요일구분', '호선', '역번호', '출발역', '상하구분'],
                    value_vars=selected_times,
                    var_name='시간대',
                    value_name='혼잡도'
                )
                df_melted['혼잡도'] = pd.to_numeric(df_melted['혼잡도'], errors='coerce')
                df_melted = df_melted[df_melted['혼잡도'] > 0]

                if df_melted.empty:
                    st.warning("혼잡도가 0보다 큰 데이터가 없습니다.")
                else:
                    df_avg = df_melted.groupby(['호선', '상하구분', '시간대'])['혼잡도'].mean().reset_index()
                    df_avg['혼잡도'] = df_avg['혼잡도'].map(lambda x: f"{x:.1f}%")
                    df_avg['시간_minutes'] = df_avg['시간대'].apply(time_str_to_minutes)
                    df_avg = df_avg.sort_values(by=['호선', '상하구분', '시간_minutes']).drop(columns='시간_minutes')

                    # 최소 혼잡도
                    min_df = df_avg.loc[df_avg.groupby(['호선', '상하구분'])['혼잡도'].idxmin()]

                    st.subheader(f"{station}역 {time_input} 기준 ±30분 혼잡도")
                    for line in df_avg['호선'].unique():
                        color = line_colors.get(line, "black")
                        df_line = df_avg[df_avg['호선'] == line]

                        # 글자 색 적용
                        st.markdown(f"**<span style='color:{color}'>{line}</span>**", unsafe_allow_html=True)

                        for group in df_line['상하구분'].unique():
                            group_df = df_line[df_line['상하구분'] == group][['시간대','혼잡도']].reset_index(drop=True)
                            group_df.index = [''] * len(group_df)
                            st.markdown(f"**{group}**")
                            st.table(group_df)  # 시간대 + 혼잡도만 표시

                    st.subheader("가장 혼잡도 낮은 시간")
                    for _, row in min_df.iterrows():
                        color = line_colors.get(row['호선'], "black")
                        st.markdown(
                            f"<span style='color:{color}'>{row['호선']}</span> {row['상하구분']}: {row['시간대']} ({row['혼잡도']})",
                            unsafe_allow_html=True
                        )

