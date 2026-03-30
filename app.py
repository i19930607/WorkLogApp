import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

st.set_page_config(page_title="工作日誌填寫系統", layout="centered")

# --- 獨立記憶體設定 (支援多人同時連線使用) ---
# 利用 session_state 讓每個打開網頁的手機/電腦都有自己獨立的資料空間，不會互相覆蓋
if "db" not in st.session_state:
    st.session_state.db = {
        "year": 115, 
        "month": 3, 
        "day": 26, 
        "co_sales": "", 
        "sales": "", # 預設改為空白，讓每位業務自己填寫
        "records": []
    }

# 編輯狀態追蹤
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = -1

st.title("📝 工作日誌 (多人獨立版)")

# --- 頂部：基本資料設定 (拆分日期與業務) ---
st.subheader("📅 日期設定")
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    st.session_state.db["year"] = st.number_input("年度", min_value=110, max_value=150, value=st.session_state.db["year"])
with col_d2:
    st.session_state.db["month"] = st.number_input("月", min_value=1, max_value=12, value=st.session_state.db["month"])
with col_d3:
    st.session_state.db["day"] = st.number_input("日", min_value=1, max_value=31, value=st.session_state.db["day"])

st.subheader("🧑‍💼 業務人員設定")
col_s1, col_s2 = st.columns(2)
with col_s1:
    st.session_state.db["sales"] = st.text_input("業務", value=st.session_state.db.get("sales", ""))
with col_s2:
    st.session_state.db["co_sales"] = st.text_input("同行業務", value=st.session_state.db.get("co_sales", ""))

st.divider()

# --- 中間：新增或編輯單筆紀錄 ---
default_items = ["古道", "台鹽", "南聯", "海尼根", "麒麟", "一口香", "清露", "台鹽水", "紅牛", "老菜脯", "好勁道", "圍爐瓦斯罐"]

if st.session_state.edit_idx >= 0:
    # ====== 編輯模式 ======
    idx = st.session_state.edit_idx
    rec = st.session_state.db["records"][idx]
    st.subheader(f"✏️ 編輯第 {idx+1} 筆拜訪")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            customer = st.text_input("客戶名稱", value=rec.get("customer", ""), key="edit_c")
        with col2:
            visit_time = st.text_input("拜訪時間 (例如: 1500)", value=rec.get("time", ""), key="edit_t")
            
        safe_items = [x for x in rec.get("items", []) if x in default_items]
        items = st.multiselect("經銷品項", options=default_items, default=safe_items, key="edit_i")
        extra_items = st.text_input("其他品項 (用逗號分隔)", value=rec.get("extra_items", ""), key="edit_ei")
        safe_purposes = [x for x in rec.get("purposes", []) if x in ["抄貨", "收款", "開發", "其他"]]
        purposes = st.multiselect("拜訪目的", ["抄貨", "收款", "開發", "其他"], default=safe_purposes, key="edit_p")
        notes = st.text_area("重點紀錄", value=rec.get("notes", ""), key="edit_n")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 儲存修改", type="primary", use_container_width=True):
                if not customer:
                    st.error("請至少填寫客戶名稱！")
                else:
                    st.session_state.db["records"][idx] = {
                        "customer": customer, "time": visit_time,
                        "items": items, "extra_items": extra_items, 
                        "purposes": purposes, "notes": notes
                    }
                    st.session_state.edit_idx = -1
                    st.rerun()
        with col_btn2:
            if st.button("❌ 取消編輯", use_container_width=True):
                st.session_state.edit_idx = -1
                st.rerun()

else:
    # ====== 新增模式 ======
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
                    st.success(f"已儲存 {customer} 的紀錄！")
                    st.rerun()

st.divider()

# --- 底部：總覽與輸出 ---
st.subheader("📋 今日拜訪清單")
if not st.session_state.db["records"]:
    st.info("目前還沒有任何紀錄。")
