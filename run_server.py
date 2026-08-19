"""
Server & Cloudflare Tunnel Supervisor
- Ensures Streamlit is running on port 8501
- Automatically launches & monitors Cloudflare Tunnel
- Auto-recovers and reconnects if internet drops or Mac wakes up from sleep
- Displays live QR-friendly mobile URL
"""

import os
import sys
import time
import subprocess
import re
import signal

PYTHON_EXEC = "/opt/anaconda3/bin/python3"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_BIN = os.path.join(PROJECT_DIR, "bin", "cloudflared")
URL_FILE = os.path.join(PROJECT_DIR, "current_url.txt")

def start_streamlit():
    """Starts Streamlit in background if not already running."""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8501", timeout=1)
        print("✅ Streamlit server is already running on port 8501.")
        return None
    except Exception:
        print("🚀 Starting Streamlit server...")
        proc = subprocess.Popen(
            [PYTHON_EXEC, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        return proc

def run_tunnel_and_monitor():
    """Runs Cloudflare tunnel and auto-restarts if connection drops."""
    while True:
        print("\n🌐 Launching Cloudflare Tunnel...")
        tunnel_proc = subprocess.Popen(
            [CLOUDFLARED_BIN, "tunnel", "--url", "http://localhost:8501"],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        tunnel_url = None
        start_time = time.time()

        # Read output line by line to extract the trycloudflare URL
        for line in iter(tunnel_proc.stdout.readline, ''):
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group(0)
                with open(URL_FILE, "w", encoding="utf-8") as f:
                    f.write(tunnel_url)
                
                print("\n" + "=" * 60)
                print("🎉 ลิงก์สำหรับเปิดบนมือถือ (4G/5G/Wi-Fi พร้อมใช้งานแล้ว):")
                print(f"👉 {tunnel_url}")
                print("=" * 60)
                print("💡 กด Add to Home Screen บนมือถือเพื่อใช้เป็นแอปได้เลย")
                print("🔄 ระบบกำลังเฝ้าระวัง: หากเน็ตหลุดจะต่อใหม่อัตโนมัติ...\n")
                break

            if time.time() - start_time > 30:
                print("⚠️ Tunnel setup timed out, retrying...")
                break

        # Health check loop
        while True:
            time.sleep(15)
            # Check if tunnel process is still alive
            if tunnel_proc.poll() is not None:
                print("⚠️ Tunnel disconnected! Reconnecting...")
                break
            
            # Check if URL is responsive
            if tunnel_url:
                import urllib.request
                try:
                    req = urllib.request.Request(tunnel_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status != 200:
                            print(f"⚠️ Health check returned {response.status}, refreshing tunnel...")
                            break
                except Exception as e:
                    print(f"⚠️ Connection lost ({e}). Restarting tunnel in 3s...")
                    break

        try:
            tunnel_proc.terminate()
            tunnel_proc.wait(timeout=3)
        except Exception:
            tunnel_proc.kill()

        time.sleep(3)

if __name__ == "__main__":
    st_proc = start_streamlit()
    try:
        run_tunnel_and_monitor()
    except KeyboardInterrupt:
        print("\n👋 Stopping server and tunnel...")
        if st_proc:
            st_proc.terminate()
        sys.exit(0)
