import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import json
import os

st.set_page_config(page_title="工作日誌填寫系統", layout="centered")

# --- 資料存檔設定 ---
DATA_FILE = "daily_records.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"year": 115, "month": 3, "day": 26, "co_sales": "", "sales": "李郡", "records": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

st.title("📝 工作日誌 (隨到隨記版)")

# --- 頂部：基本資料設定 ---
st.subheader("表單基本資料")
col_top1, col_top2, col_top3 = st.columns(3)
with col_top1:
    st.session_state.db["year"] = st.number_input("年度", min_value=110, max_value=150, value=st.session_state.db["year"])
    st.session_state.db["month"] = st.number_input("月", min_value=1, max_value=12, value=st.session_state.db["month"])
    st.session_state.db["day"] = st.number_input("日", min_value=1, max_value=31, value=st.session_state.db["day"])
with col_top2:
    st.session_state.db["co_sales"] = st.text_input("同行業務", value=st.session_state.db.get("co_sales", ""))
with col_top3:
    st.session_state.db["sales"] = st.text_input("業務", value=st.session_state.db.get("sales", "李郡"))

save_data(st.session_state.db)

st.divider()

# --- 中間：新增單筆紀錄 ---
st.subheader("➕ 新增一筆拜訪 (目前累積: {}/10)".format(len(st.session_state.db["records"])))

if len(st.session_state.db["records"]) >= 10:
    st.warning("今天已經填滿 10 筆紀錄囉！請先輸出 PDF。")
else:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            customer = st.text_input("客戶名稱", key="new_c")
        with col2:
            visit_time = st.text_input("拜訪時間 (例如: 1500)", key="new_t")
            
        default_items = ["古道", "台鹽", "南聯", "海尼根", "麒麟", "一口香", "清露", "台鹽水", "紅牛", "老菜脯", "好勁道", "圍爐瓦斯罐"]
        items = st.multiselect("經銷品項", options=default_items, key="new_i")
        extra_items = st.text_input("其他品項 (用逗號分隔)", key="new_ei")
        purposes = st.multiselect("拜訪目的", ["抄貨", "收款", "開發", "其他"], key="new_p")
        notes = st.text_area("重點紀錄", key="new_n")
        
        if st.button("💾 儲存這筆紀錄", type="primary"):
            if not customer:
                st.error("請至少填寫客戶名稱！")
            else:
                new_record = {
                    "customer": customer, "time": visit_time,
                    "items": items, "extra_items": extra_items, 
                    "purposes": purposes, "notes": notes
                }
                st.session_state.db["records"].append(new_record)
                save_data(st.session_state.db)
                st.success(f"已儲存 {customer} 的紀錄！請重新整理網頁繼續填下一筆。")
                st.rerun()

st.divider()

# --- 底部：總覽與輸出 ---
st.subheader("📋 今日拜訪清單")
if not st.session_state.db["records"]:
    st.info("目前還沒有任何紀錄。")
else:
    for idx, r in enumerate(st.session_state.db["records"]):
        st.write(f"{idx+1}. **{r['customer']}** ({r['time']}) - 目的: {','.join(r['purposes'])}")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn2:
        if st.button("🗑️ 清空今天所有紀錄"):
            st.session_state.db["records"] = []
            save_data(st.session_state.db)
            st.rerun()

    def draw_centered_text(draw_obj, text, center_x, y, font, text_color):
        """只對月、日、打勾使用 X 軸置中，Y軸絕對不加料"""
        text = str(text)
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw_obj.text((center_x - text_width / 2, y), text, font=font, fill=text_color)

    # --- 產生 PDF ---
    if st.button("🖨️ 產生 PDF 日誌表"):
        try:
            img = Image.open("blank_form.jpg")
            draw = ImageDraw.Draw(img)
            font_path = "msjh.ttc"
            
            # 字體設定保持不變
            font_m = ImageFont.truetype(font_path, 16) 
            font_s = ImageFont.truetype(font_path, 11) 
            font_v = ImageFont.truetype(font_path, 18) 
            text_color = (0, 0, 0)

            # 基本資料 (Y 座標從 27 往上提 10 像素變成 17)
            draw.text((596, 17), st.session_state.db["co_sales"], font=font_m, fill=text_color)
            draw.text((836, 17), st.session_state.db["sales"], font=font_m, fill=text_color)
            
            # -----------------------------------------------------------------
            # 微調區：整體 Y 軸往上提 10 像素
            # -----------------------------------------------------------------
            ROW_SPACING = 50  
            START_Y_SINGLE = 98  # 原本是 108
            START_Y_MULTI = 82   # 原本是 92
            
            for i, record in enumerate(st.session_state.db["records"]):
                if i >= 10: break
                
                base_y = START_Y_SINGLE + (i * ROW_SPACING)
                base_y_multi = START_Y_MULTI + (i * ROW_SPACING)
                
                # 月、日 (套用你的 X 座標，置中對齊)
                draw_centered_text(draw, st.session_state.db["month"], 53, base_y, font_m, text_color)
                draw_centered_text(draw, st.session_state.db["day"], 93, base_y, font_m, text_color)
                
                # 客戶、時間 (套用你的 X 座標，靠左對齊)
                draw.text((132, base_y), record["customer"], font=font_m, fill=text_color)
                draw.text((232, base_y), record["time"], font=font_m, fill=text_color)
                
                # 品項 (套用你的 X:334，並調整換行寬度)
                final_items = record["items"].copy()
                if record["extra_items"]:
                    final_items.extend([item.strip() for item in record["extra_items"].split(",") if item.strip()])
                items_str = "、".join(final_items)
                wrapped_items = textwrap.fill(items_str, width=12) 
                draw.text((334, base_y_multi), wrapped_items, font=font_s, fill=text_color, spacing=4)
                
                # 目的打勾 (套用你的 X 座標，Y軸對齊單行文字基準)
                if "抄貨" in record["purposes"]: draw_centered_text(draw, "V", 530, base_y, font_v, text_color)
                if "收款" in record["purposes"]: draw_centered_text(draw, "V", 570, base_y, font_v, text_color)
                if "開發" in record["purposes"]: draw_centered_text(draw, "V", 610, base_y, font_v, text_color)
                if "其他" in record["purposes"]: draw_centered_text(draw, "V", 650, base_y, font_v, text_color)
                    
                # 重點紀錄 (套用你的 X:682，並調整換行寬度)
                wrapped_notes = textwrap.fill(record["notes"], width=24)
                draw.text((682, base_y_multi), wrapped_notes, font=font_s, fill=text_color, spacing=4)

            img_rgb = img.convert('RGB')
            pdf_buffer = io.BytesIO()
            img_rgb.save(pdf_buffer, format="PDF", resolution=100.0)
            
            st.success("🎉 PDF 產生成功！")
            st.download_button(
                label="📥 下載今日工作日誌 PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"工作日誌_{st.session_state.db['month']}月{st.session_state.db['day']}日.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"發生了一個錯誤：{e}")