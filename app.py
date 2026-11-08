import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# ------------------------------------------------------------------
# 頁面設定
# ------------------------------------------------------------------
st.set_page_config(page_title="公開資訊觀測站資料", page_icon="📊", layout="wide")

# 原程式使用 verify=False，會產生 InsecureRequestWarning，這裡關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_O_1.csv"  # 換連結


# ------------------------------------------------------------------
# 資料讀取（快取 1 小時，避免每次互動都重新下載）
# ------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="資料下載中...")
def load_data(url: str, verify_ssl: bool) -> pd.DataFrame:
    response = requests.get(url, verify=verify_ssl, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")  # 繁體中文
    df = df.dropna()
    return df.reset_index(drop=True)


# ------------------------------------------------------------------
# 側邊欄
# ------------------------------------------------------------------
st.sidebar.header("設定")
url = st.sidebar.text_input("CSV 連結", value=DEFAULT_URL)
verify_ssl = st.sidebar.checkbox("驗證 SSL 憑證", value=False, help="原程式為 verify=False")

if st.sidebar.button("🔄 重新下載資料"):
    st.cache_data.clear()
    st.rerun()

# ------------------------------------------------------------------
# 主畫面
# ------------------------------------------------------------------
st.title("📊 公開資訊觀測站資料")
st.caption(f"資料來源：{url}")

try:
    df = load_data(url, verify_ssl)
except requests.exceptions.RequestException as e:
    st.error(f"下載資料失敗：{e}")
    st.stop()
except Exception as e:
    st.error(f"資料解析失敗：{e}")
    st.stop()

if df.empty:
    st.warning("沒有資料（可能全部列都含有空值而被 dropna 移除）。")
    st.stop()

# 關鍵字搜尋
keyword = st.text_input("🔍 關鍵字搜尋（搜尋所有欄位）")
if keyword:
    mask = df.astype(str).apply(lambda col: col.str.contains(keyword, case=False, na=False))
    df_show = df[mask.any(axis=1)]
else:
    df_show = df

col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df_show):,}")
col2.metric("欄位數", len(df_show.columns))

st.dataframe(df_show, use_container_width=True, height=500)

# 下載按鈕（utf-8-sig 讓 Excel 開啟繁體中文不亂碼）
csv_bytes = df_show.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="⬇️ 下載 CSV",
    data=csv_bytes,
    file_name="data01.csv",
    mime="text/csv",
)
