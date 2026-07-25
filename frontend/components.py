"""
Reusable Streamlit UI pieces.

zoom_pan_viewer() renders a self-contained HTML/JS pan+zoom image viewer
via st.iframe - no third-party pip dependency, works with any
recent Streamlit version. Mouse wheel = zoom, click-drag = pan, double
click = reset.
"""
from typing import Optional
from urllib.parse import quote

import streamlit as st
"""
Reusable Streamlit UI pieces.

zoom_pan_viewer() renders a self-contained HTML/JS pan+zoom image viewer
via st.iframe - no third-party pip dependency, works with any
recent Streamlit version. Mouse wheel = zoom, click-drag = pan, double
click = reset.
"""
from typing import Optional
from urllib.parse import quote

import streamlit as st


def zoom_pan_viewer(image_b64: str, height: int = 520) -> None:
    html = f"""
    <div id="viewer-wrap" style="
        width:100%; height:{height}px; overflow:hidden; position:relative;
        background:#111; border-radius:8px; cursor:grab; touch-action:none;">
      <img id="viewer-img" src="data:image/png;base64,{image_b64}"
           style="position:absolute; top:0; left:0; transform-origin:0 0;
                  user-select:none; -webkit-user-drag:none;" draggable="false"/>
      <div style="position:absolute; bottom:8px; right:8px; z-index:2;
                  background:rgba(0,0,0,0.55); color:#fff; font:12px sans-serif;
                  padding:4px 8px; border-radius:6px;">
        scroll = zoom &nbsp;|&nbsp; drag = pan &nbsp;|&nbsp; dbl-click = reset
      </div>
    </div>
    <script>
      (function() {{
        const wrap = document.getElementById('viewer-wrap');
        const img = document.getElementById('viewer-img');
        let scale = 1, originX = 0, originY = 0;
        let isDragging = false, startX = 0, startY = 0;

        function applyTransform() {{
          img.style.transform = `translate(${{originX}}px, ${{originY}}px) scale(${{scale}})`;
        }}

        wrap.addEventListener('wheel', function(e) {{
          e.preventDefault();
          const rect = wrap.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const mouseY = e.clientY - rect.top;
          const prevScale = scale;
          const delta = e.deltaY < 0 ? 1.12 : 0.89;
          scale = Math.min(Math.max(scale * delta, 0.5), 8);
          originX = mouseX - ((mouseX - originX) / prevScale) * scale;
          originY = mouseY - ((mouseY - originY) / prevScale) * scale;
          applyTransform();
        }}, {{ passive: false }});

        wrap.addEventListener('mousedown', function(e) {{
          isDragging = true;
          wrap.style.cursor = 'grabbing';
          startX = e.clientX - originX;
          startY = e.clientY - originY;
        }});
        window.addEventListener('mouseup', function() {{
          isDragging = false;
          wrap.style.cursor = 'grab';
        }});
        window.addEventListener('mousemove', function(e) {{
          if (!isDragging) return;
          originX = e.clientX - startX;
          originY = e.clientY - startY;
          applyTransform();
        }});
        wrap.addEventListener('dblclick', function() {{
          scale = 1; originX = 0; originY = 0;
          applyTransform();
        }});

        wrap.addEventListener('touchstart', function(e) {{
          const t = e.touches[0];
          isDragging = true;
          startX = t.clientX - originX;
          startY = t.clientY - originY;
        }});
        wrap.addEventListener('touchmove', function(e) {{
          if (!isDragging) return;
          const t = e.touches[0];
          originX = t.clientX - startX;
          originY = t.clientY - startY;
          applyTransform();
        }});
        wrap.addEventListener('touchend', function() {{ isDragging = false; }});
      }})();
    </script>
    """
    st.iframe(
        src=f"data:text/html;charset=utf-8,{quote(html)}",
        width="stretch",
        height=height + 10,
    )


