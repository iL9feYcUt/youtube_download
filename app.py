import streamlit as st
import yt_dlp
import os
import time

# --- ページ設定 ---
st.set_page_config(page_title="YT Cutter & Preview", layout="centered")

st.title("✂️ YouTube Cutter & Preview")
st.markdown("""
以下の手順で操作してください：
1. URLと時間を指定
2. **「カットしてプレビューを作成」**をクリック（サーバーで処理されます）
3. プレビューを確認して**ダウンロード**
""")

# --- ユーティリティ関数 ---
def parse_time(time_str):
    """MM:SS または HH:MM:SS を秒数に変換"""
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return int(time_str)
    except:
        return 0

def cleanup_old_files():
    """古い一時ファイルを削除（サーバー容量節約のため）"""
    for f in os.listdir('.'):
        if f.startswith("temp_") and (f.endswith(".mp4") or f.endswith(".mp3") or f.endswith(".wav")):
            try:
                os.remove(f)
            except:
                pass

# --- UI入力エリア ---
url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

col1, col2, col3 = st.columns(3)
with col1:
    fmt = st.selectbox("保存形式", ["mp4", "mp3", "wav"])
with col2:
    start_time = st.text_input("開始 (MM:SS)", "00:00")
with col3:
    end_time = st.text_input("終了 (MM:SS)", "00:10")

# --- 処理実行ボタン ---
if st.button("カットしてプレビューを作成"):
    if not url:
        st.error("URLを入力してください。")
    else:
        # 古いファイルを掃除
        cleanup_old_files()
        
        start_sec = parse_time(start_time)
        end_sec = parse_time(end_time)

        if end_sec <= start_sec:
            st.error("終了時間は開始時間より後に設定してください。")
        else:
            with st.spinner('動画をダウンロード・加工中...（数秒〜数十秒かかります）'):
                try:
                    # ファイル名の定義（拡張子は後でyt-dlpが決めるが、ここでは指定）
                    timestamp = int(time.time())
                    filename_base = f"temp_{timestamp}"
                    
                    # yt-dlpオプション
                    ydl_opts = {
                        'outtmpl': f'{filename_base}.%(ext)s',
                        'download_ranges': lambda info, ydl: [{
                            'start_time': start_sec,
                            'end_time': end_sec
                        }],
                        'force_keyframes_at_cuts': True, # カット精度向上
                    }

                    # フォーマット別設定
                    if fmt == 'mp3':
                        ydl_opts.update({
                            'format': 'bestaudio/best',
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',
                            }],
                        })
                        expected_ext = 'mp3'
                    elif fmt == 'wav':
                        ydl_opts.update({
                            'format': 'bestaudio/best',
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'wav',
                            }],
                        })
                        expected_ext = 'wav'
                    else: # mp4
                        ydl_opts.update({
                            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                            'merge_output_format': 'mp4'
                        })
                        expected_ext = 'mp4'

                    # ダウンロード実行
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                    # 生成された特定ファイルを探す
                    target_file = f"{filename_base}.{expected_ext}"
                    
                    if os.path.exists(target_file):
                        st.success("作成完了！プレビューを確認してください。")
                        
                        # --- プレビュー表示 ---
                        st.markdown("### 🎬 プレビュー")
                        if fmt == 'mp4':
                            st.video(target_file)
                        else:
                            st.audio(target_file)

                        # --- ダウンロードボタン ---
                        st.markdown("---")
                        with open(target_file, "rb") as f:
                            st.download_button(
                                label=f"💾 {fmt.upper()}ファイルを保存する",
                                data=f,
                                file_name=f"cut_video.{expected_ext}",
                                mime="video/mp4" if fmt == 'mp4' else f"audio/{fmt}"
                            )
                    else:
                        st.error("ファイルの生成に失敗しました。")

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
