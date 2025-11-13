# getnodes_modified.py

import sys
import re
import os
import gdown     # 用于下载 Google Drive
import yt_dlp    # 用于下载 YouTube
from googleapiclient.discovery import build
from datetime import datetime

# --- 变量配置 ---

# 1. API 密钥将从 GitHub Secrets (环境变量) 读取
API_KEY = os.environ.get("YOUTUBE_API_KEY")

# 2. 固定的 Video ID
VIDEO_ID = "FNs1N31XZtE" 

# 3. 创建一个输出目录
OUTPUT_DIR = "daily_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 4. 获取今天日期 (YYYY-MM-DD 格式)
TODAY_DATE = datetime.now().strftime('%Y-%m-%d')

# 5. 动态生成文件名
#    (!!) 文件名现在包含日期并保存在 OUTPUT_DIR 中
OUTPUT_LINK_FILE  = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-subscription_info.txt")
DOWNLOAD_FILENAME = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-13148866.zip")
AUDIO_FILENAME    = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-video_audio.mp3")

# -------------------------

def main():
    
    # 检查 API 密钥是否存在
    if not API_KEY:
        print("❌ 严重错误：未能在环境变量中找到 YOUTUBE_API_KEY。")
        print("请在 GitHub 仓库的 Settings > Secrets 中进行设置。")
        sys.exit(1) # 退出脚本，防止后续出错

    video_url = f"https://www.youtube.com/watch?v={VIDEO_ID}"
    
    try:
        # --- 步骤 1: 获取介绍栏，提取 GDrive 链接 ---
        print("--- 步骤 1: 获取 YouTube 视频介绍 ---")
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        video_response = youtube.videos().list(part='snippet', id=VIDEO_ID).execute()
        if not video_response.get('items'):
            print("错误：无法获取 Video ID 信息。")
            return
        description = video_response['items'][0]['snippet']['description']
        print("成功获取介绍栏。")

        pattern = r'(https?://drive\.google\.com[^\s]+)'
        matches = re.findall(pattern, description)
        
        found_gdrive_link = "" # 谷歌网盘链接
        
        if not matches:
            print(f"⚠️ 未能在介绍栏中找到 Google Drive 链接。")
        else:
            found_gdrive_link = matches[0]
            print(f"🎉 成功提取到 Google Drive 链接：\n{found_gdrive_link}")

        # --- 步骤 2: 保存所有链接到文件 ---
        print(f"\n--- 步骤 2: 保存所有链接到 {OUTPUT_LINK_FILE} ---")
        try:
            with open(OUTPUT_LINK_FILE, 'w', encoding='utf-8') as f:
                f.write("[Google Drive Link]\n")
                if found_gdrive_link:
                    f.write(found_gdrive_link + "\n")
                else:
                    f.write("(未在介绍栏找到)\n")
                
                f.write("\n[YouTube Video Link (for manual audio download)]\n")
                f.write(video_url + "\n")
            print(f"✅ 成功保存所有链接。")
        except Exception as e:
            print(f"⚠️ 无法写入链接文件: {e}")

        # --- 步骤 3: 下载 Google Drive 的 ZIP 文件 ---
        if found_gdrive_link:
            print(f"\n--- 步骤 3: 下载 Google Drive 文件 ---")
            if os.path.exists(DOWNLOAD_FILENAME):
                os.remove(DOWNLOAD_FILENAME)
                print(f"已删除旧的 {DOWNLOAD_FILENAME}")
            
            try:
                gdown.download(found_gdrive_link, DOWNLOAD_FILENAME, quiet=False, fuzzy=True)
                print(f"✅ 成功下载文件: {DOWNLOAD_FILENAME}")
            except Exception as e:
                print(f"❌ 下载 Google Drive 文件失败: {e}")
        else:
            print(f"\n--- 步骤 3: 跳过下载 (未找到 Google Drive 链接) ---")


        # --- 步骤 4: 下载 YouTube 视频音频 ---
        print(f"\n--- 步骤 4: 下载 YouTube 视频音频 ---")
        if os.path.exists(AUDIO_FILENAME):
            os.remove(AUDIO_FILENAME)
            print(f"已删除旧的 {AUDIO_FILENAME}")
        
        # (!!) 注意：outtmpl 现在是一个完整的路径
        ydl_opts = {
            'format': 'bestaudio/best', 
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': AUDIO_FILENAME,
            'quiet': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"✅ 成功下载音频: {AUDIO_FILENAME}")
            print("\n--- 任务完成 ---")
        except Exception as e:
            print(f"❌ 下载音频失败 (错误: {e})")
            print(f"--- 任务部分完成 ---")

    except Exception as e:
        print(f"\n发生严重错误：{e}")
        print("请检查 API_KEY, VIDEO_ID, FFmpeg 安装, 以及网络连接。")

if __name__ == "__main__":
    main()
