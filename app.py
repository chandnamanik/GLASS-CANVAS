import streamlit as st
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Glass Canvas | AR Studio",
    page_icon="🎨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE MANAGEMENT ---
# Initialize session variables to track steps and image data
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'input_image' not in st.session_state:
    st.session_state.input_image = None
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'rotation' not in st.session_state:
    st.session_state.rotation = 0

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

def reset_app():
    st.session_state.step = 1
    st.session_state.input_image = None
    st.session_state.processed_image = None
    st.session_state.rotation = 0

# --- 3. CUSTOM CSS & ARTISTIC STYLING ---
st.markdown("""
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=Reenie+Beanie&display=swap');
        
        /* Main Background */
        .stApp {
            /* Deep Artistic Studio Background */
            background-color: #0f0c29;
            background-image: 
                radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
                radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
            background-attachment: fixed;
            font-family: 'Space Grotesk', sans-serif;
            color: #e0e0e0;
        }

        /* Titles & Headers */
        h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            color: white;
            text-align: center;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(139, 92, 246, 0.5);
            margin-bottom: 0.5rem;
        }
        .artistic-sub {
            font-family: 'Reenie Beanie', cursive;
            color: #a78bfa;
            font-size: 2rem;
            text-align: center;
            transform: rotate(-2deg);
            margin-bottom: 2rem;
        }

        /* Glass Cards */
        .glass-panel {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }

        /* Custom Buttons */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            font-weight: 600;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            padding: 0.6rem 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }
        /* Secondary Button Style (for 'Back') */
        div[data-testid="stHorizontalBlock"] > div:first-child button {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.2);
            color: #cbd5e1;
        }

        /* Progress Bar Container */
        .progress-container {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            position: relative;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            z-index: 2;
            transition: all 0.5s ease;
        }
        .step-active {
            background: #8b5cf6;
            box-shadow: 0 0 15px #8b5cf6;
            transform: scale(1.2);
        }
        .step-line {
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 2px;
            background: rgba(255,255,255,0.1);
            z-index: 1;
            transform: translateY(-50%);
        }
        
        /* Remove extra padding */
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def get_image_base64(image_array):
    if len(image_array.shape) > 2:
        img_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    else:
        img_rgb = image_array
    pil_img = Image.fromarray(img_rgb)
    buff = BytesIO()
    pil_img.save(buff, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buff.getvalue()).decode()}"

def rotate_image(image, k):
    if k % 4 == 0: return image
    return np.rot90(image, k=k)

def crop_image(image, left_p, right_p, top_p, bottom_p):
    h, w = image.shape[:2]
    x_start = int(w * (left_p / 100))
    x_end = int(w * (1 - right_p / 100))
    y_start = int(h * (top_p / 100))
    y_end = int(h * (1 - bottom_p / 100))
    if x_start >= x_end or y_start >= y_end: return image
    return image[y_start:y_end, x_start:x_end]

def adjust_brightness_contrast(image, alpha, beta):
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

def draw_grid(image, grid_size=3):
    h, w = image.shape[:2]
    color = (100, 255, 100) if len(image.shape) > 2 else 180
    
    # Create a copy to draw lines on
    img_grid = image.copy()
    
    for i in range(1, grid_size):
        x = int(w * i / grid_size)
        cv2.line(img_grid, (x, 0), (x, h), color, 1)
    for i in range(1, grid_size):
        y = int(h * i / grid_size)
        cv2.line(img_grid, (0, y), (w, y), color, 1)
    return img_grid

def apply_processing(pil_image, rotation, crop_vals, mode, t1, t2, brightness, contrast, show_grid):
    # 1. Convert
    img_array = np.array(pil_image.convert('RGB'))
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # 2. Geometry
    img_cv = rotate_image(img_cv, rotation)
    img_cv = crop_image(img_cv, *crop_vals)
    
    # 3. Enhance
    img_cv = adjust_brightness_contrast(img_cv, contrast, brightness)

    # 4. Filter Logic
    final_img = img_cv
    if mode == "Grayscale":
        final_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    elif mode == "Magic Outline":
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, t1, t2)
        final_img = cv2.bitwise_not(edges)
    elif mode == "Pencil Sketch":
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        inv = cv2.bitwise_not(gray)
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        final_img = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
    elif mode == "Crayon Drawing":
        final_img = cv2.bilateralFilter(img_cv, 9, 75, 75)
        gray = cv2.cvtColor(final_img, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        final_img = cv2.bitwise_and(final_img, final_img, mask=edges)
    elif mode == "Abstract":
        final_img = cv2.pyrMeanShiftFiltering(img_cv, 21, 51)
    elif mode == "Negative":
        final_img = cv2.bitwise_not(img_cv)
    elif mode == "Sepia":
        kernel = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
        final_img = cv2.transform(img_cv, kernel)
        final_img = np.clip(final_img, 0, 255).astype(np.uint8)

    # 5. Grid
    if show_grid:
        final_img = draw_grid(final_img)

    return final_img


# --- 5. MAIN UI LAYOUT ---

# Header
st.markdown("<h1>GLASS CANVAS</h1>", unsafe_allow_html=True)
st.markdown("<div class='artistic-sub'>the digital camera lucida</div>", unsafe_allow_html=True)

# Progress Bar
s1 = "step-active" if st.session_state.step >= 1 else ""
s2 = "step-active" if st.session_state.step >= 2 else ""
s3 = "step-active" if st.session_state.step >= 3 else ""

st.markdown(f"""
    <div class="progress-container">
        <div class="step-line"></div>
        <div class="step-dot {s1}">1</div>
        <div class="step-dot {s2}">2</div>
        <div class="step-dot {s3}">3</div>
    </div>
""", unsafe_allow_html=True)

# --- STEP 1: UPLOAD ---
if st.session_state.step == 1:
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.markdown("### 📤 Upload Reference", unsafe_allow_html=True)
    st.markdown("Choose the image you want to trace. High contrast images work best.")
    
    uploaded_file = st.file_uploader("", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.session_state.input_image = image  # Save to session state
        st.image(image, caption="Preview", use_container_width=True)
        
        st.write("") # Spacer
        if st.button("Start Designing ➔"):
            next_step()
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)


# --- STEP 2: EDITING STUDIO ---
elif st.session_state.step == 2:
    if st.session_state.input_image is None:
        st.error("No image found. Please go back.")
        if st.button("Back"): reset_app()
    else:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.markdown("### 🎨 Image Studio", unsafe_allow_html=True)
        
        # Split into tabs for cleaner UI
        tab_geo, tab_art = st.tabs(["📐 Geometry", "✨ Artistic Filters"])
        
        with tab_geo:
            c_rot1, c_rot2 = st.columns(2)
            if c_rot1.button("↺ Rotate Left"): st.session_state.rotation = (st.session_state.rotation + 1) % 4
            if c_rot2.button("↻ Rotate Right"): st.session_state.rotation = (st.session_state.rotation - 1) % 4
            
            st.write("**Crop Image (%)**")
            cr1, cr2 = st.columns(2)
            crop_top = cr1.slider("Top", 0, 50, 0)
            crop_bottom = cr2.slider("Bottom", 0, 50, 0)
            cr3, cr4 = st.columns(2)
            crop_left = cr3.slider("Left", 0, 50, 0)
            crop_right = cr4.slider("Right", 0, 50, 0)

        with tab_art:
            mode = st.selectbox("Style", ["Original", "Grayscale", "Magic Outline", "Pencil Sketch", "Crayon Drawing", "Abstract", "Sepia", "Negative"])
            
            ac1, ac2 = st.columns(2)
            brightness = ac1.slider("Brightness", -100, 100, 0)
            contrast = ac2.slider("Contrast", 0.5, 3.0, 1.0, 0.1)
            
            t1, t2 = 100, 200
            if mode == "Magic Outline":
                st.info("Adjust edge sensitivity")
                t1 = st.slider("Min Threshold", 0, 500, 50)
                t2 = st.slider("Max Threshold", 0, 500, 150)
                
            show_grid = st.checkbox("Show Grid Lines", value=False)

        # Process the image based on all inputs
        processed = apply_processing(
            st.session_state.input_image,
            st.session_state.rotation,
            (crop_left, crop_right, crop_top, crop_bottom),
            mode, t1, t2, brightness, contrast, show_grid
        )
        
        # Save processed state for next step
        st.session_state.processed_image = processed

        st.markdown("---")
        # Display Preview
        if len(processed.shape) > 2:
            st.image(processed, channels="BGR", caption="Final Look", use_container_width=True)
        else:
            st.image(processed, caption="Final Look", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Navigation
        c_back, c_next = st.columns([1, 2])
        with c_back:
            if st.button("⬅ Back"):
                prev_step()
                st.rerun()
        with c_next:
            if st.button("Enter AR Tracing Mode ➔"):
                next_step()
                st.rerun()


# --- STEP 3: AR TRACING ---
elif st.session_state.step == 3:
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.markdown("### 📱 AR Tracing Surface", unsafe_allow_html=True)
    
    if st.session_state.processed_image is not None:
        img_b64 = get_image_base64(st.session_state.processed_image)
        
        # Instructions
        st.info("💡 Position your phone over paper. Lock the image. Trace away!")

        # HTML/JS Component
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; background: #000; font-family: 'Space Grotesk', sans-serif; overflow: hidden; }}
            .container {{ position: relative; width: 100%; height: 600px; border-radius: 12px; border: 2px solid #6366f1; overflow: hidden; background: #000; }}
            
            .fullscreen {{
                position: fixed !important; top: 0 !important; left: 0 !important;
                width: 100vw !important; height: 100vh !important;
                z-index: 9999 !important; border-radius: 0 !important; border: none !important;
            }}

            video {{ width: 100%; height: 100%; object-fit: cover; }}
            #overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; display: flex; justify-content: center; align-items: center; }}
            #trace-img {{ width: 80%; opacity: 0.5; transition: transform 0.1s; }}
            
            .controls {{ 
                position: absolute; bottom: 0; left: 0; right: 0;
                background: rgba(0,0,0,0.8); backdrop-filter: blur(8px);
                padding: 15px; border-top: 1px solid #444; color: white; pointer-events: auto;
                display: flex; flex-direction: column; gap: 10px;
            }}
            
            .row {{ display: flex; gap: 10px; justify-content: space-between; }}
            
            button {{ 
                flex: 1; padding: 12px; border: none; border-radius: 8px; 
                font-weight: bold; cursor: pointer; color: white; font-size: 13px;
                background: #334155; transition: 0.2s; white-space: nowrap;
            }}
            button:active {{ transform: scale(0.95); }}
            
            .btn-lock {{ background: #4f46e5; }}
            .btn-torch {{ background: #f59e0b; color: black; }}
            .btn-rec {{ background: #ef4444; }}
            .btn-rec.recording {{ background: #fff; color: #ef4444; animation: pulse 1s infinite; }}
            
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }}
                70% {{ box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }}
            }}
            
            input[type=range] {{ width: 100%; accent-color: #8b5cf6; margin: 0; }}
            label {{ font-size: 11px; color: #cbd5e1; display: block; margin-bottom: 4px;}}
        </style>
        </head>
        <body>
        <div id="app-container" class="container">
            <video id="video" autoplay playsinline></video>
            <div id="overlay"><img id="trace-img" src="{img_b64}"></div>
            
            <div class="controls">
                <div class="row">
                    <div style="flex:1">
                        <label>Opacity</label>
                        <input type="range" min="0" max="100" value="50" oninput="updateStyle('opacity', this.value/100)">
                    </div>
                    <div style="flex:1">
                        <label>Size</label>
                        <input type="range" min="10" max="300" value="80" oninput="updateStyle('width', this.value+'%')">
                    </div>
                </div>
                
                <div class="row">
                    <button class="btn-flip" onclick="flip('h')">↔ Flip H</button>
                    <button class="btn-flip" onclick="flip('v')">↕ Flip V</button>
                    <button class="btn-max" onclick="toggleFullScreen()">⛶ Full</button>
                </div>
                
                <div class="row">
                    <button class="btn-lock" onclick="toggleLock()">🔒 Lock Image</button>
                    <button class="btn-torch" onclick="toggleTorch()">🔦 Light</button>
                    <button class="btn-rec" onclick="toggleRecord()">🔴 Rec</button>
                </div>
            </div>
        </div>
        <script>
            const container = document.getElementById('app-container');
            const video = document.getElementById('video');
            const img = document.getElementById('trace-img');
            let isLocked = false;
            let isFull = false;
            let stream = null;
            let scaleX = 1; 
            let scaleY = 1;
            
            // Camera
            navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'environment' }} }}).then(s => {{
                stream = s;
                video.srcObject = s;
            }});

            function updateStyle(prop, val) {{
                img.style[prop] = val;
            }}

            function flip(axis) {{
                if(axis === 'h') scaleX *= -1;
                if(axis === 'v') scaleY *= -1;
                updateTransform();
            }}
            
            let startX, startY, currentX=0, currentY=0;
            
            function updateTransform() {{
                img.style.transform = `translate(${{currentX}}px, ${{currentY}}px) scale(${{scaleX}}, ${{scaleY}})`;
            }}

            // Touch logic
            document.addEventListener('touchstart', e => {{
                if(isLocked || e.target.closest('.controls')) return;
                startX = e.touches[0].clientX - currentX;
                startY = e.touches[0].clientY - currentY;
            }});
            
            document.addEventListener('touchmove', e => {{
                if(isLocked || e.target.closest('.controls')) return;
                e.preventDefault();
                currentX = e.touches[0].clientX - startX;
                currentY = e.touches[0].clientY - startY;
                updateTransform();
            }}, {{ passive: false }});

            function toggleLock() {{
                isLocked = !isLocked;
                const btn = document.querySelector('.btn-lock');
                btn.innerText = isLocked ? "🔓 Unlock" : "🔒 Lock Image";
                btn.style.background = isLocked ? "#ef4444" : "#4f46e5";
            }}

            function toggleTorch() {{
                const track = stream.getVideoTracks()[0];
                const cap = track.getCapabilities();
                if (cap.torch) {{
                    track.applyConstraints({{ advanced: [{{ torch: !track.getSettings().torch }}] }});
                }} else {{ alert("Flashlight not available on this device"); }}
            }}

            function toggleFullScreen() {{
                isFull = !isFull;
                if (isFull) {{
                    container.classList.add('fullscreen');
                }} else {{
                    container.classList.remove('fullscreen');
                }}
            }}
            
            // Recording
            let mediaRecorder;
            let recordedChunks = [];
            let isRecording = false;
            
            function toggleRecord() {{
                const btn = document.querySelector('.btn-rec');
                if (!isRecording) {{
                    let mimeType = 'video/webm'; 
                    let ext = 'webm';
                    if (MediaRecorder.isTypeSupported('video/mp4')) {{ mimeType = 'video/mp4'; ext = 'mp4'; }}
                    
                    recordedChunks = [];
                    mediaRecorder = new MediaRecorder(stream, {{ mimeType: mimeType }});
                    mediaRecorder.ondataavailable = event => {{ if (event.data.size > 0) recordedChunks.push(event.data); }};
                    mediaRecorder.onstop = () => {{
                        const blob = new Blob(recordedChunks, {{ type: mimeType }});
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = `glass_canvas.${{ext}}`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                    }};
                    mediaRecorder.start();
                    isRecording = true;
                    btn.innerText = "⬛ Stop";
                    btn.classList.add('recording');
                }} else {{
                    mediaRecorder.stop();
                    isRecording = false;
                    btn.innerText = "🔴 Rec";
                    btn.classList.remove('recording');
                }}
            }}
        </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=620)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("⬅ Edit Again"):
                prev_step()
                st.rerun()
                
    else:
        st.error("Session expired. Please restart.")
        if st.button("Restart"):
            reset_app()
            st.rerun()