else:
    for idx, r in enumerate(st.session_state.db["records"]):
        col_txt, col_edit, col_del = st.columns([7, 1, 1])
        with col_txt:
            st.write(f"**{idx+1}. {r['customer']}** ({r['time']}) - 目的: {','.join(r['purposes'])}")
        with col_edit:
            if st.button("✏️", key=f"edit_btn_{idx}"):
                st.session_state.edit_idx = idx
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_btn_{idx}"):
                st.session_state.db["records"].pop(idx)
                if st.session_state.edit_idx == idx:
                    st.session_state.edit_idx = -1
                elif st.session_state.edit_idx > idx:
                    st.session_state.edit_idx -= 1
                st.rerun()

    st.write("") 
    if st.button("🗑️ 清空今天所有紀錄"):
        st.session_state.db["records"] = []
        st.session_state.edit_idx = -1
        st.rerun()

    def draw_centered_text(draw_obj, text, center_x, y, font, text_color):
        text = str(text)
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw_obj.text((center_x - text_width / 2, y), text, font=font, fill=text_color)

    st.write("")
    # --- 產生 PDF ---
    if st.button("🖨️ 產生 PDF 日誌表"):
        try:
            img = Image.open("blank_form.jpg")
            draw = ImageDraw.Draw(img)
            
            font_path = "msjh.ttc"  
            
            font_m = ImageFont.truetype(font_path, 16) 
            font_s = ImageFont.truetype(font_path, 11) 
            font_v = ImageFont.truetype(font_path, 18) 
            text_color = (0, 0, 0)

            draw.text((596, 17), st.session_state.db["co_sales"], font=font_m, fill=text_color)
            draw.text((836, 17), st.session_state.db["sales"], font=font_m, fill=text_color)
            
            ROW_SPACING = 50  
            START_Y_SINGLE = 98  
            START_Y_MULTI = 82   
            
            for i, record in enumerate(st.session_state.db["records"]):
                if i >= 10: break
                
                base_y = START_Y_SINGLE + (i * ROW_SPACING)
                base_y_multi = START_Y_MULTI + (i * ROW_SPACING)
                
                draw_centered_text(draw, st.session_state.db["month"], 53, base_y, font_m, text_color)
                draw_centered_text(draw, st.session_state.db["day"], 93, base_y, font_m, text_color)
                
                draw.text((132, base_y), record["customer"], font=font_m, fill=text_color)
                draw.text((232, base_y), record["time"], font=font_m, fill=text_color)
                
                final_items = record["items"].copy()
                if record["extra_items"]:
                    final_items.extend([item.strip() for item in record["extra_items"].split(",") if item.strip()])
                items_str = "、".join(final_items)
                wrapped_items = textwrap.fill(items_str, width=12) 
                draw.text((334, base_y_multi), wrapped_items, font=font_s, fill=text_color, spacing=4)
                
                if "抄貨" in record["purposes"]: draw_centered_text(draw, "V", 530, base_y, font_v, text_color)
                if "收款" in record["purposes"]: draw_centered_text(draw, "V", 570, base_y, font_v, text_color)
                if "開發" in record["purposes"]: draw_centered_text(draw, "V", 610, base_y, font_v, text_color)
                if "其他" in record["purposes"]: draw_centered_text(draw, "V", 650, base_y, font_v, text_color)
                    
                wrapped_notes = textwrap.fill(record["notes"], width=24)
                draw.text((682, base_y_multi), wrapped_notes, font=font_s, fill=text_color, spacing=4)

            img_rgb = img.convert('RGB')
            pdf_buffer = io.BytesIO()
            img_rgb.save(pdf_buffer, format="PDF", resolution=100.0)
            
            st.success("🎉 PDF 產生成功！")
            
            # 將業務名稱加入到下載檔案的名稱中，方便你區分是誰交的日誌
            sales_name = st.session_state.db["sales"] if st.session_state.db["sales"] else "業務未填"
            file_name_str = f"工作日誌_{sales_name}_{st.session_state.db['month']}月{st.session_state.db['day']}日.pdf"
            
            st.download_button(
                label="📥 下載今日工作日誌 PDF",
                data=pdf_buffer.getvalue(),
                file_name=file_name_str,
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"發生了一個錯誤：{e}")