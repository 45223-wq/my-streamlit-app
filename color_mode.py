import streamlit as st
import cv2
import numpy as np

def detect_color_name(h, s, v):
    """ฟังก์ชันวิเคราะห์เฉดสีจากค่า HSV"""
    if s < 40 or v < 40:
        if v < 40: return "สีดำ (Black)"
        if v > 200: return "สีขาว (White)"
        return "สีเทา (Gray)"
        
    if (0 <= h < 10) or (170 <= h <= 180):
        return "🔴 สีแดง (Red)"
    elif 10 <= h < 25:
        return "🟠 สีส้ม (Orange)"
    elif 25 <= h < 35:
        return "🟡 สีเหลือง (Yellow)"
    elif 35 <= h < 85:
        return "🟢 สีเขียว (Green)"
    elif 85 <= h < 130:
        return "🔵 สีน้ำเงิน/ฟ้า (Blue)"
    elif 130 <= h < 170:
        return "🟣 สีม่วง (Purple)"
    
    return "ไม่สามารถระบุสีได้ชัดเจน"

def process_color_mode():
    st.header("🎨 Color Blind Mode")
    st.caption("ระบบแยกแยะชื่อสีและปรับคอนทราสต์สำหรับภาวะตาบอดสีแดง-เขียว")

    st.write("### 🎛️ Filter Settings")
    apply_filter = st.checkbox("เปิดใช้งานฟิลเตอร์ช่วยมองเห็นสีแดง-เขียว (Daltonization Simulation)")
    
    if "color_cam_on" not in st.session_state:
        st.session_state.color_cam_on = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎥 Start Camera (เปิดกล้อง)", use_container_width=True, key="color_start"):
            st.session_state.color_cam_on = True
    with col2:
        if st.button("🛑 Stop Camera (ปิดกล้อง)", use_container_width=True, key="color_stop"):
            st.session_state.color_cam_on = False

    color_placeholder = st.empty()
    FRAME_WINDOW_COLOR = st.image([])

    if st.session_state.color_cam_on:
        cap = cv2.VideoCapture(0)
        
        while st.session_state.color_cam_on:
            # 1. เช็กสวิตช์ปิดกล้อง
            if not st.session_state.color_cam_on:
                break
                
            ret, frame = cap.read()
            if not ret:
                st.error("ไม่สามารถเข้าถึงกล้องเว็บแคมได้")
                break
            
            # [ยัดกลับเข้าลูป] 2. ประมวลผลขนาดภาพและหาจุดกึ่งกลางจอ
            height, width, _ = frame.shape
            cx, cy = int(width / 2), int(height / 2)
                
            # แปลงเป็น RGB ก่อนวิเคราะห์ ค่าสีจะได้ไม่เพี้ยน
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            # วิเคราะห์สีตรงกลางจอ 10x10 พิกเซล
            roi = frame_rgb[cy-5:cy+5, cx-5:cx+5]
            hsv_roi = cv2.cvtColor(cv2.cvtColor(roi, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2HSV)
            avg_hsv = np.mean(hsv_roi, axis=(0, 1))
                
            h_val, s_val, v_val = int(avg_hsv[0]), int(avg_hsv[1]), int(avg_hsv[2])
            color_name = detect_color_name(h_val, s_val, v_val)
                
            # ปรับฟิลเตอร์ช่วยคนตาบอดสีแดง-เขียว (ถ้าเปิดใช้งาน)
            if apply_filter:
                r_ch, g_ch, b_ch = cv2.split(frame_rgb)
                r_tuned = cv2.addWeighted(r_ch, 1.2, g_ch, 0.1, 0)
                g_tuned = cv2.addWeighted(g_ch, 0.8, r_ch, 0.1, 0)
                frame_rgb = cv2.merge((r_tuned, g_tuned, b_ch))

            # วาดเป้าเล็ง (Crosshair) สีขาว
            cv2.rectangle(frame_rgb, (cx-20, cy-20), (cx+20, cy+20), (255, 255, 255), 2)
            cv2.line(frame_rgb, (cx-30, cy), (cx+30, cy), (255, 255, 255), 1)
            cv2.line(frame_rgb, (cx, cy-30), (cx, cy+30), (255, 255, 255), 1)
                
            # แสดงป้ายชื่อภาษาอังกฤษบนหน้าจอกล้อง
            english_label = color_name.split()[-1] if ")" in color_name else color_name
            cv2.putText(frame_rgb, english_label, (cx-50, cy-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

            # อัปเดตข้อความขนาดใหญ่บนหน้าเว็บ Streamlit
            color_placeholder.markdown(f"### 📍 วัตถุตรงกลางเป้าเล็งคือ: **{color_name}**")
                
            # แสดงภาพวิดีโออัปเดตแบบต่อเนื่องในลูป
            FRAME_WINDOW_COLOR.image(frame_rgb)
            
        # [ย้ายมาตรงนี้] คืนค่ากล้องเมื่อกดยกเลิกหรือหลุดลูป while จริง ๆ เท่านั้น
        cap.release()
        cv2.destroyAllWindows()
    else:
        st.write("กล้องปิดอยู่... กรุณากด Start Camera เพื่อเริ่มทำงาน")