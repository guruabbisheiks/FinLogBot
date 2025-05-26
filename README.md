# Building a Personal Finance Telegram Bot with Gemini AI and Google Sheets

*Published on May 26, 2025*

---

## 🧭 Introduction

In an era of increasing digital spending, tracking personal finances should be effortless. I decided to create a **Telegram bot that acts as my personal finance assistant**, intelligently logging and summarizing expenses from casual text inputs using **Google Gemini** and storing data in **Google Sheets**.

> 📸 _Screenshot: Telegram bot in action showing an expense being logged_

---

## 🎯 Objective

The goal of this project was to:
- Log income/expenses directly from Telegram
- Understand unstructured text using AI (like "Bought snacks ₹120")
- Store and summarize the data in Google Sheets
- Provide useful summaries like total balance and monthly breakdowns

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Python** | Core scripting |
| **Telegram Bot API** | User interaction |
| **Google Sheets API** | Data storage |
| **Google Gemini API** | Parsing unstructured messages |
| **gspread** | Python-GSheets connector |
| **dotenv** | Manage API keys/configs |

> 📸 _Screenshot: Project folder showing key files (.env, bot.py, credentials.json)_

---

## 🔨 How I Implemented It

### 1. Set up a Google Sheet

Create a sheet with these headers:  
`timestamp | description | category | amount | type`

> 📸 _Screenshot: Your Google Sheet template_

### 2. Create a Telegram Bot

Use [BotFather](https://t.me/BotFather) to create a bot and get the API token.

### 3. Configure Google Sheets Access

Generate a `credentials.json` from [Google Cloud Console](https://console.cloud.google.com/).

### 4. Set up Gemini API

Go to [Google AI Studio](https://makersuite.google.com/app) to get your Gemini API key.

### 5. Code the bot (`bot.py`)

- Parses user messages with Gemini
- Validates and stores data in Google Sheets
- Commands like `/summary` and `/breakdown` give useful financial insights

> 📸 _Screenshot: `bot.py` open in Replit or local editor_  
> 📸 _Screenshot: Response from Gemini API in logs_

---

## 💡 Use Cases

- 💬 `"Bought diapers ₹300"` → logged as Baby Care
- 💬 `"Received salary ₹50000"` → logged as Income
- 📊 `/summary` → shows total income/expenses
- 📅 `/breakdown` → monthly & category insights

---

## ☁️ Hosting Options

- **Local** for testing
- **Replit** for always-on hosting (free tier available)

> 📸 _Screenshot: Replit console running the bot_

---

## 🔮 Future Enhancements

- Add visualization (charts) with Google Sheets API
- Voice input support via Telegram voice messages
- Daily/weekly summary via scheduled messages

---

## 🏁 Conclusion

This bot not only simplifies tracking finances but also showcases the power of combining **AI + automation + chat interfaces**. Whether you're a developer or just someone wanting better control of your spending habits—this setup can be life-changing.

---

*Thanks for reading! Feel free to fork, customize, and track your money the smart way.* 💰
