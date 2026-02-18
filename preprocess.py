"""
카페 입지 분석 대시보드용 데이터 전처리 스크립트
4개 CSV 파일을 읽어 대시보드에서 사용할 JSON 데이터를 생성합니다.
"""

import pandas as pd
import json
import os
import warnings
warnings.filterwarnings('ignore')

# 데이터 경로 설정
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUTPUT_DIR = os.path.dirname(__file__)

BRANDS = ['더벤티', '매머드커피', '메가커피', '빽다방', '컴포즈커피']
BRAND_COLS = [f'count_{b}' for b in BRANDS]

# 브랜드별 색상
BRAND_COLORS = {
    '더벤티':    '#FF6B6B',
    '매머드커피': '#4ECDC4',
    '메가커피':  '#FFE66D',
    '빽다방':    '#A8E6CF',
    '컴포즈커피': '#C3A6FF',
}

print("📂 데이터 로딩 중...")

# ─────────────────────────────────────────────
# 1. brand_analysis_master.csv 로드
# ─────────────────────────────────────────────
print("  [1/4] brand_analysis_master.csv 로딩...")
df_brand = pd.read_csv(
    os.path.join(DATA_DIR, 'brand_analysis_master.csv'),
    encoding='utf-8-sig'
)

# 행정동코드를 문자열로 통일
df_brand['행정동코드'] = df_brand['행정동코드'].astype(str).str.strip()

# 숫자형 변환
brand_cols_numeric = BRAND_COLS + ['total_workers', 'female_workers',
    '당월_매출_금액', '남성_매출_금액', '여성_매출_금액',
    '연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액',
    '연령대_40_매출_금액', '연령대_50_매출_금액', '연령대_60_이상_매출_금액']
for col in brand_cols_numeric:
    if col in df_brand.columns:
        df_brand[col] = pd.to_numeric(df_brand[col], errors='coerce')

# 행정동코드별 집계 (브랜드 카운트는 max, 매출은 sum)
agg_dict = {}
for col in BRAND_COLS:
    if col in df_brand.columns:
        agg_dict[col] = 'max'
for col in ['total_workers', 'female_workers']:
    if col in df_brand.columns:
        agg_dict[col] = 'max'
for col in ['당월_매출_금액', '남성_매출_금액', '여성_매출_금액',
            '연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액',
            '연령대_40_매출_금액', '연령대_50_매출_금액', '연령대_60_이상_매출_금액']:
    if col in df_brand.columns:
        agg_dict[col] = 'sum'

df_brand_agg = df_brand.groupby(['행정동코드', '행정동_코드_명'], as_index=False).agg(agg_dict)
print(f"     → {len(df_brand_agg)}개 행정동")

# ─────────────────────────────────────────────
# 2. seoul_dong_attractiveness.csv 로드 (업데이트된 컬럼명)
# ─────────────────────────────────────────────
print("  [2/4] seoul_dong_attractiveness.csv 로딩...")
df_attr = pd.read_csv(
    os.path.join(DATA_DIR, 'seoul_dong_attractiveness.csv'),
    encoding='utf-8-sig'
)
# 컬럼명 확인 후 행정동_코드 컬럼 사용 (10자리)
print(f"     컬럼: {list(df_attr.columns)}")
df_attr['행정동_코드'] = df_attr['행정동_코드'].astype(str).str.strip()
print(f"     → {len(df_attr)}개 행정동")

# ─────────────────────────────────────────────
# 3. seoul_caffee_data_with_coords.csv 로드 (좌표 데이터)
# ─────────────────────────────────────────────
print("  [3/4] seoul_caffee_data_with_coords.csv 로딩 (대용량)...")
df_coords = pd.read_csv(
    os.path.join(DATA_DIR, 'seoul_caffee_data_with_coords.csv'),
    encoding='utf-8-sig',
    usecols=lambda c: c in ['행정동코드', '사업장명', '브랜드', 'latitude', 'longitude']
)
df_coords['행정동코드'] = df_coords['행정동코드'].astype(str).str.strip()
df_coords['latitude'] = pd.to_numeric(df_coords['latitude'], errors='coerce')
df_coords['longitude'] = pd.to_numeric(df_coords['longitude'], errors='coerce')

# 저가 브랜드만 필터링
df_target = df_coords[df_coords['브랜드'].isin(BRANDS)].dropna(subset=['latitude', 'longitude'])
print(f"     → 전체 카페: {len(df_coords):,}개, 저가 브랜드: {len(df_target):,}개")

# ─────────────────────────────────────────────
# 4. seoul_caffee_data_with_brand.csv 로드
# ─────────────────────────────────────────────
print("  [4/4] seoul_caffee_data_with_brand.csv 로딩 (대용량)...")
df_brand_raw = pd.read_csv(
    os.path.join(DATA_DIR, 'seoul_caffee_data_with_brand.csv'),
    encoding='utf-8-sig',
    usecols=lambda c: c in ['행정동코드', '사업장명', '브랜드']
)
df_brand_raw['행정동코드'] = df_brand_raw['행정동코드'].astype(str).str.strip()
print(f"     → {len(df_brand_raw):,}개 카페")

# ─────────────────────────────────────────────
# 데이터 병합 (행정동코드 직접 매칭)
# ─────────────────────────────────────────────
print("\n🔗 데이터 병합 중...")

df_merged = df_brand_agg.merge(
    df_attr.rename(columns={'행정동_코드': '행정동코드'}),
    on='행정동코드',
    how='left'
)
matched = df_merged['매력도점수'].notna().sum()
print(f"  병합 결과: {len(df_merged)}개 행정동, 매력도 매칭: {matched}개")

