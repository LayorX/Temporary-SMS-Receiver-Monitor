# **Temporary SMS Receiver Monitor**
<div align="center">

<img src="https://i.meee.com.tw/ikqBwaY.jpg" alt="Project Banner" style="border-radius: 10px; margin-top: 10px; margin-bottom: 10px;width: 300px; height: 300px;">

</div>

<p align="center">  
<strong>English</strong> •  
<a href="./README.md"><strong>繁體中文 (Traditional Chinese)</strong></a>  
</p>

This project is a Python application for scraping temporary SMS receiver numbers from **multiple sources**. It offers the following core features:

* **Multi-Website Support**: Scrapes numbers and messages from multiple sites, including `freereceivesms.com`, `receive-smss.com`, and `temp-number.com`.
* **Multi-Language Interface**: Supports **English** and **Traditional Chinese**, easily switchable via command-line arguments.
* **Flexible Command-Line Controls**: Allows users to customize which websites to scrape, set the display language, and integrate with ngrok for public URLs.
* **Efficient Concurrent Scraping**: Uses a **ThreadPoolExecutor** to concurrently check multiple number pages and identify active numbers.

![Demo GIF](demo_en.png)

## **🚀 Project Setup**

### **1\. Prerequisites**

* Python 3.10 or newer.  
* uv (recommended package manager) or pip.  
* Google Chrome browser (for local execution).  
* [ngrok Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) (optional but recommended for public access).

### **2\. Install Dependencies**

The project uses pyproject.toml. Install dependencies using uv or pip:

`uv sync`  
\# OR  
`pip install beautifulsoup4 flask pyngrok requests selenium tomli waitress webdriver-manager`

### **3\. Configuration (config.toml)**

Edit the config.toml file to suit your needs:

| Setting | Description |
| :---- | :---- |
| ngrok\_auth\_token | Your ngrok key. If running in Colab, it's best to leave this blank and pass the token via command line. |
| country\_code | The country code for numbers to search (e.g., us, ca, gb). |
| cache\_duration\_seconds | The interval (in seconds) for the background scraper to refresh data (default 300 seconds, or 5 minutes). |
| max\_workers | The maximum number of threads to use for concurrent number checking. |

## **💻 Execution Guide**

This project supports custom settings via command-line arguments for flexible service startup.

### **Command-Line Arguments**

You can run `uv run python main.py --help` to see all available arguments.

| Argument | Options | Default | Description |
| :--- | :--- | :--- | :--- |
| `--web` | `1`, `2`, `3`, `top2`, `all` | `all` | **Specify websites to scrape**:<br>• `1`: freereceivesms.com<br>• `2`: temp-number.com<br>• `3`: receive-smss.com<br>• `top2`: Scrape the top 2 websites<br>• `all`: Scrape all websites |
| `--lan` | `zh`, `en` | `en` | **Set display language**:<br>• `zh`: Traditional Chinese<br>• `en`: English |
| `--ngrok_token` | `YOUR_TOKEN` | Value from `config.toml` | **Set ngrok token**:<br>Provide your ngrok Authtoken via the command line. This overrides the setting in `config.toml`. |

### **Execution Examples**

#### **1. Basic Start (Local Mode)**

This starts the service locally at `http://127.0.0.1:5000` with default settings (scrape all sites, English interface).

```bash
uv run python main.py
```

#### **2. Start with a Public URL**

Provide your ngrok token to create a public URL for the service.

```bash
uv run python main.py --ngrok_token <YOUR_NGROK_TOKEN>
```

#### **3. Specify Website and Language**

Scrape only `receive-smss.com` (`--web 2`) and switch the terminal and web interface to Traditional Chinese (`--lan zh`).

```bash
uv run python main.py --web 2 --lan zh
```

#### **4. Run in Google Colab**

In a Colab environment, it's recommended to store your ngrok token in the Secrets Manager and run the following command to get a public monitoring URL.

```python
# Read the token from Colab Secrets
from google.colab import userdata
ng_token = userdata.get("NGROK_AUTH_TOKEN")

# Run the main script to scrape all websites and create an ngrok tunnel
!uv run python main.py --web all --ngrok_token $ng_token
```
<a href="https://colab.research.google.com/github/LayorX/Temporary-SMS-Receiver-Monitor/blob/master/Temporary_SMS_Receiver_Monitor.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

[Click here to run quickly in Google Colab](/Temporary_SMS_Receiver_Monitor.ipynb)


## **💡 Optimization Summary**

The core performance issue in the original code was the repeated execution of **ChromeDriverManager().install()** inside the concurrent threads. This caused significant overhead.

| Aspect | Original Code (main.py) | Optimized Code (Revised) | Benefit |
| :---- | :---- | :---- | :---- |
| **Scraper Performance** | Repeated calls to ChromeDriverManager().install() in every thread. | **ChromeDriverManager().install() is now called only ONCE during startup.** | **Dramatically improved startup time and scraping efficiency.** Avoids unnecessary driver file checks and setup multiple times per cache update cycle. |

The revised files maintain the clear separation between local and Colab initialization while incorporating the critical performance fix.


## **💖 Contributing**

This is an open-source project, and contributions of all kinds are welcome\! **Whether you are an experienced developer or a newcomer, your help is appreciated in making this tool even better\!**

### [**👉Contributing**](./CONTRIBUTING.md) 

We will review your contribution as soon as possible. Thank you to everyone who dedicates their time and effort to this project\!

## **📄 License**

This project is licensed under the [MIT License](https://www.google.com/search?q=./LICENSE).
