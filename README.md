# GetYoutubeNodes - 自动订阅提取器

[![Daily Update Status](https://github.com/FanningHau/GetYoutubeNodes/actions/workflows/daily_download.yml/badge.svg)](https://github.com/FanningHau/GetYoutubeNodes/actions/workflows/daily_download.yml)

这是一个使用 GitHub Actions 自动运行的 Python 脚本项目。

它的主要功能是**每天自动**访问一个指定的 YouTube 视频，从中找到 Google Drive 链接，下载对应的订阅文件解析并保存到本仓库的根目录。

---

## 自动化工作流

本项目由 `.github/workflows/daily_download.yml` 文件定义的工作流驱动。

1.  **触发方式**:
    * **定时**: 每天在 `08:00 UTC` (北京时间 16:00) 自动运行。
    * **手动**: 可以在 GitHub 仓库的 "Actions" 标签页手动触发 (`workflow_dispatch`)。

2.  **执行步骤**:
    * 检出 (Checkout) `main` 分支的代码。
    * 设置 Python 3.10 环境。
    * 安装 `google-api-python-client` 和 `gdown` 依赖。
    * 执行 `getnodes_modified.py` 脚本。
    * 脚本将新提取的 `1.txt` 等文件保存在根目录，并将下载的临时文件保存在 `temp_downloads/`。
    * 工作流的最后一步会自动将所有变动 (`git add .`) 提交 (Commit) 并推送 (Push) 回 `main` 分支。

---
