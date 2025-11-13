import sys
import re
import os
import gdown     
from googleapiclient.discovery import build
from datetime import datetime
import zipfile 
import io      

# --- (变量配置和步骤 1 & 2 保持不变) ---
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

    print(f"--- 正在处理 Video ID: {VIDEO_ID} ---")
    video_url = f"https://www.youtube.com/watch?v={VIDEO_ID}"
    
    try:
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

        # --- (!! 核心修改在步骤 4 !!) ---
        extracted_files_list = [] 
        if found_gdrive_link:
            print(f"\n--- 步骤 3: 下载 Google Drive 文件 ---")
            try:
                gdown.download(found_gdrive_link, DOWNLOAD_FILENAME, quiet=False, fuzzy=True)
                print(f"✅ 成功下载文件: {DOWNLOAD_FILENAME}")

                print(f"\n--- 步骤 4: 扫描 {DOWNLOAD_FILENAME} 内的所有目标文件 ---")
                pwd_bytes = ZIP_PASSWORD.encode('utf-8')

                with zipfile.ZipFile(DOWNLOAD_FILENAME, 'r') as zip_ref:
                    
                    # (!!) --- DEBUG：打印所有文件名 ---
                    print("\n[DEBUG] 正在读取 Zip 包内的所有文件列表:")
                    for file_info in zip_ref.infolist():
                        print(f"  [DEBUG] 原始路径: {file_info.filename}")
                        
                        # (!!) 尝试修复编码问题
                        try:
                            # 尝试用 GBK 解码 (Windows 中文默认)
                            fixed_filename = file_info.filename.encode('cp437').decode('gbk')
                        except:
                            # 如果失败，则使用原始路径
                            fixed_filename = file_info.filename

                        base_filename = os.path.basename(fixed_filename)
                        print(f"  [DEBUG] 解码后 basename: '{base_filename}'")
                    print("[DEBUG] 文件列表读取完毕。\n")
                    # --- DEBUG 结束 ---

                    # 再次遍历以进行提取
                    for file_info in zip_ref.infolist():
                        if file_info.is_dir():
                            continue
                        
                        # (!!) 使用与上面 DEBUG 相同的解码逻辑
                        try:
                            fixed_filename = file_info.filename.encode('cp437').decode('gbk')
                        except:
                            fixed_filename = file_info.filename
                        
                        base_filename = os.path.basename(fixed_filename)
                        
                        # (!!) 使用更健壮的检查：去除空格并忽略大小写
                        target_suffix = '复制导入.txt'
                        if base_filename.strip().lower().endswith(target_suffix.lower()):
                            print(f"  -> [!!] 匹配成功: {fixed_filename}")
                            
                            try:
                                # (!!) 保存到根目录的文件名
                                repo_filename = base_filename.strip() 
                                with zip_ref.open(file_info, pwd=pwd_bytes) as f:
                                    content = io.TextIOWrapper(f, encoding='utf-8').read()
                                
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
            print(f"\n--- 步骤 3/4: 跳过下载和提取 (未找到 Google Drive 链接) ---")

        # --- 总结 ---
        if not extracted_files_list:
            print(f"\n--- 任务完成 ---")
            print(f"⚠️ 未能在 {DOWNLOAD_FILENAME} 中找到任何匹配 '...复制导入.txt' 的文件。")
            print(f"  (!!) 请检查上面的 [DEBUG] 日志输出，查看文件名是否是乱码 (!!)")
        else:
            print(f"\n--- 任务完成 ---")
            print(f"成功提取并保存了 {len(extracted_files_list)} 个文件。")

    except Exception as e:
        print(f"\n发生严重错误：{e}")

if __name__ == "__main__":
    main()
