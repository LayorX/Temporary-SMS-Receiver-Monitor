# **臨時簡訊接收號碼監控器**
(Temporary SMS Receiver Monitor)
---

<div align="center">

<img src="https://i.meee.com.tw/ikqBwaY.jpg" alt="Project Banner" style="border-radius: 10px; margin-top: 10px; margin-bottom: 10px;width: 300px; height: 300px;">

</div>


<p align="center">  
<a href="./README.en.md"><strong>English</strong></a> •  
<strong>繁體中文</strong>  
</p>

這個專案是一個 Python 應用程式，用於從**多個來源網站**爬取臨時簡訊接收號碼。它具備以下核心功能：

* **多網站支援**：可同時從 `freereceivesms.com`、`receive-smss.com`、`temp-number.com` 等多個網站獲取號碼與簡訊。
* **多語言介面**：支援**繁體中文**與**英文**，可透過命令列參數輕鬆切換。
* **靈活的命令列控制**：允許使用者自訂要爬取的網站、顯示語言，並整合 ngrok 建立公開網址。
* **高效的併發爬蟲**：利用 **執行緒池 (ThreadPoolExecutor)** 併發檢查多個號碼頁面，以找出活躍號碼。

![Demo GIF](demo.png)

## **🚀 專案設置 (Setup)**

### **1\. 先決條件 (Prerequisites)**

* Python 3.10 或更高版本。  
* uv (推薦的 Python 包管理器) 或 pip。  
* Google Chrome 瀏覽器 (用於本地執行)。  
* [ngrok Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) (用於建立公開網址，非必要但推薦)。

### **2\. 安裝依賴項 (Install Dependencies)**

專案使用 pyproject.toml 管理依賴。請使用 uv sync 或 pip install \-r requirements.txt (如果已生成) 來安裝。

`uv sync`

或  

`pip install beautifulsoup4 flask pyngrok requests selenium tomli waitress webdriver-manager`

### **3\. 配置檔案 (config.toml)**

請根據您的需求編輯 config.toml 檔案：

| 設定項目 | 說明 |
| :---- | :---- |
| ngrok\_auth\_token | 您的 ngrok 金鑰。若在 Colab 中執行，此項可留空，透過命令行傳入。 |
| country\_code | 要搜尋的國家/地區代碼 (例如: us, ca, gb)。 |
| cache\_duration\_seconds | 爬蟲背景更新資料的間隔時間（預設 300 秒，即 5 分鐘）。 |
| max\_workers | 併發檢查號碼時使用的最大執行緒數。 |

## **💻 執行指南 (Execution Guide)**

本專案支援透過命令列參數進行客製化設定，讓您能更靈活地啟動服務。

### **命令列參數 (Command-Line Arguments)**

您可以使用 `uv run python main.py --help` 來查看所有可用的參數。

| 參數 | 選項 | 預設值 | 說明 |
| :--- | :--- | :--- | :--- |
| `--web` | `1`, `2`, `3`, `top2`, `all` | `all` | **指定要爬取的網站**：<br>• `1`: freereceivesms.com<br>• `2`: temp-number.com<br>• `3`: receive-smss.com<br>• `top2`: 爬取前兩個網站<br>• `all`: 爬取所有網站 |
| `--lan` | `zh`, `en` | `zh` | **設定顯示語言**：<br>• `zh`: 繁體中文<br>• `en`: 英文 |
| `--ngrok_token` | `YOUR_TOKEN` | `config.toml` 中的值 | **設定 ngrok 權杖**：<br>直接透過命令列提供您的 ngrok Authtoken，此參數會覆寫 `config.toml` 中的設定。 |

### **執行範例 (Examples)**

#### **1. 基本啟動 (本地模式)**

這會使用預設設定 (爬取所有網站、使用中文介面) 在本地 `http://127.0.0.1:5000` 啟動。

```bash
uv run python main.py
```

#### **2. 啟動並建立公開網址**

提供您的 ngrok 權杖，程式將會為您建立一個公開的網址。

```bash
uv run python main.py --ngrok_token <YOUR_NGROK_TOKEN>
```

#### **3. 指定爬取網站並切換為英文介面**

只爬取 `receive-smss.com` (`--web 2`)，並將終端與網頁介面都切換為英文 (`--lan en`)。

```bash
uv run python main.py --web 2 --lan en
```

#### **4. 在 Google Colab 中執行**

在 Colab 環境中，建議將 ngrok 權杖儲存在 Secrets Manager 中，並透過以下指令執行，即可獲得一個公開的監控網址。

```python
# 從 Colab Secrets 讀取權杖
from google.colab import userdata
ng_token = userdata.get("NGROK_AUTH_TOKEN")

# 執行主程式，爬取所有網站並建立 ngrok 通道
!uv run python main.py --web all --ngrok_token $ng_token
```
<a href="https://colab.research.google.com/github/LayorX/Temporary-SMS-Receiver-Monitor/blob/master/Temporary_SMS_Receiver_Monitor.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

[點此在 Google Colab 中快速執行](/Temporary_SMS_Receiver_Monitor.ipynb)


## **💡 優化分析總結 (Optimization Summary)**

| 項目 | 原始程式碼 (main.py) | 優化後的程式碼 (已修訂) | 效益 |
| :---- | :---- | :---- | :---- |
| **結構重複** | 兩個檔案高度重複。 | 結構分離但核心邏輯相同（保留分離以適應不同啟動方式）。 | **清晰度維持**，未來可進一步重構。 |
| **爬蟲效能** | 在每個執行緒中重複呼叫 ChromeDriverManager().install()。 | **將 ChromeDriverManager().install() 移至主程式啟動區塊，僅執行一次。** | **極大提升啟動速度和爬蟲效率**，避免數十次重複的驅動程式檢查和設定。 |
| **WebDriver** | 每個檢查任務啟動一個獨立的瀏覽器實例。 | 保持現有設計，但共用單一 Service 實例。 | 這是 Selenium 併發的標準模式，但應留意 **MAX\_WORKERS** 的設定，數值過高仍可能耗盡系統資源。 |

優化後的程式碼主要解決了 **WebDriver 驅動程式的重複安裝問題**，這是在使用 Selenium 進行併發爬蟲時最常見且影響最大的效能瓶頸。

## **💖 歡迎貢獻 (Contributing)**

這個專案是開源的，我們非常歡迎任何形式的貢獻！**無論您是經驗豐富的開發者，還是剛入門的新手，都歡迎您一起加入，讓這個工具變得更好！**

### [**👉貢獻**](./CONTRIBUTING.zh-TW.md) 


我們將會盡快 review 您的貢獻。感謝所有為這個專案付出時間和精力的開發者！

## **📄 授權 (License)**

本專案採用 [MIT License](./LICENSE) 授權。
