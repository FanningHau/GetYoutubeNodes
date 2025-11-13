# GetYoutubeNodes - 自动订阅提取器

[![Daily Update Status](https://github.com/FanningHau/GetYoutubeNodes/actions/workflows/daily_download.yml/badge.svg)](https://github.com/FanningHau/GetYoutubeNodes/actions/workflows/daily_download.yml)

这是一个使用 GitHub Actions 自动运行的 Python 脚本项目。

它的主要功能是**每天自动**访问一个指定的 YouTube 视频，从中找到 Google Drive 链接，下载对应的加密 `.zip` 包，然后解压提取出所有 `...复制导入.txt` 文件，最后将这些文件作为 `1.txt`, `2.txt`, `3.txt`... 保存到本仓库的根目录。

这个仓库被设为 **Public (公开)**，以便通过 CDN 作为 V2RayN, Clash 等客户端的订阅链接源。

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

## 维护与配置 (重要)

本项目的核心配置完全依赖于 GitHub Secrets (仓库秘密)。

**每月（或当链接/密码失效时）**，您需要访问本仓库的 `Settings > Secrets and variables > Actions` 页面，更新以下 **3** 个秘密的值：

1.  `YOUTUBE_API_KEY`:
    * **用途**: 用于 Google YouTube Data API v3，以便脚本有权限读取视频介绍。
    * **内容**: 您的 Google API 密钥。

2.  `VIDEO_ID`:
    * **用途**: 指定脚本去哪个 YouTube 视频（例如 `FNs1N31XZtE`）寻找 Google Drive 链接。
    * **更新**: **这是最常需要更新的！**

3.  `ZIP_PASSWORD`:
    * **用途**: GDrive 中 `.zip` 压缩包的解压密码。
    * **更新**: 当密码变更时，必须更新这里。

**注意：** 更新 Secrets 后，您无需修改任何代码。您可以**手动触发一次 Action**，自动化流程将自动使用新的 Secret 值来获取最新的文件。
