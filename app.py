"""
서울 저가 커피 브랜드 카페 입지 분석 대시보드
Streamlit 버전 - dashboard_data.json 기반
"""

import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="서울 카페 입지 분석",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# 커스텀 CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"] { background: #161b22; }

/* 헤더 */
.main-header {
    background: linear-gradient(135deg, #1a1f2e, #0d1117);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
.main-header h1 {
    font-size: 1.6rem; font-weight: 800;
    background: linear-gradient(90deg, #58a6ff, #bc8cff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.main-header p { color: #8b949e; margin: 4px 0 0; font-size: .85rem; }

/* 브랜드 카드 */
.brand-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.brand-name { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
.brand-val  { font-size: 1.8rem; font-weight: 900; }
.brand-sub  { font-size: .72rem; color: #8b949e; }

/* 메트릭 카드 */
[data-testid="metric-container"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
    padding: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
@st.cache_data
def load_data():
    """dashboard_data.json 로드 (캐시)"""
    json_path = os.path.join(os.path.dirname(__file__), "dashboard_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 행정동 DataFrame
    df_dong = pd.DataFrame(data["dong_data"])
    # 브랜드 컬럼 분리
    brands_df = pd.json_normalize(df_dong["brands"])
    brands_df.columns = [f"cnt_{c}" for c in brands_df.columns]
    df_dong = pd.concat([df_dong.drop(columns=["brands"]), brands_df], axis=1)

    # 지도 포인트 DataFrame
    df_map = pd.DataFrame(data["map_points"])

    # 추천 DataFrame
    df_rec = pd.DataFrame(data["recommend_top"])

    return data, df_dong, df_map, df_rec

data, df_dong, df_map, df_rec = load_data()

BRANDS      = data["brands"]
BRAND_COLORS = data["brand_colors"]
BRAND_STATS  = data["brand_stats"]

# Plotly 공통 레이아웃
PLOT_LAYOUT = dict(
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    font=dict(color="#e6edf3", family="Noto Sans KR"),
    margin=dict(l=10, r=10, t=30, b=10),
)

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>☕ 서울 저가 커피 브랜드 입지 분석</h1>
  <p>행정동별 브랜드 현황 · 매출 분석 · 입지 추천 | 더벤티 · 매머드커피 · 메가커피 · 빽다방 · 컴포즈커피</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 필터")
    selected_tab = st.radio(
        "분석 메뉴",
        ["📊 브랜드 개요", "🗺️ 지도", "🏙️ 행정동 분석", "⭐ 입지 추천"],
        label_visibility="collapsed",
    )
    st.divider()

    if selected_tab == "🏙️ 행정동 분석":
        dong_search = st.text_input("행정동 검색", placeholder="예: 강남, 홍대...")
        brand_filter = st.selectbox("브랜드 필터", ["전체"] + BRANDS)
        sort_by = st.selectbox(
            "정렬 기준",
            ["total_brand_count", "attractiveness_score", "monthly_sales", "total_workers"],
            format_func=lambda x: {
                "total_brand_count": "총 브랜드 수",
                "attractiveness_score": "매력도 점수",
                "monthly_sales": "월 매출",
                "total_workers": "근로자 수",
            }[x],
        )

    elif selected_tab == "⭐ 입지 추천":
        rec_brand = st.selectbox("브랜드 선택", ["전체"] + BRANDS)
        rec_sort = st.selectbox(
            "정렬 기준",
            ["attractiveness_score", "demand_score", "cost_score"],
            format_func=lambda x: {
                "attractiveness_score": "매력도 점수",
                "demand_score": "수요 점수",
                "cost_score": "비용 점수",
            }[x],
        )
        rec_search = st.text_input("행정동 검색", placeholder="예: 강남...")

    elif selected_tab == "🗺️ 지도":
        map_brands = st.multiselect(
            "표시할 브랜드",
            BRANDS,
            default=BRANDS,
        )

    st.divider()
    st.caption(f"행정동 {len(df_dong)}개 · 매장 {len(df_map):,}개")

# ══════════════════════════════════════════════
# 탭 1: 브랜드 개요
# ══════════════════════════════════════════════
if selected_tab == "📊 브랜드 개요":

    # 브랜드 카드 (5개)
    cols = st.columns(5)
    for i, brand in enumerate(BRANDS):
        s = BRAND_STATS[brand]
        color = BRAND_COLORS[brand]
        with cols[i]:
            avg = s.get('avg_monthly_sales', 0)
            avg_str = f"{avg:,}만" if avg else '-'
            st.markdown(f"""
            <div class="brand-card" style="border-top:3px solid {color}">
              <div class="brand-name" style="color:{color}">{brand}</div>
              <div class="brand-val">{s['total_stores']:,}</div>
              <div class="brand-sub">총 매장 수</div>
              <hr style="border-color:#30363d;margin:8px 0">
              <div style="font-size:1.1rem;font-weight:700">{s['dong_count']}</div>
              <div class="brand-sub">진출 행정동</div>
              <hr style="border-color:#30363d;margin:8px 0">
              <div style="font-size:1.1rem;font-weight:700;color:{color}">{avg_str}</div>
              <div class="brand-sub">점포당 평균월매출</div>
            </div>
            """, unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)

    # 차트 행 1
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### 브랜드별 총 매장 수")
        fig = go.Figure(go.Bar(
            x=BRANDS,
            y=[BRAND_STATS[b]["total_stores"] for b in BRANDS],
            marker_color=[BRAND_COLORS[b] for b in BRANDS],
            text=[BRAND_STATS[b]["total_stores"] for b in BRANDS],
            textposition="outside",
        ))
        fig.update_layout(**PLOT_LAYOUT, height=300,
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(gridcolor="#21262d"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("##### 브랜드별 진출 행정동 수")
        fig = go.Figure(go.Pie(
            labels=BRANDS,
            values=[BRAND_STATS[b]["dong_count"] for b in BRANDS],
            marker_colors=[BRAND_COLORS[b] for b in BRANDS],
            hole=0.45,
            textinfo="label+percent",
        ))
        fig.update_layout(**PLOT_LAYOUT, height=300,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # 차트 행 2: 상위 30개 동 누적 막대
    st.markdown("##### 행정동별 브랜드 분포 (총 브랜드 수 상위 30개 동)")
    top30 = df_dong[df_dong["total_brand_count"] > 0].nlargest(30, "total_brand_count")
    fig = go.Figure()
    for brand in BRANDS:
        col = f"cnt_{brand}"
        if col in top30.columns:
            fig.add_trace(go.Bar(
                name=brand,
                x=top30["dong_name"],
                y=top30[col],
                marker_color=BRAND_COLORS[brand],
            ))
    fig.update_layout(
        **PLOT_LAYOUT, barmode="stack", height=350,
        xaxis=dict(tickangle=-40, gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
        legend=dict(orientation="h", y=1.05),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 차트 행 3: 연령대별 매출
    st.markdown("##### 연령대별 총 매출 합계")
    age_cols  = ["age_10","age_20","age_30","age_40","age_50","age_60"]
    age_labels = ["10대","20대","30대","40대","50대","60대+"]
    age_colors = ["#FF6B6B","#FFE66D","#4ECDC4","#58a6ff","#bc8cff","#A8E6CF"]
    age_totals = [df_dong[c].sum() / 1e8 for c in age_cols]

    fig = go.Figure(go.Bar(
        x=age_labels, y=age_totals,
        marker_color=age_colors,
        text=[f"{v:.0f}억" for v in age_totals],
        textposition="outside",
    ))
    fig.update_layout(**PLOT_LAYOUT, height=300,
        xaxis=dict(gridcolor="#21262d"),
        yaxis=dict(title="매출(억원)", gridcolor="#21262d"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# 탭 2: 지도
# ══════════════════════════════════════════════
elif selected_tab == "🗺️ 지도":
    st.markdown("##### 저가 커피 브랜드 매장 위치")

    # 선택 브랜드 필터
    filtered_map = df_map[df_map["brand"].isin(map_brands)] if map_brands else df_map.iloc[0:0]

    if filtered_map.empty:
        st.warning("표시할 브랜드를 사이드바에서 선택하세요.")
    else:
        # 색상 컬럼 추가 (hex → RGB)
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return [int(h[i:i+2], 16) for i in (0, 2, 4)] + [200]

        filtered_map = filtered_map.copy()
        filtered_map["color"] = filtered_map["brand"].map(
            lambda b: hex_to_rgb(BRAND_COLORS.get(b, "#888888"))
        )

        import pydeck as pdk
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_map,
            get_position=["lng", "lat"],
            get_fill_color="color",
            get_radius=80,
            pickable=True,
            auto_highlight=True,
        )
        view = pdk.ViewState(latitude=37.5665, longitude=126.9780, zoom=10.5, pitch=0)
        tooltip = {"html": "<b>{brand}</b><br>{name}", "style": {"background": "#21262d", "color": "#e6edf3"}}

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            tooltip=tooltip,
            map_style="mapbox://styles/mapbox/dark-v10",
        ))

        # 브랜드별 매장 수 요약
        st.markdown("---")
        summary_cols = st.columns(len(map_brands))
        brand_counts = filtered_map["brand"].value_counts()
        for i, brand in enumerate(map_brands):
            cnt = brand_counts.get(brand, 0)
            color = BRAND_COLORS[brand]
            with summary_cols[i]:
                st.markdown(f"""
                <div style="text-align:center;padding:10px;background:#161b22;
                     border:1px solid #30363d;border-radius:8px;border-top:3px solid {color}">
                  <div style="color:{color};font-weight:700;font-size:.9rem">{brand}</div>
                  <div style="font-size:1.4rem;font-weight:900">{cnt}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 탭 3: 행정동 분석
# ══════════════════════════════════════════════
elif selected_tab == "🏙️ 행정동 분석":

    # 필터 적용
    df_view = df_dong.copy()
    if dong_search:
        df_view = df_view[df_view["dong_name"].str.contains(dong_search)]
    if brand_filter != "전체":
        col = f"cnt_{brand_filter}"
        if col in df_view.columns:
            df_view = df_view[df_view[col] > 0]
    df_view = df_view.sort_values(sort_by, ascending=False, na_position="last")

    st.markdown(f"##### 행정동 분석 — {len(df_view)}개 동")

    # 좌우 분할
    left, right = st.columns([2, 1])

    with left:
        # 표시 컬럼 선택
        display_cols = ["dong_name"] + [f"cnt_{b}" for b in BRANDS] + \
                       ["total_brand_count", "attractiveness_score", "monthly_sales", "total_workers"]
        display_cols = [c for c in display_cols if c in df_view.columns]

        rename_map = {"dong_name": "행정동"}
        for b in BRANDS:
            rename_map[f"cnt_{b}"] = b
        rename_map.update({
            "total_brand_count": "합계",
            "attractiveness_score": "매력도",
            "monthly_sales": "월매출(억)",
            "total_workers": "근로자",
        })

        show_df = df_view[display_cols].rename(columns=rename_map).head(200).copy()
        if "월매출(억)" in show_df.columns:
            show_df["월매출(억)"] = (show_df["월매출(억)"] / 1e8).round(1)
        if "매력도" in show_df.columns:
            show_df["매력도"] = show_df["매력도"].round(1)

        # 선택 행 이벤트
        selected_rows = st.dataframe(
            show_df,
            use_container_width=True,
            height=500,
            on_select="rerun",
            selection_mode="single-row",
        )

    with right:
        # 선택 행 상세
        sel_idx = selected_rows.selection.get("rows", []) if selected_rows else []
        if sel_idx:
            row_idx = df_view.index[sel_idx[0]]
            d = df_dong.loc[row_idx]

            color_map = {
                "매력도": "#58a6ff", "수요": "#4ECDC4",
                "경쟁": "#FFE66D", "비용": "#A8E6CF",
            }
            st.markdown(f"#### {d['dong_name']}")

            m1, m2 = st.columns(2)
            m1.metric("매력도 점수", f"{d['attractiveness_score']:.1f}" if pd.notna(d.get('attractiveness_score')) else "-")
            m2.metric("수요 점수",   f"{d['demand_score']:.1f}"        if pd.notna(d.get('demand_score'))        else "-")
            m3, m4 = st.columns(2)
            m3.metric("경쟁 점수",   f"{d['competition_score']:.1f}"   if pd.notna(d.get('competition_score'))   else "-")
            m4.metric("비용 점수",   f"{d['cost_score']:.1f}"          if pd.notna(d.get('cost_score'))          else "-")

            st.markdown("---")
            st.markdown(f"**근로자** {int(d.get('total_workers',0)):,}명 (여성 {int(d.get('female_workers',0)):,}명)")
            st.markdown(f"**카페 수** {int(d.get('cafe_count',0))}개")
            st.markdown(f"**월 매출** {d.get('monthly_sales',0)/1e8:.1f}억원")

            # 브랜드 현황
            st.markdown("**브랜드 현황**")
            for brand in BRANDS:
                col = f"cnt_{brand}"
                cnt = int(d.get(col, 0))
                color = BRAND_COLORS[brand]
                bar_w = min(cnt * 20, 100)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                  <span style="color:{color};font-size:.8rem;width:80px">{brand}</span>
                  <div style="background:{color};height:8px;width:{bar_w}px;border-radius:4px"></div>
                  <span style="font-size:.8rem">{cnt}</span>
                </div>
                """, unsafe_allow_html=True)

            # 연령대 차트
            st.markdown("**연령대별 매출**")
            age_vals = [d.get(c, 0) / 1e6 for c in ["age_10","age_20","age_30","age_40","age_50","age_60"]]
            fig = go.Figure(go.Bar(
                x=["10대","20대","30대","40대","50대","60대+"],
                y=age_vals,
                marker_color=["#FF6B6B","#FFE66D","#4ECDC4","#58a6ff","#bc8cff","#A8E6CF"],
            ))
            fig.update_layout(**PLOT_LAYOUT, height=220,
                xaxis=dict(gridcolor="#21262d"),
                yaxis=dict(title="백만원", gridcolor="#21262d"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("👆 테이블에서 행을 클릭하면 상세 정보가 표시됩니다.")


# ══════════════════════════════════════════════
# 탭 4: 입지 추천
# ══════════════════════════════════════════════
elif selected_tab == "⭐ 입지 추천":

    # 필터
    df_r = df_rec.copy()
    if rec_brand != "전체":
        df_r = df_r[df_r["brand"] == rec_brand]
    if rec_search:
        df_r = df_r[df_r["dong_name"].str.contains(rec_search)]
    df_r = df_r.sort_values(rec_sort, ascending=False).head(60)

    st.markdown(f"##### ⭐ 입지 추천 — {len(df_r)}개 결과")
    st.caption("매력도 점수 기준 해당 브랜드가 **아직 진출하지 않은** 행정동을 추천합니다.")

    if df_r.empty:
        st.warning("조건에 맞는 추천 결과가 없습니다.")
    else:
        # 3열 카드 그리드
        for row_start in range(0, len(df_r), 3):
            cols = st.columns(3)
            for ci, idx in enumerate(range(row_start, min(row_start + 3, len(df_r)))):
                r = df_r.iloc[idx]
                color = BRAND_COLORS.get(r["brand"], "#888")
                score = r.get("attractiveness_score")
                score_color = "#4ECDC4" if score and score > 60 else "#FFE66D" if score and score > 40 else "#FF6B6B"

                with cols[ci]:
                    st.markdown(f"""
                    <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
                         padding:16px;border-top:3px solid {color};margin-bottom:12px">
                      <div style="font-size:.7rem;color:#8b949e">#{row_start+ci+1} 추천</div>
                      <div style="font-size:1rem;font-weight:700;margin:4px 0">{r['dong_name']}</div>
                      <span style="background:{color}25;color:{color};padding:2px 8px;
                            border-radius:10px;font-size:.75rem;font-weight:600">{r['brand']}</span>
                      <span style="font-size:.72rem;color:#8b949e;margin-left:6px">미진출 지역</span>
                      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:12px">
                        <div style="background:#21262d;border-radius:6px;padding:8px">
                          <div style="font-size:.65rem;color:#8b949e">매력도</div>
                          <div style="font-size:1.1rem;font-weight:700;color:{score_color}">
                            {score:.1f if score else '-'}
                          </div>
                        </div>
                        <div style="background:#21262d;border-radius:6px;padding:8px">
                          <div style="font-size:.65rem;color:#8b949e">수요</div>
                          <div style="font-size:1.1rem;font-weight:700;color:#4ECDC4">
                            {r['demand_score']:.1f if r.get('demand_score') else '-'}
                          </div>
                        </div>
                        <div style="background:#21262d;border-radius:6px;padding:8px">
                          <div style="font-size:.65rem;color:#8b949e">경쟁</div>
                          <div style="font-size:1.1rem;font-weight:700;color:#FFE66D">
                            {r['competition_score']:.1f if r.get('competition_score') else '-'}
                          </div>
                        </div>
                        <div style="background:#21262d;border-radius:6px;padding:8px">
                          <div style="font-size:.65rem;color:#8b949e">비용</div>
                          <div style="font-size:1.1rem;font-weight:700;color:#A8E6CF">
                            {r['cost_score']:.1f if r.get('cost_score') else '-'}
                          </div>
                        </div>
                      </div>
                      <div style="font-size:.72rem;color:#8b949e;margin-top:8px">
                        근로자 {int(r.get('total_workers',0)):,}명 · 
                        카페 {int(r.get('cafe_count',0))}개 · 
                        월매출 {r.get('monthly_sales',0)/1e8:.1f}억
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