def render_image_grid(images: list[dict], key_prefix: str, columns: int = 4) -> Optional[str]:
    """
    Renders thumbnails in a grid. Returns the image_id whose "Preview"
    button was just clicked (or None). `images` items need
    {"image_id", "filename", "b64"}.
    """
    clicked_id = None
    cols = st.columns(columns)
    for idx, img in enumerate(images):
        col = cols[idx % columns]
        with col:
            st.image(
                f"data:image/png;base64,{img['b64']}",
                caption=img["filename"],
                width="stretch",
            )
            if st.button("🔍 Preview", key=f"{key_prefix}_preview_{img['image_id']}"):
                clicked_id = img["image_id"]
    return clicked_id

def zoom_pan_viewer(image_b64: str, height: int = 520) -> None:
    html = f"""
    <div id="viewer-wrap" style="
        width:100%; height:{height}px; overflow:hidden; position:relative;
        background:#111; border-radius:8px; cursor:grab; touch-action:none;">
      <img id="viewer-img" src="data:image/png;base64,{image_b64}"
           style="position:absolute; top:0; left:0; transform-origin:0 0;
                  user-select:none; -webkit-user-drag:none;" draggable="false"/>
      <div style="position:absolute; bottom:8px; right:8px; z-index:2;
                  background:rgba(0,0,0,0.55); color:#fff; font:12px sans-serif;
                  padding:4px 8px; border-radius:6px;">
        scroll = zoom &nbsp;|&nbsp; drag = pan &nbsp;|&nbsp; dbl-click = reset
      </div>
    </div>
    <script>
      (function() {{
        const wrap = document.getElementById('viewer-wrap');
        const img = document.getElementById('viewer-img');
        let scale = 1, originX = 0, originY = 0;
        let isDragging = false, startX = 0, startY = 0;

        function applyTransform() {{
          img.style.transform = `translate(${{originX}}px, ${{originY}}px) scale(${{scale}})`;
        }}

        wrap.addEventListener('wheel', function(e) {{
          e.preventDefault();
          const rect = wrap.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const mouseY = e.clientY - rect.top;
          const prevScale = scale;
          const delta = e.deltaY < 0 ? 1.12 : 0.89;
          scale = Math.min(Math.max(scale * delta, 0.5), 8);
          originX = mouseX - ((mouseX - originX) / prevScale) * scale;
          originY = mouseY - ((mouseY - originY) / prevScale) * scale;
          applyTransform();
        }}, {{ passive: false }});

        wrap.addEventListener('mousedown', function(e) {{
          isDragging = true;
          wrap.style.cursor = 'grabbing';
          startX = e.clientX - originX;
          startY = e.clientY - originY;
        }});
        window.addEventListener('mouseup', function() {{
          isDragging = false;
          wrap.style.cursor = 'grab';
        }});
        window.addEventListener('mousemove', function(e) {{
          if (!isDragging) return;
          originX = e.clientX - startX;
          originY = e.clientY - startY;
          applyTransform();
        }});
        wrap.addEventListener('dblclick', function() {{
          scale = 1; originX = 0; originY = 0;
          applyTransform();
        }});

        // Touch support (pinch not included - single-finger pan only)
        wrap.addEventListener('touchstart', function(e) {{
          const t = e.touches[0];
          isDragging = true;
          startX = t.clientX - originX;
          startY = t.clientY - originY;
        }});
        wrap.addEventListener('touchmove', function(e) {{
          if (!isDragging) return;
          const t = e.touches[0];
          originX = t.clientX - startX;
          originY = t.clientY - startY;
          applyTransform();
        }});
        wrap.addEventListener('touchend', function() {{ isDragging = false; }});
      }})();
    </script>
    """
    st.iframe(
        src=f"data:text/html;charset=utf-8,{quote(html)}",
        width="stretch",
        height=height + 10,
    )


def render_image_grid(images: list[dict], key_prefix: str, columns: int = 4) -> Optional[str]:
    """
    Renders thumbnails in a grid. Returns the image_id whose "Preview"
    button was just clicked (or None). `images` items need
    {"image_id", "filename", "b64"}.
    """
    clicked_id = None
    cols = st.columns(columns)
    for idx, img in enumerate(images):
        col = cols[idx % columns]
        with col:
            st.image(
                f"data:image/png;base64,{img['b64']}",
                caption=img["filename"],
                width="stretch",
            )
            if st.button("🔍 Preview", key=f"{key_prefix}_preview_{img['image_id']}"):
                clicked_id = img["image_id"]
    return clicked_id

