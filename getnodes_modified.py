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
API_KEY = os.environ.get("YOUTUBE_API_KEY")
VIDEO_ID = os.environ.get("VIDEO_ID")
ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")

# 1. 临时下载目录
OUTPUT_DIR = "temp_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. (!!) 最终文件名不再固定，而是动态生成

# 3. 临时文件名
TODAY_DATE = datetime.now().strftime('%Y-%m-%d')
OUTPUT_LINK_FILE  = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-subscription_info.txt")
DOWNLOAD_FILENAME = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-13148866.zip")
AUDIO_FILENAME    = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-video_audio.mp3")
# -------------------------

def main():
    # 检查所有 Secrets
    if not all([API_KEY, VIDEO_ID, ZIP_PASSWORD]):
        print("❌ 严重错误：YOUTUBE_API_KEY, VIDEO_ID, 或 ZIP_PASSWORD 未设置。")
        print("请在 GitHub 仓库的 Settings > Secrets 中检查它们。")
        sys.exit(1)

    print(f"--- 正在处理 Video ID: {VIDEO_ID} ---")
    video_url = f"https://www.youtube.com/watch?v={VIDEO_ID}"
    
    try:
        # --- 步骤 1 & 2: 获取并保存链接 (不变) ---
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
        extracted_files_list = [] # 用来存放所有成功提取的文件名
        if found_gdrive_link:
            print(f"\n--- 步骤 3: 下载 Google Drive 文件 ---")
            try:
                gdown.download(found_gdrive_link, DOWNLOAD_FILENAME, quiet=False, fuzzy=True)
                print(f"✅ 成功下载文件: {DOWNLOAD_FILENAME}")

                # (!!) --- 步骤 4: (核心修改) 遍历、解压、提取所有匹配文件 ---
                print(f"\n--- 步骤 4: 扫描 {DOWNLOAD_FILENAME} 内的所有目标文件 ---")
                
                pwd_bytes = ZIP_PASSWORD.encode('utf-8')

                with zipfile.ZipFile(DOWNLOAD_FILENAME, 'r') as zip_ref:
                    # 遍历 zip 包中的每一个文件
                    for file_info in zip_ref.infolist():
                        # 如果是文件夹，则跳过
                        if file_info.is_dir():
                            continue
                        
                        # (!!) 获取文件名 (e.g., "v2ray+Karing+IOS火箭复制导入.txt")
                        base_filename = os.path.basename(file_info.filename)
                        
                        # (!!) 检查文件名是否以 '复制导入.txt' 结尾
                        if base_filename.endswith('复制导入.txt'):
                            print(f"  -> 找到目标文件: {file_info.filename}")
                            
                            try:
                                # (!!) 新的 repo 根目录文件名就是它本身
                                repo_filename = base_filename
                                
                                # 读取加密文件内容
                                with zip_ref.open(file_info, pwd=pwd_bytes) as f:
                                    content = io.TextIOWrapper(f, encoding='utf-8').read()
                                
                                # (!!) 将内容写入到【仓库根目录】
                                with open(repo_filename, 'w', encoding='utf-8') as final_file:
                                    final_file.write(content)
                                
                                print(f"  ✅ 成功提取并保存到 ./{repo_filename}")
                                extracted_files_list.append(repo_filename)
                                
                            except RuntimeError as e:
                                if 'password' in str(e).lower():
                                    print(f"  ❌ 密码错误 (文件: {base_filename})")
                                else:
                                    print(f"  ❌ 运行时错误 (文件: {base_filename}): {e}")
                            except Exception as e:
                                print(f"  ❌ 提取时发生未知错误 (文件: {base_filename}): {e}")

            except zipfile.BadZipFile:
                 print(f"❌ 下载的文件不是一个有效的 ZIP 文件。")
            except Exception as e:
                print(f"❌ 下载或解压 Google Drive 文件失败: {e}")
        else:
            print(f"\n--- 步骤 3/4: 跳过下载和提取 (未找到链接) ---")

        # --- 步骤 5: 下载音频 (不变, 仍然是临时的) ---
        print(f"\n--- 步骤 5: 下载 YouTube 视频音频 (临时) ---")
        try:
            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': AUDIO_FILENAME}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"✅ 成功下载临时音频")
        except Exception as e:
            print(f"⚠️ 下载音频失败: {e}")
        
        # --- 总结 ---
        if not extracted_files_list:
            print(f"\n--- 任务完成 ---")
            print(f"⚠️ 未能在 {DOWNLOAD_FILENAME} 中找到任何匹配 '...复制导入.txt' 的文件。")
        else:
            print(f"\n--- 任务完成 ---")
            print(f"成功提取并保存了 {len(extracted_files_list)} 个文件:")
            for f in extracted_files_list:
                print(f"  - {f}")

    except Exception as e:
        print(f"\n发生严重错误：{e}")

if __name__ == "__main__":
    main()
