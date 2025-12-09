import sys
import re
import os
import gdown     
from googleapiclient.discovery import build
from datetime import datetime
import pyzipper
import io      

# --- (变量配置保持不变) ---
API_KEY = os.environ.get("YOUTUBE_API_KEY")
VIDEO_ID = os.environ.get("VIDEO_ID")
ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")

OUTPUT_DIR = "temp_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TODAY_DATE = datetime.now().strftime('%Y-%m-%d')
OUTPUT_LINK_FILE  = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-subscription_info.txt")
DOWNLOAD_FILENAME = os.path.join(OUTPUT_DIR, f"{TODAY_DATE}-13148866.zip")

def main():
    if not all([API_KEY, VIDEO_ID, ZIP_PASSWORD]):
        print("❌ 严重错误：YOUTUBE_API_KEY, VIDEO_ID, 或 ZIP_PASSWORD 未设置。")
        sys.exit(1)

    # (!!) --- [新增] 步骤 0: 清理旧的订阅文件 ---
    # 这一步是为了防止旧的 2.txt, 3.txt 残留
    print("--- 步骤 0: 清理旧的订阅文件 (1.txt, 2.txt...) ---")
    current_dir = os.getcwd() # 获取当前根目录
    deleted_count = 0
    
    for filename in os.listdir(current_dir):
        # 使用正则匹配：开头是数字 + 结尾是 .txt (例如 1.txt, 12.txt)
        if re.match(r'^\d+\.txt$', filename):
            try:
                os.remove(os.path.join(current_dir, filename))
                print(f"  🗑️ 已删除旧文件: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"  ⚠️ 删除失败 {filename}: {e}")
    
    if deleted_count == 0:
        print("  没有发现旧的数字命名文件，无需清理。")
    # (!!) ---------------------------------------

    print(f"\n--- 正在处理 Video ID: {VIDEO_ID} ---")
    video_url = f"https://www.youtube.com/watch?v={VIDEO_ID}"
    
    try:
        # --- (步骤 1 & 2 保持不变) ---
        print("--- 步骤 1 & 2: 获取 YouTube 链接 ---")
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        video_response = youtube.videos().list(part='snippet', id=VIDEO_ID).execute()
        
        if not video_response.get('items'):
            print(f"❌ 错误：无法获取 Video ID '{VIDEO_ID}' 的信息。")
            return
            
        description = video_response['items'][0]['snippet']['description']
        pattern = r'(https?://drive\.google\.com[^\s]+)'
        matches = re.findall(pattern, description)
        found_gdrive_link = ""
        
        if matches:
            found_gdrive_link = matches[0]
            print(f"🎉 成功提取到 Google Drive 链接")
        else:
            print(f"⚠️ 未能在视频介绍栏中找到 Google Drive 链接。")
        
        with open(OUTPUT_LINK_FILE, 'w', encoding='utf-8') as f:
            f.write(f"[Google Drive Link]\n{found_gdrive_link}\n")
            f.write(f"\n[YouTube Video Link]\n{video_url}\n")
        print(f"✅ 成功保存链接到 {OUTPUT_LINK_FILE}")

        # --- (步骤 3 & 4) ---
        extracted_files_list = [] 
        if found_gdrive_link:
            print(f"\n--- 步骤 3: 下载 Google Drive 文件 ---")
            try:
                gdown.download(found_gdrive_link, DOWNLOAD_FILENAME, quiet=False, fuzzy=True)
                print(f"✅ 成功下载文件: {DOWNLOAD_FILENAME}")

                print(f"\n--- 步骤 4: 扫描 {DOWNLOAD_FILENAME} 内的所有目标文件 ---")
                
                file_counter = 1

                with pyzipper.AESZipFile(DOWNLOAD_FILENAME, 'r') as zip_ref:
                    zip_ref.setpassword(ZIP_PASSWORD.encode('utf-8'))
                    
                    for file_info in zip_ref.infolist():
                        if file_info.is_dir():
                            continue
                        
                        try:
                            fixed_filename = file_info.filename.encode('cp437').decode('gbk')
                        except:
                            fixed_filename = file_info.filename
                        
                        base_filename = os.path.basename(fixed_filename)
                        
                        target_suffix = '复制导入.txt'
                        if base_filename.strip().lower().endswith(target_suffix.lower()):
                            print(f"  -> 匹配成功: {fixed_filename}")
                            
                            try:
                                repo_filename = f"{file_counter}.txt"
                                
                                with zip_ref.open(file_info) as f:
                                    content = io.TextIOWrapper(f, encoding='utf-8').read()
                                
                                with open(repo_filename, 'w', encoding='utf-8') as final_file:
                                    final_file.write(content)
                                
                                print(f"  ✅ 成功提取并保存到 ./{repo_filename}")
                                extracted_files_list.append(repo_filename)
                                file_counter += 1
                                
                            except RuntimeError as e:
                                if 'password' in str(e).lower():
                                    print(f"  ❌ 密码错误 (文件: {base_filename})")
                                else:
                                    print(f"  ❌ 运行时错误 (文件: {base_filename}): {e}")
                            except Exception as e:
                                print(f"  ❌ 提取时发生未知错误 (文件: {base_filename}): {e}")

            except pyzipper.BadZipFile: 
                 print(f"❌ 下载的文件不是一个有效的 ZIP 文件。")
            except Exception as e:
                print(f"❌ 下载或解压 Google Drive 文件失败: {e}")
        else:
            print(f"\n--- 步骤 3/4: 跳过下载和提取 (未找到 Google Drive 链接) ---")

        # --- 总结 ---
        if not extracted_files_list:
            print(f"\n--- 任务完成 ---")
            print(f"⚠️ 未能在 ZIP 中找到任何匹配文件。")
        else:
            print(f"\n--- 任务完成 ---")
            print(f"成功提取并保存了 {len(extracted_files_list)} 个文件。")

    except Exception as e:
        print(f"\n发生严重错误：{e}")

if __name__ == "__main__":
    main()
