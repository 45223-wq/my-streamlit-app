import streamlit as st
import cv2
import numpy as np
from gtts import gTTS
from ultralytics import YOLO
import time
import os
import pygame

def pre_cache_sounds():
    """ฟังก์ชันเจนไฟล์เสียงแจ้งเตือนสแตนด์บายไว้ล่วงหน้า เพื่อไม่ให้หน่วงในลูปกล้อง"""
    # รายชื่อวัตถุเด่นๆ ที่มักจะเจอระยะประชิด
    common_objects = ['person', 'chair', 'cup', 'bottle', 'cell phone', 'backpack', 'umbrella']
    
    # สร้างโฟลเดอร์สำหรับเก็บไฟล์เสียงถ้ายังไม่มี
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
        
    for obj in common_objects:
        file_path = f"sounds/{obj}.mp3"
        if not os.path.exists(file_path):
            try:
                tts = gTTS(text=f"Warning. {obj} ahead.", lang='en', slow=False)
                tts.save(file_path)
            except:
                pass
                
    # ไฟล์เสียงเตือนทั่วไปในกรณีเจอวัตถุอื่นนอกเหนือจากรายการข้างบน
    general_path = "sounds/general.mp3"
    if not os.path.exists(general_path):
        try:
            tts = gTTS(text="Warning. Obstacle ahead.", lang='en', slow=False)
            tts.save(general_path)
        except:
            pass

def play_cached_sound(label):
    """เรียกเล่นไฟล์เสียงจากในเครื่องทันทีแบบ Non-blocking และเสียงไม่ขาดหาย"""
    try:
        # ตรวจสอบว่าระบบเสียงของ pygame พร้อมใช้งานไหม
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # เลือกไฟล์เสียงตามชื่อวัตถุ
        file_path = f"sounds/{label}.mp3"
        if not os.path.exists(file_path):
            file_path = "sounds/general.mp3" # ถ้าไม่มีเสียงเฉพาะ ให้ใช้เสียงเตือนทั่วไป
            
        # ถ้าช่องเสียงกำลังเล่นอยู่ ให้ข้ามไปก่อนเพื่อป้องกันเสียงซ้อนจนฟังไม่รู้เรื่อง
        if pygame.mixer.music.get_busy():
            return
            
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
    except Exception as e:
        pass

def process_blind_mode():
    st.header("👁️ Blind Mode (YOLOv8)")
    st.caption("ระบบตรวจจับวัตถุและแจ้งเตือนระยะสิ่งกีดขวางด้วยเสียงสำหรับผู้พิการทางสายตา")

    # 1. เจนไฟล์เสียงเก็บไว้ในเครื่องล่วงหน้าทันทีที่เปิดโหมดนี้
    if "sounds_cached" not in st.session_state:
        with st.spinner("🎵 กำลังเตรียมระบบเสียงแจ้งเตือนแบบด่วน..."):
            pre_cache_sounds()
        st.session_state.sounds_cached = True

    # 2. โหลดโมเดล YOLOv8 nano
    if "yolo_model" not in st.session_state:
        try:
            with st.spinner("📦 กำลังเปิดใช้งานโมเดล YOLOv8 nano..."):
                st.session_state.yolo_model = YOLO('yolov8n.pt')
            st.success("✅ โหลดโมเดล YOLOv8 สำเร็จ!")
        except Exception as e:
            st.session_state.yolo_model = None
            st.warning("⚠️ โหลดโมเดลไม่สำเร็จ ระบบจะทำงานในโหมดกล้องปกติ")

    # จัดการสถานะปุ่มเปิด-ปิดกล้อง
    if "blind_cam_on" not in st.session_state:
        st.session_state.blind_cam_on = False
    
    if "last_alert_time" not in st.session_state:
        st.session_state.last_alert_time = 0.0

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎥 Start Camera (เปิดกล้อง)", use_container_width=True, key="blind_start"):
            st.session_state.blind_cam_on = True
    with col2:
        if st.button("🛑 Stop Camera (ปิดกล้อง)", use_container_width=True, key="blind_stop"):
            st.session_state.blind_cam_on = False

    status_placeholder = st.empty()
    FRAME_WINDOW_BLIND = st.image([])

    if st.session_state.blind_cam_on:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        while st.session_state.blind_cam_on:
            ret, frame = cap.read()
            if not ret:
                st.error("ไม่สามารถเข้าถึงกล้องเว็บแคมได้")
                break
                
            height, width, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            closest_object = None
            max_area_ratio = 0.0
            
            if st.session_state.yolo_model is not None:
                results = st.session_state.yolo_model(frame, stream=True, verbose=False)
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        cls_id = int(box.cls[0])
                        label = st.session_state.yolo_model.names[cls_id]
                        conf = float(box.conf[0])
                        
                        if conf > 0.45:
                            cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            
                            box_area = (x2 - x1) * (y2 - y1)
                            screen_area = width * height
                            area_ratio = box_area / screen_area
                            
                            is_close = area_ratio > 0.25
                            status_text = f"{label} [CLOSE]" if is_close else f"{label}"
                            color = (255, 0, 0) if is_close else (0, 255, 0)
                            
                            cv2.putText(frame_rgb, f"{status_text} {conf:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            
                            if is_close and (area_ratio > max_area_ratio):
                                max_area_ratio = area_ratio
                                closest_object = label

            # 3. ลอจิกการเล่นเสียงเตือนแบบออฟไลน์ (ไหลลื่น ไม่กระตุก)
            if closest_object:
                current_time = time.time()
                # หน่วงเวลาเช็ก 2.5 วินาทีต่อครั้ง เพื่อให้ประโยคเสียงพูดจบคำอย่างสวยงาม
                if current_time - st.session_state.last_alert_time > 2.5:
                    status_placeholder.markdown(f"### ⚠️ [เสียงเตือนทำงาน]: **Warning! {closest_object} is too close.**")
                    
                    # ยิงเสียงออฟไลน์ทันที
                    play_cached_sound(closest_object)
                    
                    st.session_state.last_alert_time = current_time
            else:
                status_placeholder.markdown("### 🟢 สถานะปัจจุบัน: เส้นทางด้านหน้าปลอดภัย")

            FRAME_WINDOW_BLIND.image(frame_rgb)
            
        cap.release()
        try:
            pygame.mixer.quit()
        except:
            pass
    else:
        st.write("กล้องปิดอยู่... กรุณากด Start Camera เพื่อเริ่มทำงาน")