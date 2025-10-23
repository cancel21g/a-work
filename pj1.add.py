import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="지역별 인기업종 현황 분석",
    page_icon="🏪",
    layout="wide"
)

# 제목
st.title("🏪 지역별 인기업종 현황 분석")
st.markdown("### 2025년 04월 100대 생활업종 데이터 기반")

# 컬럼명 찾기 함수
def find_column(df, possible_names):
    """가능한 컬럼명 리스트에서 실제 존재하는 컬럼 찾기"""
    for name in possible_names:
        if name in df.columns:
            return name
    return None

# 사이드바
st.sidebar.header("⚙️ 분석 설정")

# 파일 업로드
uploaded_file = st.sidebar.file_uploader("📁 엑셀 파일 업로드", type=['xlsx', 'xls'])

# 엑셀 파일 경로
import os
default_file_path = os.path.join('C:', 'Users', 'user', 'mcp-demo', 'data', '사업자 현황(2025년 04월 100대생활업종).xlsx')

# 데이터 로드 함수 수정
@st.cache_data
def load_data(file_source):
    try:
        if isinstance(file_source, str):
            # 파일 경로인 경우
            df = pd.read_excel(file_source)
        else:
            # 업로드된 파일인 경우
            df = pd.read_excel(file_source)
        return df, None
    except Exception as e:
        return None, str(e)

# 파일 소스 결정
if uploaded_file is not None:
    file_source = uploaded_file
    st.sidebar.success("✅ 파일이 업로드되었습니다!")
else:
    if os.path.exists(default_file_path):
        file_source = default_file_path
        st.sidebar.info("ℹ️ 기본 파일을 사용합니다.")
    else:
        st.error("❌ 파일을 업로드하거나 기본 파일 경로를 확인해주세요.")
        st.info("👆 왼쪽 사이드바에서 엑셀 파일을 업로드해주세요.")
        st.stop()

# 데이터 로드
df, error = load_data(file_source)

if error:
    st.error(f"❌ 데이터 로드 중 오류 발생: {error}")
    st.info("파일 경로를 확인해주세요.")
    st.stop()

if df is None:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# 디버그 정보 표시 (토글)
with st.expander("🔍 데이터 구조 확인"):
    st.write("**전체 컬럼명:**")
    st.write(df.columns.tolist())
    st.write(f"**데이터 shape:** {df.shape}")
    st.write("**데이터 샘플 (첫 5행):**")
    st.dataframe(df.head())

# 컬럼명 자동 매칭
region_col = find_column(df, ['지역명', '시도명', '행정구역', '지역', '시도', '광역시도'])
industry_col = find_column(df, ['업종명', '업종', '업태명', '서비스업종명'])
stores_col = find_column(df, ['점포수', '매장수', '사업체수', '개소수', '당월'])
growth_col = find_column(df, ['증감율', '증감률', '성장률', '성장율', '전년동월대비'])

# 컬럼 확인
missing_cols = []
if region_col is None:
    missing_cols.append("지역명")
if industry_col is None:
    missing_cols.append("업종명")
if stores_col is None:
    missing_cols.append("점포수")
if growth_col is None:
    missing_cols.append("증감율")

if missing_cols:
    st.error(f"❌ 다음 컬럼을 찾을 수 없습니다: {', '.join(missing_cols)}")
    st.info("위의 '데이터 구조 확인' 섹션을 펼쳐서 실제 컬럼명을 확인해주세요.")
    st.stop()

# 숫자형으로 변환
df[stores_col] = pd.to_numeric(df[stores_col], errors='coerce')
df[growth_col] = pd.to_numeric(df[growth_col], errors='coerce')

# NaN 제거
df = df.dropna(subset=[stores_col, growth_col])

# 지역 선택
regions = ['전체'] + sorted(df[region_col].unique().tolist())
selected_region = st.sidebar.selectbox("📍 분석 지역 선택", regions)

# 상위 N개 선택
top_n = st.sidebar.slider("📊 상위 업종 개수", 5, 20, 10)

# 증감율 필터
min_growth_rate = st.sidebar.number_input("📈 최소 증감율 (%)", value=100.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 분석 기준")
st.sidebar.info(f"""
- **고성장 업종**: 증감율 {min_growth_rate}% 이상
- **인기 업종**: 점포수 기준 상위
- **데이터 기준일**: 2025년 04월
""")

# 데이터 필터링
if selected_region == '전체':
    filtered_df = df.copy()
    region_title = "전국"
else:
    filtered_df = df[df[region_col] == selected_region].copy()
    region_title = selected_region

if filtered_df.empty:
    st.warning(f"'{selected_region}' 지역의 데이터가 없습니다.")
    st.stop()

# 메인 대시보드
st.markdown(f"## 📊 {region_title} 지역 현황")

# KPI 지표
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_industries = len(filtered_df)
    st.metric(
        label="📋 분석 업종 수",
        value=f"{total_industries:,}개"
    )

with col2:
    total_stores = filtered_df[stores_col].sum()
    st.metric(
        label="🏪 총 점포 수",
        value=f"{total_stores:,.0f}개"
    )

with col3:
    avg_growth = filtered_df[growth_col].mean()
    st.metric(
        label="📈 평균 증감율",
        value=f"{avg_growth:.2f}%",
        delta=f"{avg_growth:.2f}%"
    )

with col4:
    high_growth_count = len(filtered_df[filtered_df[growth_col] >= min_growth_rate])
    high_growth_pct = (high_growth_count / total_industries * 100) if total_industries > 0 else 0
    st.metric(
        label=f"🚀 고성장 업종",
        value=f"{high_growth_count}개",
        delta=f"{high_growth_pct:.1f}%"
    )

st.markdown("---")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 고성장 업종 분석",
    "🏆 인기 업종 순위",
    "📊 종합 비교 분석",
    "📋 상세 데이터"
])

