import os
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from datetime import datetime # Ensure this is imported
import requests
import json

# Load environment variables from .env file
load_dotenv()

# --- Configuration from Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SHEET_NAME = os.getenv("SHEET_NAME")

# Validate essential environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set. Please check your .env file.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please check your .env file.")
if not SHEET_NAME:
    raise ValueError("SHEET_NAME environment variable not set. Please check your .env file.")

# Initialize Telegram bot
bot = telebot.TeleBot(BOT_TOKEN)

# Setup Google Sheets authorization scopes and client
try:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    print(f"Error setting up Google Sheets: {e}")
    print("Please ensure 'credentials.json' is correctly configured and the Google Sheet name is correct.")
    exit()

# Gemini API endpoint (API key is passed as a query parameter)
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Headers for the Gemini API request
headers = {
    "Content-Type": "application/json"
}

def parse_expense(text):
    """
    Parses expense/income data from a given text using the Gemini API.
    It expects the Gemini API to return a JSON object with specific fields.
    """
    gemini_url_with_key = f"{GEMINI_API_BASE_URL}?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Extract expense/income data from the following message. "
                            "Reply ONLY with a JSON object containing 'description' (string), "
                            "'category' (string, 'Rent', 'EMI', 'Groceries & Home Needs', 'Utilities', 'Transportation', 'Baby Care', 'Insurance', 'Entertainment', 'Miscellaneous', 'Amount Lend', 'Investments', 'Income'), 'amount' (number), and 'type' (string, either 'expense' or 'income').\n\n"
                            f"Message: {text}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "amount": {"type": "NUMBER"},
                    "type": {"type": "STRING", "enum": ["expense", "income"]}
                },
                "required": ["description", "category", "amount", "type"]
            },
            "temperature": 0.0,
            "maxOutputTokens": 500
        }
    }

    try:
        print(f"Message:{text} -> Sending request to Gemini API...")
        response = requests.post(gemini_url_with_key, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print("Gemini API response received successfully.")
        # print(f"Gemini API raw response: {json.dumps(data, indent=2)}")

        if data and data.get("candidates") and data["candidates"][0].get("content") and \
           data["candidates"][0]["content"].get("parts") and data["candidates"][0]["content"]["parts"][0].get("text"):
            content_json_str = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content_json_str)
            return parsed
        else:
            print("Gemini API response did not contain expected content structure.")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        print(f"Error decoding JSON from Gemini response: {json_err}. Raw content: {content_json_str if 'content_json_str' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in parse_expense: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    """Handles the /start command."""
    bot.reply_to(message, "Hi! Send me your expenses or incomes in any message, e.g., 'Bought coffee ₹150'. Use /summary to get your totals.")

@bot.message_handler(commands=['summary'])
def summary(message):
    """Provides a summary of total income and expenses from the Google Sheet."""
    try:
        records = sheet.get_all_records()
        total_expense = 0.0
        total_income = 0.0
        
        for r in records:
            try:
                amount = float(r.get('amount', 0))
                record_type = str(r.get('type', '')).lower()
                
                if record_type == 'expense':
                    total_expense += amount
                elif record_type == 'income':
                    total_income += amount
            except ValueError:
                print(f"Skipping record due to invalid amount or type: {r}")
                continue
        
        summary_msg = (
            f"📊 Expense Summary:\n"
            f"Total Income: ₹{total_income:.2f}\n"
            f"Total Expense: ₹{total_expense:.2f}\n"
            f"Balance: ₹{total_income - total_expense:.2f}"
        )
        bot.reply_to(message, summary_msg)
    except Exception as e:
        bot.reply_to(message, f"Error retrieving summary: {e}")

# --- NEW FUNCTION FOR MONTHLY/CATEGORY BREAKDOWN ---
@bot.message_handler(commands=['breakdown'])
def monthly_breakdown_summary(message):
    """Provides a monthly and category-wise breakdown of expenses and income."""
    try:
        records = sheet.get_all_records()
        if not records:
            bot.reply_to(message, "Your sheet is empty. No breakdown available.")
            return

        # Structure: {'YYYY-MM': {'month_name': 'Month Year', 'expenses': {'Category': amount}, 'income': total_income_for_month, 'total_monthly_expense': total, 'total_monthly_income': total}}
        monthly_data = {} 

        for r in records:
            try:
                # Extract and validate data from the record
                timestamp_str = r.get('timestamp')
                category = r.get('category', 'N/A').strip() or 'Uncategorized' # Default to 'Uncategorized' if category is empty
                amount = float(r.get('amount', 0))
                typ = str(r.get('type', '')).lower()

                # Basic validation for essential fields
                if not timestamp_str or not isinstance(amount, (int, float)) or amount <= 0:
                    print(f"Skipping invalid record: {r} (Missing timestamp, invalid amount, or non-positive amount)")
                    continue

                # Parse timestamp to get month and year
                dt_object = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                month_year_key = dt_object.strftime("%Y-%m") # e.g., "2024-05"
                month_name = dt_object.strftime("%B %Y") # e.g., "May 2024"

                # Initialize month entry if it doesn't exist
                if month_year_key not in monthly_data:
                    monthly_data[month_year_key] = {
                        'month_name': month_name,
                        'expenses': {},
                        'income': 0.0,
                        'total_monthly_expense': 0.0,
                        'total_monthly_income': 0.0
                    }
                
                month_entry = monthly_data[month_year_key]

                # Aggregate data
                if typ == 'expense':
                    month_entry['expenses'][category] = month_entry['expenses'].get(category, 0.0) + amount
                    month_entry['total_monthly_expense'] += amount
                elif typ == 'income':
                    month_entry['income'] += amount
                    month_entry['total_monthly_income'] += amount

            except (ValueError, TypeError) as e:
                print(f"Error processing record '{r}': {e}. Skipping this record.")
                continue # Skip to the next record if parsing fails

        # Sort months chronologically for ordered display
        sorted_months = sorted(monthly_data.keys())

        summary_msg = "📈 **Monthly Financial Breakdown** 📈\n\n"
        
        # If no valid records were processed after filtering
        if not sorted_months:
            summary_msg = "No valid financial records found to generate a breakdown."
            bot.reply_to(message, summary_msg)
            return

        # Build the formatted message
        for month_key in sorted_months:
            month_entry = monthly_data[month_key]
            summary_msg += f"--- **{month_entry['month_name']}** ---\n"
            
            # Display Income
            summary_msg += f"💰 Income: ₹{month_entry['income']:.2f}\n"

            # Display Expenses by Category
            if month_entry['expenses']:
                summary_msg += "💸 Expenses by Category:\n"
                # Sort categories alphabetically for consistent display
                sorted_categories = sorted(month_entry['expenses'].items(), key=lambda item: item[0])
                for category, amount in sorted_categories:
                    summary_msg += f"  - {category}: ₹{amount:.2f}\n"
            else:
                summary_msg += "💸 No expenses recorded for this month.\n"

            # Display Monthly Totals and Balance
            monthly_balance = month_entry['total_monthly_income'] - month_entry['total_monthly_expense']
            summary_msg += (
                f"Total Monthly Expense: ₹{month_entry['total_monthly_expense']:.2f}\n"
                f"Monthly Balance: ₹{monthly_balance:.2f}\n\n"
            )

        bot.reply_to(message, summary_msg, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"Error generating breakdown summary: {e}")
        print(f"Error in monthly_breakdown_summary: {e}")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handles incoming text messages, parses them as expenses/incomes, and logs to Google Sheet."""
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing') # Show typing indicator
    parsed = parse_expense(user_text)
    
    if parsed:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = parsed.get('description', 'N/A')
        category = parsed.get('category', 'N/A')
        amount = parsed.get('amount', 0)
        typ = parsed.get('type', 'expense').lower() # Default to 'expense' if type is missing
        
        # Basic validation for amount
        if not isinstance(amount, (int, float)) or amount <= 0:
            bot.reply_to(message, "Sorry, I couldn't extract a valid positive amount from your message. Please try again.")
            return

        try:
            sheet.append_row([timestamp, description, category, amount, typ])
            bot.reply_to(message, f"✅ Logged your {typ}: {description} of ₹{amount:.2f}")
        except Exception as e:
            bot.reply_to(message, f"Failed to log your data to Google Sheet: {e}")
            print(f"Error appending row to sheet: {e}")
    else:
        bot.reply_to(message, "Sorry, I couldn't understand your message. Please try again with details like 'Bought snacks ₹150' or 'Received salary ₹50000'.")

if __name__ == "__main__":
    print("🤖 Personal Finance Bot using Google Gemini is running!")
    print("Waiting for Telegram messages...")
    bot.infinity_polling()