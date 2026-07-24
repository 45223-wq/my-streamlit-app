import sys
import os

# ดึงเส้นทางของโฟลเดอร์ปัจจุบันเพื่อให้ Python รู้จักไฟล์อื่น
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st
import cv2
from blind_mode import process_blind_mode
from color_mode import process_color_mode

# ==========================================
# 1. SET UP PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Ophiuchus Project",
    page_icon="⚕️",
    layout="centered"
)

st.title("⚕️ Ophiuchus Project")
st.subheader("AI-Powered Assistive Web Application Proof of Concept Prototype")
st.write("---")

# ==========================================
# 2. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🧭 Navigation")
mode = st.sidebar.radio(
    "Select Mode / เลือกโหมดการทำงาน:",
    ["Home (หน้าแรก)", "Blind Mode (โหมดคนตาบอด)", "Color Blind Mode (โหมดตาบอดสี)"]
)

st.sidebar.write("---")
st.sidebar.info("Device: Huawei MateBook D 15\n\nPowered by Streamlit & OpenCV")

# ==========================================
# [FIXED BUG] 🛠️ ระบบตรวจจับการสลับโหมดเพื่อรีเซ็ตกล้องด่วน!
# ==========================================
# สร้างตัวแปรเก็บโหมดล่าสุดที่ผู้ใช้กดคลิกไว้ในระบบความจำ (Session State)
if "previous_mode" not in st.session_state:
    st.session_state.previous_mode = mode

# ถ้า "โหมดปัจจุบัน" ไม่ตรงกับ "โหมดก่อนหน้า" แปลว่าผู้ใช้เพิ่งกดเปลี่ยนเมนูตรง Sidebar!
if st.session_state.previous_mode != mode:
    # สั่งดับสวิตช์กล้องของทุกโหมดทันทีเพื่อคืนค่าทรัพยากรกล้องให้ Windows
    st.session_state.blind_cam_on = False
    st.session_state.color_cam_on = False
    
    # อัปเดตโหมดล่าสุดให้เป็นปัจจุบัน
    st.session_state.previous_mode = mode
    
    # สั่งให้ Streamlit รันหน้าเว็บใหม่อีกรอบแบบคลีน ๆ เพื่อเคลียร์กล้องค้าง
    st.rerun()

# ==========================================
# 3. ROUTING TO EACH MODE
# ==========================================
if mode == "Home (หน้าแรก)":
    st.header("🏠 Welcome to Ophiuchus Project")
    st.write("""
    โครงการพัฒนาสมองกลฝังตัวและซอฟต์แวร์ต้นแบบเพื่อช่วยเหลือผู้พิการทางสายตาและผู้มีภาวะตาบอดสี
    
    * **Blind Mode:** ระบบตรวจจับสิ่งกีดขวางระยะใกล้ (< 1 เมตร) พร้อมระบบแจ้งเตือนด้วยเสียง
    * **Color Blind Mode:** ระบบช่วยระบุชื่อสีตรงกลางภาพ และฟิลเตอร์ช่วยปรับสเปกตรัมสีแดง-เขียว
    """)
    
elif mode == "Blind Mode (โหมดคนตาบอด)":
    process_blind_mode()

elif mode == "Color Blind Mode (โหมดตาบอดสี)":
    process_color_mode()