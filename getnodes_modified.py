import sys
import re
import os
import gdown     
import yt_dlp    
from googleapiclient.discovery import build
from datetime import datetime
import zipfile 
import io      

# --- 变量配置 ---
# (!!) 所有动态配置都从环境变量中读取
API_KEY = os.environ.get("YOUTUBE_API_KEY")
VIDEO_ID = os.environ.get("VIDEO_ID")
ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")

# 1. 临时下载目录
OUTPUT_DIR = "temp_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. 最终在【仓库根目录】生成的文件名
FINAL_CONTENT_FILE = "subscription_content.txt"

# 3. 临时文件名
TODAY_DATE = datetime.now().strftime('%Y-%m-%d')
OUTPUT_LINK_FILE  = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-subscription_info.txt")
DOWNLOAD_FILENAME = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-13148866.zip")
AUDIO_FILENAME    = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-video_audio.mp3")
# -------------------------

def main():
    # (!!) 检查所有 Secrets 是否都已设置
    if not API_KEY:
        print("❌ 严重错误：未能在环境变量中找到 YOUTUBE_API_KEY。")
        sys.exit(1)
    if not VIDEO_ID:
        print("❌ 严重错误：未能在环境变量中找到 VIDEO_ID。")
        print("请在 GitHub 仓库的 Settings > Secrets 中设置它。")
        sys.exit(1)
    if not ZIP_PASSWORD:
        print("❌ 严重错误：未能在环境变量中找到 ZIP_PASSWORD。")
        print("请在 GitHub 仓库的 Settings > Secrets 中设置它。")
        sys.exit(1)

    print(f"--- 正在处理 Video ID: {VIDEO_ID} ---")
    video_url = f"https://www.youtube.com/watch?v={VIDEO_ID}"
    
    try:
        # --- 步骤 1 & 2: 获取并保存链接 (与之前相同) ---
        print("--- 步骤 1 & 2: 获取并保存链接 ---")
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        video_response = youtube.videos().list(part='snippet', id=VIDEO_ID).execute()
        if not video_response.get('items'):
            print("错误：无法获取 Video ID 信息。")
            return
        description = video_response['items'][0]['snippet']['description']
        pattern = r'(https?://drive\.google\.com[^\s]+)'
        matches = re.findall(pattern, description)
        found_gdrive_link = ""
        
        if matches:
            found_gdrive_link = matches[0]
            print(f"🎉 成功提取到 Google Drive 链接")
        else:
            print(f"⚠️ 未能在介绍栏中找到 Google Drive 链接。")
        
        with open(OUTPUT_LINK_FILE, 'w', encoding='utf-8') as f:
            f.write(f"[GDrive] {found_gdrive_link}\n[YouTube] {video_url}\n")
        print(f"✅ 成功保存链接到 {OUTPUT_LINK_FILE}")

        # --- 步骤 3: 下载 Google Drive 的 ZIP 文件 ---
        zip_content_extracted = False
        if found_gdrive_link:
            print(f"\n--- 步骤 3: 下载 Google Drive 文件 ---")
            try:
                gdown.download(found_gdrive_link, DOWNLOAD_FILENAME, quiet=False, fuzzy=True)
                print(f"✅ 成功下载文件: {DOWNLOAD_FILENAME}")

                # (!!) --- 步骤 4: 使用密码解压并提取文本 ---
                print(f"\n--- 步骤 4: 提取 {DOWNLOAD_FILENAME} 内的文本 ---")
                
                # (!!) 将密码字符串转换为 bytes
                pwd_bytes = ZIP_PASSWORD.encode('utf-8')

                with zipfile.ZipFile(DOWNLOAD_FILENAME, 'r') as zip_ref:
                    target_file_name = None
                    for name in zip_ref.namelist():
                        if name.endswith('.txt'):
                            target_file_name = name
                            print(f"在 ZIP 中找到目标文件: {target_file_name}")
                            break
                    
                    if target_file_name:
                        # (!!) 使用 pwd 参数打开加密文件
                        with zip_ref.open(target_file_name, pwd=pwd_bytes) as f:
                            content = io.TextIOWrapper(f, encoding='utf-8').read()
                        
                        with open(FINAL_CONTENT_FILE, 'w', encoding='utf-8') as final_file:
                            final_file.write(content)
                        
                        print(f"✅ 成功提取加密内容并保存到 {FINAL_CONTENT_FILE}")
                        zip_content_extracted = True
                    else:
                        print(f"⚠️ 未能在 {DOWNLOAD_FILENAME} 中找到任何 .txt 文件。")

            except zipfile.BadZipFile:
                 print(f"❌ 下载的文件不是一个有效的 ZIP 文件。")
            except RuntimeError as e:
                # (!!) 捕获密码错误的异常
                if 'password' in str(e).lower():
                    print(f"❌ 解压失败：密码错误！")
                    print("请检查 GitHub Secrets 中的 ZIP_PASSWORD 是否为最新。")
                else:
                    print(f"❌ 解压时发生运行时错误: {e}")
            except Exception as e:
                print(f"❌ 下载或解压 Google Drive 文件失败: {e}")
        else:
            print(f"\n--- 步骤 3/4: 跳过下载和提取 (未找到链接) ---")

        # --- 步骤 5: 下载音频 (仍然是临时的) ---
        print(f"\n--- 步骤 5: 下载 YouTube 视频音频 (临时) ---")
        try:
            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': AUDIO_FILENAME}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"✅ 成功下载临时音频")
        except Exception as e:
            print(f"⚠️ 下载音频失败: {e}")
        
        if zip_content_extracted:
            print(f"\n--- 任务完成 ---")
        else:
             print(f"\n--- 任务部分完成 ---")

    except Exception as e:
        print(f"\n发生严重错误：{e}")

if __name__ == "__main__":
    main()