# 탭 1: 고성장 업종 분석
with tab1:
    st.subheader(f"🚀 증감율 {min_growth_rate}% 이상 고성장 업종 Top {top_n}")
    
    high_growth_df = filtered_df[filtered_df[growth_col] >= min_growth_rate].copy()
    
    if high_growth_df.empty:
        st.info(f"증감율 {min_growth_rate}% 이상인 업종이 없습니다.")
    else:
        high_growth_sorted = high_growth_df.sort_values(by=growth_col, ascending=False).head(top_n)
        
        # 좌우 2열 레이아웃
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📊 고성장 업종 순위")
            
            # 순위 테이블
            display_df = high_growth_sorted[[industry_col, growth_col, stores_col]].copy()
            display_df.index = range(1, len(display_df) + 1)
            display_df.columns = ['업종명', '증감율(%)', '점포수']
            
            # 스타일 적용
            def highlight_top3(s):
                colors = ['background-color: #FFD700', 'background-color: #C0C0C0', 'background-color: #CD7F32']
                return [colors[i] if i < 3 else '' for i in range(len(s))]
            
            styled_df = display_df.style.format({
                '증감율(%)': '{:.2f}',
                '점포수': '{:,.0f}'
            }).apply(highlight_top3, axis=0, subset=['업종명'])
            
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # 통계 정보
            st.markdown("##### 📈 고성장 업종 통계")
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric("평균 증감율", f"{high_growth_sorted[growth_col].mean():.2f}%")
            with stat_col2:
                st.metric("최고 증감율", f"{high_growth_sorted[growth_col].max():.2f}%")
        
        with col2:
            st.markdown("#### 📊 증감율 시각화")
            
            # 가로 막대 차트
            fig1 = go.Figure()
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
                     '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
            
            fig1.add_trace(go.Bar(
                y=high_growth_sorted[industry_col],
                x=high_growth_sorted[growth_col],
                orientation='h',
                marker=dict(
                    color=colors[:len(high_growth_sorted)],
                    line=dict(color='rgba(0,0,0,0.3)', width=1)
                ),
                text=high_growth_sorted[growth_col].apply(lambda x: f'{x:.1f}%'),
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>증감율: %{x:.2f}%<extra></extra>'
            ))
            
            fig1.update_layout(
                title='증감율 Top 10',
                xaxis_title='증감율 (%)',
                yaxis_title='',
                height=400,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False,
                margin=dict(l=10, r=50, t=40, b=40)
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # 점포수 vs 증감율 산점도
            st.markdown("#### 📊 점포수 vs 증감율")
            fig2 = px.scatter(
                high_growth_sorted,
                x=stores_col,
                y=growth_col,
                size=stores_col,
                color=growth_col,
                hover_name=industry_col,
                color_continuous_scale='Viridis',
                labels={stores_col: '점포수', growth_col: '증감율(%)'}
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)

# 탭 2: 인기 업종 순위
with tab2:
    st.subheader(f"🏆 점포수 기준 인기 업종 Top {top_n}")
    
    top_stores_df = filtered_df.sort_values(by=stores_col, ascending=False).head(top_n)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 인기 업종 순위")
        
        # 순위 테이블
        display_df2 = top_stores_df[[industry_col, stores_col, growth_col]].copy()
        display_df2.index = range(1, len(display_df2) + 1)
        display_df2.columns = ['업종명', '점포수', '증감율(%)']
        
        styled_df2 = display_df2.style.format({
            '점포수': '{:,.0f}',
            '증감율(%)': '{:.2f}'
        })
        
        st.dataframe(styled_df2, use_container_width=True, height=400)
        
        # 통계 정보
        st.markdown("##### 📊 인기 업종 통계")
        stat_col1, stat_col2 = st.columns(2)
        with stat_col1:
            st.metric("평균 점포수", f"{top_stores_df[stores_col].mean():,.0f}개")
        with stat_col2:
            st.metric("총 점포수", f"{top_stores_df[stores_col].sum():,.0f}개")
    
    with col2:
        st.markdown("#### 📊 점포수 시각화")
        
        # 가로 막대 차트
        fig3 = go.Figure()
        
        fig3.add_trace(go.Bar(
            y=top_stores_df[industry_col],
            x=top_stores_df[stores_col],
            orientation='h',
            marker=dict(
                color=top_stores_df[stores_col],
                colorscale='Blues',
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=top_stores_df[stores_col].apply(lambda x: f'{x:,.0f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>점포수: %{x:,.0f}개<extra></extra>'
        ))
        
        fig3.update_layout(
            title='점포수 Top 10',
            xaxis_title='점포수 (개)',
            yaxis_title='',
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            margin=dict(l=10, r=50, t=40, b=40)
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # 파이 차트
        st.markdown("#### 📊 점포수 비율")
        fig4 = px.pie(
            top_stores_df,
            values=stores_col,
            names=industry_col,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig4.update_traces(textposition='inside', textinfo='percent+label', textfont_size=10)
        fig4.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# 탭 3: 종합 비교 분석
with tab3:
    st.subheader("📊 증감율 vs 점포수 종합 분석")
    
    # 버블 차트
    fig5 = px.scatter(
        filtered_df.head(50),
        x=stores_col,
        y=growth_col,
        size=stores_col,
        color=growth_col,
        hover_name=industry_col,
        color_continuous_scale='RdYlGn',
        labels={stores_col: '점포수', growth_col: '증감율(%)'},
        title=f'{region_title} 지역 업종 분포 (상위 50개)'
    )
    
    # 기준선 추가
    fig5.add_hline(y=min_growth_rate, line_dash="dash", line_color="red", 
                   annotation_text=f"고성장 기준선 ({min_growth_rate}%)")
    fig5.add_hline(y=0, line_dash="dash", line_color="gray", 
                   annotation_text="증감 기준선 (0%)")
    
    fig5.update_layout(height=500)
    st.plotly_chart(fig5, use_container_width=True)
    
    # 4분면 분석
    st.markdown("#### 🎯 업종 4분면 분석")
    
    median_stores = filtered_df[stores_col].median()
    median_growth = filtered_df[growth_col].median()
    
    q1 = filtered_df[(filtered_df[stores_col] >= median_stores) & (filtered_df[growth_col] >= median_growth)]
    q2 = filtered_df[(filtered_df[stores_col] < median_stores) & (filtered_df[growth_col] >= median_growth)]
    q3 = filtered_df[(filtered_df[stores_col] < median_stores) & (filtered_df[growth_col] < median_growth)]
    q4 = filtered_df[(filtered_df[stores_col] >= median_stores) & (filtered_df[growth_col] < median_growth)]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌟 스타 업종", f"{len(q1)}개", help="높은 점포수 + 높은 성장률")
        with st.expander("상위 5개 보기"):
            if not q1.empty:
                st.write(q1.nlargest(5, growth_col)[industry_col].tolist())
    
    with col2:
        st.metric("🚀 성장 업종", f"{len(q2)}개", help="낮은 점포수 + 높은 성장률")
        with st.expander("상위 5개 보기"):
            if not q2.empty:
                st.write(q2.nlargest(5, growth_col)[industry_col].tolist())
    
    with col3:
        st.metric("⚠️ 주의 업종", f"{len(q3)}개", help="낮은 점포수 + 낮은 성장률")
        with st.expander("상위 5개 보기"):
            if not q3.empty:
                st.write(q3.head(5)[industry_col].tolist())
    
    with col4:
        st.metric("🏰 안정 업종", f"{len(q4)}개", help="높은 점포수 + 낮은 성장률")
        with st.expander("상위 5개 보기"):
            if not q4.empty:
                st.write(q4.nlargest(5, stores_col)[industry_col].tolist())

# 탭 4: 상세 데이터
with tab4:
    st.subheader(f"📋 {region_title} 지역 전체 업종 데이터")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_min_growth = st.number_input("최소 증감율 (%)", value=-100.0, step=10.0)
    with col2:
        filter_min_stores = st.number_input("최소 점포수", value=0, step=100)
    with col3:
        sort_option = st.selectbox("정렬 기준", ["점포수 높은순", "점포수 낮은순", "증감율 높은순", "증감율 낮은순"])
    
    # 정렬 적용
    sort_mapping = {
        "점포수 높은순": (stores_col, False),
        "점포수 낮은순": (stores_col, True),
        "증감율 높은순": (growth_col, False),
        "증감율 낮은순": (growth_col, True)
    }
    sort_col, sort_asc = sort_mapping[sort_option]
    
    # 필터링 및 정렬
    detail_df = filtered_df[
        (filtered_df[growth_col] >= filter_min_growth) & 
        (filtered_df[stores_col] >= filter_min_stores)
    ].sort_values(by=sort_col, ascending=sort_asc)
    
    st.info(f"📊 필터링된 업종: **{len(detail_df)}개** / 전체 {len(filtered_df)}개")
    
    # 데이터 테이블
    st.dataframe(
        detail_df,
        use_container_width=True,
        height=500
    )
    
    # CSV 다운로드
    csv = detail_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 파일 다운로드",
        data=csv,
        file_name=f"{region_title}_업종현황_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