# ─────────────────────────────────────────────
# JSON 데이터 생성
# ─────────────────────────────────────────────
print("\n📊 JSON 데이터 생성 중...")

# 컬럼명 매핑 (한국어 → 영어 키)
COL_MAP = {
    '총_매출':       'total_sales',
    '총_직원수':     'total_workers_attr',
    '카페_수':       'cafe_count',
    'm²당_평균_가격': 'avg_price_per_m2',
    '수요점수':      'demand_score',
    '경쟁점수':      'competition_score',
    '비용점수':      'cost_score',
    '매력도점수':    'attractiveness_score',
}

def safe_float(val):
    try:
        v = float(val)
        return None if pd.isna(v) else v
    except:
        return None

def safe_int(val):
    try:
        v = float(val)
        return 0 if pd.isna(v) else int(v)
    except:
        return 0

# 1) 행정동별 브랜드 현황 + 매력도 점수
dong_data = []
for _, row in df_merged.iterrows():
    brand_counts = {}
    total_brand = 0
    for brand, col in zip(BRANDS, BRAND_COLS):
        cnt = safe_int(row.get(col, 0))
        brand_counts[brand] = cnt
        total_brand += cnt

    dong_data.append({
        'dong_code': str(row['행정동코드']),
        'dong_name': str(row['행정동_코드_명']),
        'brands': brand_counts,
        'total_brand_count': total_brand,
        'total_workers': safe_int(row.get('total_workers')),
        'female_workers': safe_int(row.get('female_workers')),
        'monthly_sales': safe_float(row.get('당월_매출_금액')) or 0,
        'male_sales': safe_float(row.get('남성_매출_금액')) or 0,
        'female_sales': safe_float(row.get('여성_매출_금액')) or 0,
        'age_10': safe_float(row.get('연령대_10_매출_금액')) or 0,
        'age_20': safe_float(row.get('연령대_20_매출_금액')) or 0,
        'age_30': safe_float(row.get('연령대_30_매출_금액')) or 0,
        'age_40': safe_float(row.get('연령대_40_매출_금액')) or 0,
        'age_50': safe_float(row.get('연령대_50_매출_금액')) or 0,
        'age_60': safe_float(row.get('연령대_60_이상_매출_금액')) or 0,
        'attractiveness_score': safe_float(row.get('매력도점수')),
        'demand_score': safe_float(row.get('수요점수')),
        'competition_score': safe_float(row.get('경쟁점수')),
        'cost_score': safe_float(row.get('비용점수')),
        'cafe_count': safe_int(row.get('카페_수')),
        'avg_price_per_m2': safe_float(row.get('m²당_평균_가격')) or 0,
    })

# 2) 저가 브랜드 카페 좌표 데이터 (지도용)
map_points = []
for _, row in df_target.iterrows():
    map_points.append({
        'brand': str(row['브랜드']),
        'name': str(row['사업장명']),
        'lat': float(row['latitude']),
        'lng': float(row['longitude']),
        'dong_code': str(row['행정동코드']),
    })

# 3) 브랜드별 통계
brand_stats = {}
for brand in BRANDS:
    col = f'count_{brand}'
    total_stores = safe_int(df_merged[col].sum()) if col in df_merged.columns else 0

    # 해당 브랜드가 있는 행정동의 매출 합계 / 총 매장 수 → 점포당 평균 월매출
    brand_dongs = df_merged[df_merged[col] > 0] if col in df_merged.columns else pd.DataFrame()
    total_sales_for_brand = brand_dongs['당월_매출_금액'].sum() if '당월_매출_금액' in brand_dongs.columns else 0
    avg_monthly_sales = int(total_sales_for_brand / total_stores / 1e4) if total_stores > 0 else 0  # 만원 단위

    brand_stats[brand] = {
        'color': BRAND_COLORS[brand],
        'total_stores': total_stores,
        'dong_count': int((df_merged[col] > 0).sum()) if col in df_merged.columns else 0,
        'map_count': int((df_target['브랜드'] == brand).sum()),
        'avg_monthly_sales': avg_monthly_sales,  # 점포당 평균 월매출 (만원)
    }


# 4) 입지 추천: 매력도 점수 있는 동 중 해당 브랜드 없는 곳
recommend_data = []
for d in dong_data:
    if d['attractiveness_score'] is not None:
        for brand in BRANDS:
            if d['brands'].get(brand, 0) == 0:
                recommend_data.append({
                    'dong_name': d['dong_name'],
                    'dong_code': d['dong_code'],
                    'brand': brand,
                    'attractiveness_score': d['attractiveness_score'],
                    'demand_score': d['demand_score'],
                    'competition_score': d['competition_score'],
                    'cost_score': d['cost_score'],
                    'total_workers': d['total_workers'],
                    'monthly_sales': d['monthly_sales'],
                    'cafe_count': d['cafe_count'],
                })

recommend_data.sort(key=lambda x: x['attractiveness_score'], reverse=True)

# ─────────────────────────────────────────────
# JSON 저장
# ─────────────────────────────────────────────
print("\n💾 JSON 파일 저장 중...")

output = {
    'brands': BRANDS,
    'brand_colors': BRAND_COLORS,
    'brand_stats': brand_stats,
    'dong_data': dong_data,
    'map_points': map_points,
    'recommend_top': recommend_data[:200],
}

out_path = os.path.join(OUTPUT_DIR, 'dashboard_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

file_size = os.path.getsize(out_path) / 1024 / 1024
print(f"  ✅ dashboard_data.json 저장 완료 ({file_size:.1f} MB)")
print(f"     - 행정동 수: {len(dong_data)}")
print(f"     - 지도 포인트 수: {len(map_points):,}")
print(f"     - 입지 추천 후보: {len(recommend_data):,}")
print("\n✅ 전처리 완료!")
