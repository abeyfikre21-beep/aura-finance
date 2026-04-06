import base64
import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from supabase import Client, create_client
except ImportError:
    Client = None
    create_client = None


APP_TITLE = "Aura Finance"
DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "aura_state.json"
AURA_MARK = """
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M4 20H20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M6 20V9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M10 20V9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M14 20V9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M18 20V9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M3.5 9.5L12 4L20.5 9.5H3.5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
</svg>
"""


DEFAULT_STATE = {
    "accounts": {
        "monthly_income": 0.0,
        "checking": 0.0,
        "savings": 0.0,
        "retirement": 0.0,
        "monthly_savings_goal": 1000.0,
    },
    "profile": {
        "name": "Your Name",
        "title": "Personal Finance Owner",
        "photo": "",
    },
    "auth": {
        "username": "",
        "password_hash": "",
        "configured": False,
    },
    "monthly_budgets": [
        {"name": "Housing", "budget": 0.0, "spent": 0.0, "bill_day": 1},
        {"name": "Food", "budget": 0.0, "spent": 0.0, "bill_day": 7},
        {"name": "Emergency Expense", "budget": 0.0, "spent": 0.0, "bill_day": 15},
    ],
    "weekly_budgets": [
        {"name": "Food", "budget": 0.0, "spent": 0.0},
        {"name": "Gas", "budget": 0.0, "spent": 0.0},
    ],
    "debts": [
        {"name": "Credit Card", "balance": 0.0, "payment": 0.0, "due_day": 10},
    ],
    "leftover_ledger": [],
    "monthly_history": [],
    "weekly_history": [],
    "last_month_rollover": "",
    "last_week_rollover": "",
    "_meta": {
        "updated_at": "",
    },
}


def default_state_copy() -> dict:
    return json.loads(json.dumps(DEFAULT_STATE))


def state_fingerprint(state: dict) -> str:
    copy_state = json.loads(json.dumps(state))
    copy_state.setdefault("_meta", {})
    copy_state["_meta"]["updated_at"] = ""
    return json.dumps(copy_state, sort_keys=True)


def today_local() -> date:
    return datetime.now().date()


def month_key(value: date | None = None) -> str:
    current = value or today_local()
    return current.strftime("%Y-%m")


def week_start(value: date | None = None) -> date:
    current = value or today_local()
    return current - timedelta(days=current.weekday())


def week_key(value: date | None = None) -> str:
    return week_start(value).strftime("%Y-%m-%d")


def week_label(value: str) -> str:
    base = datetime.strptime(value, "%Y-%m-%d").date()
    end = base + timedelta(days=6)
    return f"{base.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"


def money(value: float) -> str:
    return f"${value:,.0f}" if abs(value) >= 1 else f"${value:,.2f}"


def load_state() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    local_edit_until = float(st.session_state.get("local_edit_priority_until", 0.0) or 0.0)
    if shared_storage_enabled() and datetime.now().timestamp() >= local_edit_until:
        loaded = load_state_from_supabase()
        if loaded is not None:
            write_local_backup(loaded)
            return loaded

    if not STATE_FILE.exists():
        default_state = default_state_copy()
        save_state(default_state)
        return default_state

    try:
        raw = STATE_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            raise json.JSONDecodeError("Empty JSON file", "", 0)
        loaded = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        default_state = default_state_copy()
        save_state(default_state)
        return default_state

    if "_meta" not in loaded:
        loaded["_meta"] = {"updated_at": ""}
    return loaded


def save_state(state: dict, immediate_remote: bool = False) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    state.setdefault("_meta", {})
    state["_meta"]["updated_at"] = datetime.now().isoformat()
    write_local_backup(state)
    fingerprint = state_fingerprint(state)
    st.session_state["last_local_snapshot"] = fingerprint
    st.session_state["local_edit_priority_until"] = datetime.now().timestamp() + 8
    if shared_storage_enabled():
        if immediate_remote:
            save_state_to_supabase(state)
            st.session_state["last_remote_snapshot"] = fingerprint
            st.session_state["pending_remote_snapshot"] = ""
            st.session_state["pending_remote_since"] = 0.0
        else:
            if fingerprint != st.session_state.get("last_remote_snapshot", ""):
                st.session_state["pending_remote_snapshot"] = fingerprint
                st.session_state["pending_remote_since"] = datetime.now().timestamp()


def write_local_backup(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def shared_storage_enabled() -> bool:
    return bool(
        create_client
        and secrets_available()
        and secret_value("SUPABASE_URL")
        and (
            secret_value("SUPABASE_SERVICE_KEY")
            or secret_value("SUPABASE_KEY")
        )
    )


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client | None:
    if not shared_storage_enabled():
        return None
    url = secret_value("SUPABASE_URL")
    key = secret_value("SUPABASE_SERVICE_KEY") or secret_value("SUPABASE_KEY")
    if not url or not key or not create_client:
        return None
    return create_client(url, key)


def supabase_state_table() -> str:
    return secret_value("SUPABASE_STATE_TABLE", "aura_app_state") or "aura_app_state"


def supabase_state_id() -> str:
    return secret_value("SUPABASE_STATE_ID", "primary") or "primary"


def load_state_from_supabase() -> dict | None:
    client = get_supabase_client()
    if client is None:
        return None
    try:
        response = (
            client.table(supabase_state_table())
            .select("payload")
            .eq("state_id", supabase_state_id())
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            default_state = default_state_copy()
            save_state_to_supabase(default_state)
            return default_state
        loaded = rows[0].get("payload") or default_state_copy()
        if "_meta" not in loaded:
            loaded["_meta"] = {"updated_at": ""}
        return loaded
    except Exception:
        return None


def save_state_to_supabase(state: dict) -> None:
    client = get_supabase_client()
    if client is None:
        return
    try:
        (
            client.table(supabase_state_table())
            .upsert(
                {
                    "state_id": supabase_state_id(),
                    "payload": state,
                    "updated_at": state["_meta"]["updated_at"],
                },
                on_conflict="state_id",
            )
            .execute()
        )
    except Exception:
        pass


def flush_remote_save_if_due(state: dict, debounce_seconds: float = 2.0) -> None:
    pending_snapshot = st.session_state.get("pending_remote_snapshot", "")
    pending_since = float(st.session_state.get("pending_remote_since", 0.0) or 0.0)
    if not pending_snapshot or not pending_since or not shared_storage_enabled():
        return
    if datetime.now().timestamp() - pending_since < debounce_seconds:
        return
    current_fingerprint = state_fingerprint(state)
    if current_fingerprint != pending_snapshot:
        st.session_state["pending_remote_snapshot"] = current_fingerprint
        st.session_state["pending_remote_since"] = datetime.now().timestamp()
        return
    save_state_to_supabase(state)
    st.session_state["last_remote_snapshot"] = current_fingerprint
    st.session_state["pending_remote_snapshot"] = ""
    st.session_state["pending_remote_since"] = 0.0


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_username(value: str) -> str:
    cleaned = str(value or "").strip().lower()
    return "".join(ch for ch in cleaned if ch.isalnum() or ch in "._-@")


def secret_value(key: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(key, default) or default).strip()
    except Exception:
        return default


def secrets_available() -> bool:
    try:
        _ = st.secrets
        return True
    except Exception:
        return False


def shared_auth_from_secrets() -> dict | None:
    username = normalize_username(
        secret_value("AURA_USERNAME")
        or secret_value("aura_username")
    )
    password_hash = secret_value("AURA_PASSWORD_HASH") or secret_value("aura_password_hash")
    plain_password = secret_value("AURA_PASSWORD") or secret_value("aura_password")

    if not password_hash and plain_password:
        password_hash = hash_password(plain_password)

    if username and password_hash:
        return {
            "username": username,
            "password_hash": password_hash,
            "source": "shared_secrets",
        }
    return None


def normalize_rows(rows: list[dict], weekly: bool = False) -> list[dict]:
    normalized = []
    for row in rows:
        item = {
            "name": row.get("name", "Untitled"),
            "budget": float(row.get("budget", 0.0) or 0.0),
            "spent": float(row.get("spent", 0.0) or 0.0),
        }
        if not weekly:
            bill_day = int(row.get("bill_day", 1) or 1)
            item["bill_day"] = min(31, max(1, bill_day))
        normalized.append(item)
    return normalized


def normalize_debts(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "name": row.get("name", "Debt"),
                "balance": float(row.get("balance", 0.0) or 0.0),
                "payment": float(row.get("payment", 0.0) or 0.0),
                "due_day": min(31, max(1, int(row.get("due_day", 1) or 1))),
            }
        )
    return normalized


def add_leftover_entry(state: dict, source: str, amount: float, kind: str, period: str) -> None:
    if amount <= 0:
        return
    state["leftover_ledger"].insert(
        0,
        {
            "date": today_local().isoformat(),
            "source": source,
            "amount": round(amount, 2),
            "kind": kind,
            "period": period,
        },
    )


def leftover_balance(state: dict) -> float:
    return sum(item["amount"] for item in state["leftover_ledger"])


def process_rollovers(state: dict) -> bool:
    changed = False
    current_month = month_key()
    current_week = week_key()
    last_month = state.get("last_month_rollover", "")
    last_week = state.get("last_week_rollover", "")

    if not last_month:
        state["last_month_rollover"] = current_month
        changed = True
    elif last_month != current_month:
        monthly_rows = normalize_rows(state.get("monthly_budgets", []), weekly=False)
        total_budget = sum(row["budget"] for row in monthly_rows)
        total_spent = sum(row["spent"] for row in monthly_rows)
        savings_goal = float(state["accounts"].get("monthly_savings_goal", 0.0) or 0.0)
        income = float(state["accounts"].get("monthly_income", 0.0) or 0.0)
        for row in monthly_rows:
            unused = max(row["budget"] - row["spent"], 0.0)
            add_leftover_entry(state, f"{row['name']} monthly leftover", unused, "monthly_leftover", last_month)
        free_cash = max(income - total_budget - savings_goal, 0.0)
        add_leftover_entry(state, "Income left after budget and savings goal", free_cash, "income_leftover", last_month)
        status = "Saved" if total_budget >= total_spent else "Overspent"
        amount = max(total_budget - total_spent, 0.0) if status == "Saved" else max(total_spent - total_budget, 0.0)
        state["monthly_history"].insert(
            0,
            {
                "month": last_month,
                "budgeted": round(total_budget, 2),
                "spent": round(total_spent, 2),
                "saved": round(max(total_budget - total_spent, 0.0), 2),
                "overspent": round(max(total_spent - total_budget, 0.0), 2),
                "leftover_sent": round(sum(max(r["budget"] - r["spent"], 0.0) for r in monthly_rows), 2),
                "status": status,
                "amount": round(amount, 2),
            },
        )
        for row in state["monthly_budgets"]:
            row["spent"] = 0.0
        state["last_month_rollover"] = current_month
        changed = True

    if not last_week:
        state["last_week_rollover"] = current_week
        changed = True
    elif last_week != current_week:
        weekly_rows = normalize_rows(state.get("weekly_budgets", []), weekly=True)
        total_budget = sum(row["budget"] for row in weekly_rows)
        total_spent = sum(row["spent"] for row in weekly_rows)
        for row in weekly_rows:
            unused = max(row["budget"] - row["spent"], 0.0)
            add_leftover_entry(state, f"{row['name']} weekly leftover", unused, "weekly_leftover", last_week)
        status = "Saved" if total_budget >= total_spent else "Overspent"
        amount = max(total_budget - total_spent, 0.0) if status == "Saved" else max(total_spent - total_budget, 0.0)
        state["weekly_history"].insert(
            0,
            {
                "week": last_week,
                "budgeted": round(total_budget, 2),
                "spent": round(total_spent, 2),
                "saved": round(max(total_budget - total_spent, 0.0), 2),
                "overspent": round(max(total_spent - total_budget, 0.0), 2),
                "leftover_sent": round(sum(max(r["budget"] - r["spent"], 0.0) for r in weekly_rows), 2),
                "status": status,
                "amount": round(amount, 2),
            },
        )
        for row in state["weekly_budgets"]:
            row["spent"] = 0.0
        state["last_week_rollover"] = current_week
        changed = True

    return changed


def monthly_metrics(state: dict) -> dict:
    income = float(state["accounts"].get("monthly_income", 0.0) or 0.0)
    savings_goal = float(state["accounts"].get("monthly_savings_goal", 0.0) or 0.0)
    rows = normalize_rows(state.get("monthly_budgets", []), weekly=False)
    budgeted = sum(row["budget"] for row in rows)
    spent = sum(row["spent"] for row in rows)
    return {
        "income": income,
        "savings_goal": savings_goal,
        "budgeted": budgeted,
        "spent": spent,
        "left_after_budget_and_savings": income - budgeted - savings_goal,
    }


def weekly_metrics(state: dict) -> dict:
    rows = normalize_rows(state.get("weekly_budgets", []), weekly=True)
    budgeted = sum(row["budget"] for row in rows)
    spent = sum(row["spent"] for row in rows)
    return {"budgeted": budgeted, "spent": spent, "left": budgeted - spent}


def total_debt(state: dict) -> float:
    return sum(item["balance"] for item in normalize_debts(state.get("debts", [])))


def next_bill_record(state: dict):
    today = today_local()
    all_items = []
    for row in normalize_rows(state.get("monthly_budgets", []), weekly=False):
        due = date(today.year, today.month, min(row["bill_day"], 28 if today.month == 2 else row["bill_day"]))
        days = (due - today).days
        if days >= -2:
            all_items.append({"name": row["name"], "amount": row["budget"], "due_day": row["bill_day"], "days": days, "type": "Bill"})
    for row in normalize_debts(state.get("debts", [])):
        due = date(today.year, today.month, min(row["due_day"], 28 if today.month == 2 else row["due_day"]))
        days = (due - today).days
        if days >= -2:
            all_items.append({"name": row["name"], "amount": row["payment"], "due_day": row["due_day"], "days": days, "type": "Debt"})
    if not all_items:
        return None
    return sorted(all_items, key=lambda item: item["days"] if item["days"] >= 0 else 999)[0]


def notification_messages(state: dict) -> list[str]:
    notes = []
    today = today_local()
    for row in normalize_rows(state.get("monthly_budgets", []), weekly=False):
        if row["spent"] > row["budget"]:
            notes.append(f"{row['name']} is over monthly budget by {money(row['spent'] - row['budget'])}. Cover it from leftover money or checking.")
        due_date = date(today.year, today.month, min(row["bill_day"], 28 if today.month == 2 else row["bill_day"]))
        if (due_date - today).days == 1:
            notes.append(f"{row['name']} is due tomorrow.")
    for row in normalize_rows(state.get("weekly_budgets", []), weekly=True):
        if row["spent"] > row["budget"]:
            notes.append(f"{row['name']} is over weekly budget by {money(row['spent'] - row['budget'])}. Use leftover money to absorb it.")
    for row in normalize_debts(state.get("debts", [])):
        due_date = date(today.year, today.month, min(row["due_day"], 28 if today.month == 2 else row["due_day"]))
        if (due_date - today).days == 1:
            notes.append(f"Debt payment for {row['name']} is due tomorrow.")
    if leftover_balance(state) < 0:
        notes.append("Leftover money is negative. Shift the shortage to checking.")
    return notes[:8]


def recommendation_lines(state: dict) -> list[str]:
    monthly = monthly_metrics(state)
    weekly = weekly_metrics(state)
    notes = []
    if monthly["left_after_budget_and_savings"] > 0:
        notes.append(f"You still have {money(monthly['left_after_budget_and_savings'])} after monthly budget and savings. Move it to leftover money.")
    elif monthly["left_after_budget_and_savings"] < 0:
        notes.append(f"You are short {money(abs(monthly['left_after_budget_and_savings']))} after budget and savings. Reduce a category or use checking.")
    if weekly["spent"] > weekly["budgeted"]:
        notes.append(f"Weekly spending is above plan by {money(weekly['spent'] - weekly['budgeted'])}. Cover it from leftover money first.")
    if total_debt(state) > 0:
        notes.append(f"Total debt is {money(total_debt(state))}. Keep checking cash ready for the next payment.")
    highest = None
    for row in normalize_rows(state.get("monthly_budgets", []), weekly=False):
        diff = row["spent"] - row["budget"]
        if diff > 0 and (highest is None or diff > highest[1]):
            highest = (row["name"], diff)
    if highest:
        notes.append(f"{highest[0]} is your biggest over-budget monthly category. Consider pulling {money(highest[1])} from leftover money.")
    if not notes:
        notes.append("Your plan looks stable right now. Keep logging spending so insights stay accurate.")
    return notes[:5]


def monthly_budget_table(state: dict) -> pd.DataFrame:
    rows = []
    for row in normalize_rows(state.get("monthly_budgets", []), weekly=False):
        left = row["budget"] - row["spent"]
        rows.append(
            {
                "Category": row["name"],
                "Budget": row["budget"],
                "Spent": row["spent"],
                "Left": left,
                "Bill Day": row["bill_day"],
                "Status": "Over Budget" if left < 0 else "On Track",
            }
        )
    return pd.DataFrame(rows)


def weekly_budget_table(state: dict) -> pd.DataFrame:
    rows = []
    for row in normalize_rows(state.get("weekly_budgets", []), weekly=True):
        left = row["budget"] - row["spent"]
        rows.append(
            {
                "Category": row["name"],
                "Budget": row["budget"],
                "Spent": row["spent"],
                "Left": left,
                "Status": "Over Budget" if left < 0 else "On Track",
            }
        )
    return pd.DataFrame(rows)


def parse_money_input(raw_value: str, fallback: float) -> float:
    cleaned = str(raw_value).replace("$", "").replace(",", "").strip()
    if cleaned == "":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return fallback


def uploaded_file_to_data_url(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    mime = uploaded_file.type or "image/png"
    return f"data:{mime};base64,{encoded}"


def sync_live_widget_values(state: dict) -> None:
    for idx, row in enumerate(state.get("monthly_budgets", [])):
        if f"m_name_{idx}" in st.session_state:
            row["name"] = st.session_state[f"m_name_{idx}"]
        if f"m_budget_{idx}" in st.session_state:
            row["budget"] = float(st.session_state[f"m_budget_{idx}"])
        if f"m_spent_{idx}" in st.session_state:
            row["spent"] = float(st.session_state[f"m_spent_{idx}"])
        if f"m_bill_{idx}" in st.session_state:
            row["bill_day"] = int(st.session_state[f"m_bill_{idx}"])

    for idx, row in enumerate(state.get("weekly_budgets", [])):
        if f"w_name_{idx}" in st.session_state:
            row["name"] = st.session_state[f"w_name_{idx}"]
        if f"w_budget_{idx}" in st.session_state:
            row["budget"] = float(st.session_state[f"w_budget_{idx}"])
        if f"w_spent_{idx}" in st.session_state:
            row["spent"] = float(st.session_state[f"w_spent_{idx}"])

    for idx, row in enumerate(state.get("debts", [])):
        if f"d_name_{idx}" in st.session_state:
            row["name"] = st.session_state[f"d_name_{idx}"]
        if f"d_balance_{idx}" in st.session_state:
            row["balance"] = float(st.session_state[f"d_balance_{idx}"])
        if f"d_payment_{idx}" in st.session_state:
            row["payment"] = float(st.session_state[f"d_payment_{idx}"])
        if f"d_due_{idx}" in st.session_state:
            row["due_day"] = int(st.session_state[f"d_due_{idx}"])


def hero_card(label: str, value: str, tone: str = "default") -> None:
    st.markdown(
        f"""
        <div class="hero-card {tone}">
            <div class="card-eyebrow">{label}</div>
            <div class="hero-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def soft_card(label: str, value: str, helper: str = "") -> None:
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="card-eyebrow">{label}</div>
            <div class="soft-value">{value}</div>
            <div class="soft-helper">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(mode: str) -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="A", layout="wide", initial_sidebar_state="expanded")
    if mode == "Dark":
        palette = {
            "app_bg": "linear-gradient(180deg, #0f1318 0%, #151b22 55%, #10151b 100%)",
            "text": "#f4efe7",
            "ink": "#ffffff",
            "sidebar_bg": "linear-gradient(180deg, #090c10 0%, #11161c 100%)",
            "sidebar_text": "#f4efe7",
            "title": "#f8f2e8",
            "subtitle": "#b6aa9c",
            "section": "#a89b8c",
            "surface": "rgba(26, 32, 39, 0.88)",
            "surface_border": "rgba(214, 188, 153, 0.12)",
            "surface_shadow": "0 24px 60px rgba(0, 0, 0, 0.35)",
            "default_bg": "linear-gradient(135deg, #1a232c 0%, #24313d 100%)",
            "good_bg": "linear-gradient(135deg, #1a2b24 0%, #234335 100%)",
            "warn_bg": "linear-gradient(135deg, #2b211b 0%, #4a3429 100%)",
            "danger_bg": "linear-gradient(135deg, #2c1c1f 0%, #4a2a31 100%)",
            "eyebrow": "#c8b9a8",
            "value": "#f7f2ea",
            "helper": "#b5a99a",
            "line_title": "#f4efe7",
            "line_helper": "#b5a99a",
            "divider": "rgba(214, 188, 153, 0.12)",
            "warning_bg": "#4a2a31",
            "warning_text": "#ffd6da",
            "good_pill_bg": "#234335",
            "good_pill_text": "#d8f4de",
            "input_bg": "#182029",
            "input_text": "#f7f2ea",
        }
    else:
        palette = {
            "app_bg": "linear-gradient(180deg, #f8f4eb 0%, #f1ece2 60%, #ece6db 100%)",
            "text": "#1f1a17",
            "ink": "#000000",
            "sidebar_bg": "linear-gradient(180deg, #f6f1e7 0%, #ece4d6 100%)",
            "sidebar_text": "#000000",
            "title": "#231d18",
            "subtitle": "#6e6256",
            "section": "#7b6c5e",
            "surface": "rgba(255,255,255,0.68)",
            "surface_border": "rgba(112, 92, 72, 0.15)",
            "surface_shadow": "0 22px 60px rgba(59, 40, 26, 0.08)",
            "default_bg": "linear-gradient(135deg, #fffaf2 0%, #efe5d2 100%)",
            "good_bg": "linear-gradient(135deg, #eef7ef 0%, #deecd8 100%)",
            "warn_bg": "linear-gradient(135deg, #fff4ec 0%, #f6dcc7 100%)",
            "danger_bg": "linear-gradient(135deg, #fff1f1 0%, #f2d1d1 100%)",
            "eyebrow": "#7b6c5e",
            "value": "#1e1813",
            "helper": "#7d7065",
            "line_title": "#2a211b",
            "line_helper": "#786b5f",
            "divider": "rgba(112, 92, 72, 0.12)",
            "warning_bg": "#f5dbdb",
            "warning_text": "#7e2a2a",
            "good_pill_bg": "#dbead7",
            "good_pill_text": "#2f6132",
            "input_bg": "#ffffff",
            "input_text": "#1f1a17",
        }
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');
        .stApp {{ background: {palette["app_bg"]}; color: {palette["ink"]}; }}
        header[data-testid="stHeader"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        header[data-testid="stHeader"]::before,
        header[data-testid="stHeader"]::after,
        header[data-testid="stHeader"] > div,
        header[data-testid="stHeader"] > div::before,
        header[data-testid="stHeader"] > div::after {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] {{ background: {palette["sidebar_bg"]}; }}
        [data-testid="stSidebar"] * {{ color: {palette["sidebar_text"]} !important; }}
        header button,
        button[kind="header"],
        button[kind="headerNoPadding"],
        [data-testid="baseButton-header"],
        [data-testid="baseButton-headerNoPadding"],
        [data-testid="collapsedControl"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            opacity: 1 !important;
            visibility: visible !important;
            display: flex !important;
            z-index: 999999 !important;
            color: {palette["ink"]} !important;
        }}
        [data-testid="stToolbar"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        [data-testid="stDecoration"] {{
            display: none !important;
        }}
        header button::before,
        header button::after,
        header button > div,
        header button > span,
        [data-testid="collapsedControl"]::before,
        [data-testid="collapsedControl"]::after,
        [data-testid="collapsedControl"] > div,
        [data-testid="collapsedControl"] > span {{
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }}
        button[kind="header"],
        button[kind="headerNoPadding"],
        [data-testid="baseButton-header"],
        [data-testid="baseButton-headerNoPadding"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {{
            background: transparent !important;
            color: {palette["ink"]} !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            opacity: 1 !important;
            visibility: visible !important;
            display: flex !important;
            z-index: 999999 !important;
        }}
        header button:focus,
        header button:focus-visible,
        header button:active,
        button[kind="header"]:focus,
        button[kind="header"]:focus-visible,
        button[kind="header"]:active,
        button[kind="headerNoPadding"]:focus,
        button[kind="headerNoPadding"]:focus-visible,
        button[kind="headerNoPadding"]:active,
        [data-testid="baseButton-header"]:focus,
        [data-testid="baseButton-header"]:focus-visible,
        [data-testid="baseButton-header"]:active,
        [data-testid="baseButton-headerNoPadding"]:focus,
        [data-testid="baseButton-headerNoPadding"]:focus-visible,
        [data-testid="baseButton-headerNoPadding"]:active,
        [data-testid="stSidebarCollapseButton"]:focus,
        [data-testid="stSidebarCollapseButton"]:focus-visible,
        [data-testid="stSidebarCollapseButton"]:active,
        [data-testid="collapsedControl"]:focus,
        [data-testid="collapsedControl"]:focus-visible,
        [data-testid="collapsedControl"]:active {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }}
        header button svg,
        header button path,
        button[kind="header"] svg,
        button[kind="header"] path,
        button[kind="headerNoPadding"] svg,
        button[kind="headerNoPadding"] path,
        [data-testid="baseButton-header"] svg,
        [data-testid="baseButton-header"] path,
        [data-testid="baseButton-headerNoPadding"] svg,
        [data-testid="baseButton-headerNoPadding"] path,
        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="collapsedControl"] svg,
        [data-testid="stSidebarCollapseButton"] path,
        [data-testid="collapsedControl"] path {{
            fill: {palette["ink"]} !important;
            stroke: {palette["ink"]} !important;
            color: {palette["ink"]} !important;
            opacity: 1 !important;
            visibility: visible !important;
        }}
        .block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1400px; }}
        h1, h2, h3 {{ font-family: 'Cormorant Garamond', serif; letter-spacing: 0.02em; color: {palette["title"]}; }}
        .brand-row {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            color: {palette["title"]};
        }}
        .brand-row svg {{
            width: 1.45rem;
            height: 1.45rem;
            flex: 0 0 auto;
        }}
        .page-title {{ font-family: 'Cormorant Garamond', serif; font-size: 2.7rem; font-weight: 700; margin-bottom: 0.15rem; color: {palette["title"]}; text-align: left; }}
        .page-subtitle {{ color: {palette["subtitle"]}; margin-bottom: 1rem; text-align: left; }}
        .section-label {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.18em; color: {palette["section"]}; margin: 1rem 0 0.8rem; }}
        .hero-card, .soft-card, .glass-panel {{
            background: {palette["surface"]};
            border: 1px solid {palette["surface_border"]};
            border-radius: 16px;
            box-shadow: {palette["surface_shadow"]};
            padding: 0.68rem 0.82rem;
            min-height: 108px;
        }}
        .hero-card.default {{ background: {palette["default_bg"]}; }}
        .hero-card.good {{ background: {palette["good_bg"]}; }}
        .hero-card.warn {{ background: {palette["warn_bg"]}; }}
        .hero-card.danger {{ background: {palette["danger_bg"]}; }}
        .card-eyebrow {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.15em; color: {palette["eyebrow"]}; margin-bottom: 0.32rem; }}
        .hero-value {{ font-size: 1.48rem; font-weight: 700; color: {palette["value"]}; }}
        .soft-value {{ font-size: 1.08rem; font-weight: 700; color: {palette["value"]}; }}
        .soft-helper {{ font-size: 0.78rem; color: {palette["helper"]}; margin-top: 0.12rem; min-height: 0.9rem; }}
        .panel-title {{ font-family: 'Cormorant Garamond', serif; font-size: 1.28rem; margin-bottom: 0.45rem; color: {palette["title"]}; }}
        .dashboard-group {{
            margin-bottom: 1rem;
        }}
        .mini-line {{ padding: 0.5rem 0; border-bottom: 1px solid {palette["divider"]}; }}
        .mini-line:last-child {{ border-bottom: none; }}
        .line-title {{ font-weight: 600; color: {palette["line_title"]}; }}
        .line-helper {{ color: {palette["line_helper"]}; font-size: 0.9rem; }}
        .warning-pill {{ display: inline-block; padding: 0.4rem 0.7rem; border-radius: 999px; background: {palette["warning_bg"]}; color: {palette["warning_text"]}; font-size: 0.85rem; margin: 0.25rem 0.35rem 0 0; }}
        .good-pill {{ display: inline-block; padding: 0.4rem 0.7rem; border-radius: 999px; background: {palette["good_pill_bg"]}; color: {palette["good_pill_text"]}; font-size: 0.85rem; margin: 0.25rem 0.35rem 0 0; }}
        .quick-edit-anchor {{
            display: flex;
            justify-content: flex-end;
            margin: -0.35rem 0 0.8rem;
        }}
        .quick-edit-anchor [data-testid="stPopover"] > button {{
            width: 2.35rem !important;
            height: 2.35rem !important;
            border-radius: 999px !important;
            padding: 0 !important;
            font-size: 1rem !important;
            font-weight: 700 !important;
        }}
        [data-testid="stExpander"] {{
            background: {palette["surface"]};
            border: 1px solid {palette["surface_border"]};
            border-radius: 18px;
        }}
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] label {{
            color: {palette["ink"]} !important;
        }}
        [data-baseweb="tab-list"] {{
            gap: 0.4rem;
        }}
        [data-baseweb="tab"] {{
            background: {palette["surface"]} !important;
            color: {palette["ink"]} !important;
            border-radius: 999px !important;
            border: 1px solid {palette["surface_border"]} !important;
        }}
        [aria-selected="true"][data-baseweb="tab"] {{
            background: {palette["default_bg"]} !important;
            color: {palette["value"]} !important;
        }}
        [data-testid="stSidebarNav"] *,
        [data-testid="stSidebarNavItems"] *,
        [data-testid="stRadio"] *,
        [data-testid="stSelectbox"] *,
        [data-testid="stNumberInput"] *,
        [data-testid="stTextInput"] *,
        [data-testid="stTextArea"] *,
        [role="listbox"] *,
        [role="option"] *,
        [data-baseweb="menu"] *,
        [data-baseweb="popover"] * {{
            color: {palette["ink"]} !important;
        }}
        .stRadio label,
        .stSelectbox label,
        .stNumberInput label,
        .stTextInput label,
        .stTextArea label,
        .stCaption,
        p,
        li,
        span {{
            color: {palette["ink"]};
        }}
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] span,
        div[data-baseweb="popover"] *,
        textarea,
        input {{
            background: {palette["input_bg"]} !important;
            color: {palette["input_text"]} !important;
        }}
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button {{
            -webkit-appearance: none !important;
            margin: 0 !important;
        }}
        input[type=number] {{
            -moz-appearance: textfield !important;
            appearance: textfield !important;
        }}
        [data-testid="stNumberInput"] button {{
            display: none !important;
        }}
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] div,
        [data-baseweb="select"] input,
        [data-baseweb="menu"] *,
        [role="listbox"] *,
        [role="option"] * {{
            color: {palette["ink"]} !important;
        }}
        button[kind],
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stPopover"] button {{
            background: {palette["surface"]} !important;
            color: {palette["ink"]} !important;
            border: 1px solid {palette["surface_border"]} !important;
        }}
        input::placeholder, textarea::placeholder {{ color: {palette["helper"]} !important; opacity: 1; }}
        label, .stMarkdown, .stCaption, .stText, .st-emotion-cache-10trblm, .stSubheader, .stHeader {{ color: {palette["ink"]}; }}
        [data-testid="stDataFrame"] * {{ color: {palette["ink"]} !important; }}
        [data-testid="stTable"] * {{ color: {palette["ink"]} !important; }}
        .quick-edit-panel {{
            min-width: 250px;
        }}
        .profile-box {{
            margin: 0.85rem 0 1rem;
            padding: 0.85rem 0.9rem;
            border-radius: 16px;
            background: {palette["surface"]};
            border: 1px solid {palette["surface_border"]};
        }}
        .profile-avatar {{
            width: 3rem;
            height: 3rem;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: {palette["default_bg"]};
            color: {palette["value"]};
            font-size: 1rem;
            font-weight: 700;
            overflow: hidden;
            margin-bottom: 0.65rem;
        }}
        .profile-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .profile-name {{
            font-weight: 700;
            color: {palette["ink"]};
        }}
        .profile-title {{
            font-size: 0.8rem;
            color: {palette["helper"]};
            margin-top: 0.2rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="brand-row">{AURA_MARK}<div class="page-title">{title}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def auth_page(state: dict) -> bool:
    auth = state.setdefault("auth", {"username": "", "password_hash": "", "configured": False})
    shared_auth = shared_auth_from_secrets()
    local_auth = {
        "username": normalize_username(auth.get("username", "")),
        "password_hash": str(auth.get("password_hash", "")).strip(),
        "source": "local_state",
    }
    st.markdown(
        f'<div class="brand-row" style="margin-bottom:0.6rem;">{AURA_MARK}<div class="page-title">{APP_TITLE}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="page-subtitle">Private access for your personal finance dashboard.</div>', unsafe_allow_html=True)

    if not shared_auth and not auth.get("configured"):
        st.markdown("### Create Login")
        with st.form("setup_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Login")
            if submitted:
                if not username.strip() or not password:
                    st.error("Enter a username and password.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    auth["username"] = normalize_username(username)
                    auth["password_hash"] = hash_password(password)
                    auth["configured"] = True
                    save_state(state, immediate_remote=True)
                    st.session_state.logged_in = True
                    st.session_state["auth_verified"] = True
                    st.rerun()
        return False

    if st.session_state.get("logged_in") or st.session_state.get("auth_verified"):
        st.session_state.logged_in = True
        st.session_state["auth_verified"] = True
        return True

    st.markdown("### Sign In")
    if shared_auth:
        st.caption("Shared login is active. Use the same username and password on desktop and phone.")
        st.caption(f"Debug auth source: {shared_auth.get('source')} | username: {shared_auth.get('username')}")
        st.caption(f"Debug password hash prefix: {str(shared_auth.get('password_hash', ''))[:8]}")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")
        if submitted:
            normalized_input = normalize_username(username)
            candidate_passwords = []
            for candidate in [password, password.strip()]:
                if candidate not in candidate_passwords:
                    candidate_passwords.append(candidate)
            candidate_hashes = {hash_password(candidate) for candidate in candidate_passwords}
            shared_match = bool(
                shared_auth
                and normalized_input == shared_auth.get("username")
                and shared_auth.get("password_hash") in candidate_hashes
            )
            local_match = bool(
                local_auth.get("username")
                and normalized_input == local_auth.get("username")
                and local_auth.get("password_hash") in candidate_hashes
            )
            if shared_match or local_match:
                st.session_state.logged_in = True
                st.session_state["auth_verified"] = True
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Incorrect username or password.")
                st.caption(f"Debug entered hash prefix: {hash_password(password.strip())[:8]}")
    return False


@st.fragment(run_every="60s")
def rollover_watch(state: dict) -> None:
    if process_rollovers(state):
        save_state(state, immediate_remote=True)
        st.rerun()
    st.empty()


@st.fragment(run_every="3s")
def debounced_sync_watch(state: dict) -> None:
    flush_remote_save_if_due(state)
    st.empty()


def live_sync_watch() -> None:
    return


def dashboard_page(state: dict) -> None:
    render_header("Aura Finance", "A calm command center for your money, budgets, debt, and leftover cash flow.")
    accounts = state["accounts"]
    sync_live_widget_values(state)
    edit_left, edit_right = st.columns([14, 1])
    with edit_left:
        st.empty()
    with edit_right:
        st.markdown('<div class="quick-edit-anchor">', unsafe_allow_html=True)
        with st.popover("✎"):
            st.markdown('<div class="quick-edit-panel">', unsafe_allow_html=True)
            st.caption("Quick Edit")
            checking_text = st.text_input(
                "Checking",
                value=str(int(accounts["checking"])) if float(accounts["checking"]).is_integer() else str(accounts["checking"]),
                key="quick_edit_checking_text",
            )
            savings_text = st.text_input(
                "Savings",
                value=str(int(accounts["savings"])) if float(accounts["savings"]).is_integer() else str(accounts["savings"]),
                key="quick_edit_savings_text",
            )
            retirement_text = st.text_input(
                "Retirement Fund",
                value=str(int(accounts["retirement"])) if float(accounts["retirement"]).is_integer() else str(accounts["retirement"]),
                key="quick_edit_retirement_text",
            )
            accounts["checking"] = parse_money_input(checking_text, float(accounts["checking"]))
            accounts["savings"] = parse_money_input(savings_text, float(accounts["savings"]))
            accounts["retirement"] = parse_money_input(retirement_text, float(accounts["retirement"]))
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    monthly = monthly_metrics(state)
    weekly = weekly_metrics(state)
    net_worth = accounts["checking"] + accounts["savings"] + accounts["retirement"] - total_debt(state)
    next_due = next_bill_record(state)
    left_amount = leftover_balance(state)

    st.markdown('<div class="section-label">Wealth Snapshot</div>', unsafe_allow_html=True)
    top_group = st.columns(5)
    with top_group[0]:
        hero_card("Net Worth", money(net_worth), "good" if net_worth >= 0 else "danger")
    with top_group[1]:
        hero_card("Checking", money(accounts["checking"]))
    with top_group[2]:
        hero_card("Savings", money(accounts["savings"]))
    with top_group[3]:
        hero_card("Retirement", money(accounts["retirement"]))
    with top_group[4]:
        hero_card("Total Debt", money(total_debt(state)), "warn" if total_debt(state) > 0 else "default")

    main_col, slide_col = st.columns([4.2, 1.15], gap="large")

    with main_col:
        st.markdown('<div class="section-label">At A Glance</div>', unsafe_allow_html=True)
        row = st.columns(4)
        with row[0]:
            tone = "good" if monthly["left_after_budget_and_savings"] >= 0 else "danger"
            hero_card("Left To Spend", money(monthly["left_after_budget_and_savings"]), tone)
        with row[1]:
            soft_card("Leftover Money", money(left_amount), "Unused money rolls here automatically")
        with row[2]:
            soft_card("Total Money Spent", money(monthly["spent"] + weekly["spent"]), "Monthly plus weekly spending")
        with row[3]:
            next_text = f"{next_due['name']} on day {next_due['due_day']}" if next_due else "Nothing due soon"
            soft_card("Next Bill", money(next_due["amount"]) if next_due else money(0), next_text)

        row2 = st.columns(4)
        with row2[0]:
            soft_card("Weekly Budget", money(weekly["budgeted"]), week_label(week_key()))
        with row2[1]:
            helper = "Over limit" if weekly["spent"] > weekly["budgeted"] else "This week"
            soft_card("Weekly Spent", money(weekly["spent"]), helper)
        with row2[2]:
            soft_card("Monthly Budget", money(monthly["budgeted"]), datetime.now().strftime("%B %Y"))
        with row2[3]:
            helper = "Over limit" if monthly["spent"] > monthly["budgeted"] else "This month"
            soft_card("Monthly Spent", money(monthly["spent"]), helper)

        tab_stats, tab_recs, tab_bills = st.tabs(["Statistics", "Recommendations", "Upcoming Bills"])
        with tab_stats:
            charts = st.columns(2)
            monthly_df = pd.DataFrame(normalize_rows(state.get("monthly_budgets", []), weekly=False))
            with charts[0]:
                if not monthly_df.empty and monthly_df["budget"].sum() > 0:
                    fig = px.pie(monthly_df, names="name", values="budget", hole=0.62, title="Monthly Budget Mix")
                    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20), paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Add monthly budget categories to see the circle graph.")
            with charts[1]:
                wealth_df = pd.DataFrame(
                    [
                        {"name": "Checking", "value": accounts["checking"]},
                        {"name": "Savings", "value": accounts["savings"]},
                        {"name": "Retirement", "value": accounts["retirement"]},
                        {"name": "Debt", "value": max(total_debt(state), 0.0)},
                    ]
                )
                positive = wealth_df[wealth_df["value"] > 0]
                if not positive.empty:
                    fig = px.pie(positive, names="name", values="value", hole=0.62, title="Account and Debt View")
                    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20), paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Add account balances to see your net worth breakdown.")

        with tab_recs:
            for note in recommendation_lines(state):
                st.markdown(f'<div class="mini-line"><div class="line-title">{note}</div></div>', unsafe_allow_html=True)

        with tab_bills:
            bills = pd.DataFrame(normalize_rows(state.get("monthly_budgets", []), weekly=False))
            if not bills.empty:
                bills = bills.sort_values(by="bill_day").rename(columns={"name": "Category", "budget": "Amount", "bill_day": "Due Day"})
                st.dataframe(bills[["Category", "Amount", "Due Day"]], use_container_width=True, hide_index=True)
            else:
                st.info("No monthly bills yet.")

    with slide_col:
        st.markdown('<div class="section-label">Left Slide Panel</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-panel"><div class="panel-title">Support Details</div>', unsafe_allow_html=True)
        st.markdown('<div class="line-title">Leftover Sources</div>', unsafe_allow_html=True)
        if state["leftover_ledger"]:
            for item in state["leftover_ledger"][:6]:
                st.markdown(f'<div class="mini-line"><div class="line-title">{item["source"]}</div><div class="line-helper">{money(item["amount"])} - {item["period"]}</div></div>', unsafe_allow_html=True)
        else:
            st.caption("Unused money and extra room will appear here.")

        st.markdown('<div class="line-title" style="margin-top:1rem;">Notifications</div>', unsafe_allow_html=True)
        for note in notification_messages(state) or ["No urgent notifications right now."]:
            st.markdown(f'<span class="warning-pill">{note}</span>', unsafe_allow_html=True)

        st.markdown('<div class="line-title" style="margin-top:1rem;">Debt Categories</div>', unsafe_allow_html=True)
        debts = normalize_debts(state.get("debts", []))
        if debts:
            for debt in debts[:5]:
                st.markdown(f'<div class="mini-line"><div class="line-title">{debt["name"]}</div><div class="line-helper">{money(debt["balance"])} balance - due day {debt["due_day"]}</div></div>', unsafe_allow_html=True)
        else:
            st.caption("No debt categories yet.")
        st.markdown("</div>", unsafe_allow_html=True)


def accounts_editor(state: dict) -> None:
    st.subheader("Money Setup")
    left, right = st.columns(2)
    with left:
        state["accounts"]["monthly_income"] = st.number_input("Monthly Income", min_value=0.0, value=float(state["accounts"]["monthly_income"]), step=50.0)
        state["accounts"]["checking"] = st.number_input("Checking Account", min_value=0.0, value=float(state["accounts"]["checking"]), step=50.0)
        state["accounts"]["savings"] = st.number_input("Savings", min_value=0.0, value=float(state["accounts"]["savings"]), step=50.0)
    with right:
        state["accounts"]["retirement"] = st.number_input("Retirement Fund", min_value=0.0, value=float(state["accounts"]["retirement"]), step=50.0)
        state["accounts"]["monthly_savings_goal"] = st.number_input("Monthly Savings Goal", min_value=0.0, value=float(state["accounts"]["monthly_savings_goal"]), step=50.0)


def monthly_page(state: dict) -> None:
    render_header("Monthly Budget", "Track bill days, monthly spending, emergency expenses, and leftover transfers.")
    accounts_editor(state)
    sync_live_widget_values(state)
    st.divider()

    metrics = monthly_metrics(state)
    summary = st.columns(4)
    with summary[0]:
        hero_card("Monthly Income", money(metrics["income"]))
    with summary[1]:
        hero_card("Savings Goal", money(metrics["savings_goal"]))
    with summary[2]:
        soft_card("Monthly Budgeted", money(metrics["budgeted"]), datetime.now().strftime("%B %Y"))
    with summary[3]:
        tone = "good" if metrics["left_after_budget_and_savings"] >= 0 else "danger"
        hero_card("Left After Plan", money(metrics["left_after_budget_and_savings"]), tone)

    add_col, list_col = st.columns([1, 2], gap="large")
    with add_col:
        st.subheader("Add Monthly Category")
        with st.form("add_monthly"):
            name = st.text_input("Category Name")
            budget = st.number_input("Budget Amount", min_value=0.0, step=25.0)
            bill_day = st.number_input("Bill Day", min_value=1, max_value=31, step=1, value=1)
            submitted = st.form_submit_button("Add Category")
            if submitted and name.strip():
                state["monthly_budgets"].append({"name": name.strip(), "budget": budget, "spent": 0.0, "bill_day": int(bill_day)})
                save_state(state, immediate_remote=True)
                st.rerun()

    with list_col:
        st.subheader("Monthly Categories")
        rows = normalize_rows(state.get("monthly_budgets", []), weekly=False)
        if not rows:
            st.info("Add a monthly category to begin.")
        for idx, row in enumerate(rows):
            with st.expander(f"{row['name']} - budget {money(row['budget'])}", expanded=True):
                c1, c2, c3, c4, c5 = st.columns([1.3, 1, 1, 1, 0.8])
                state["monthly_budgets"][idx]["name"] = c1.text_input("Name", value=row["name"], key=f"m_name_{idx}")
                state["monthly_budgets"][idx]["budget"] = c2.number_input("Budget", min_value=0.0, value=float(row["budget"]), step=25.0, key=f"m_budget_{idx}")
                state["monthly_budgets"][idx]["spent"] = c3.number_input("Spent", min_value=0.0, value=float(row["spent"]), step=10.0, key=f"m_spent_{idx}")
                state["monthly_budgets"][idx]["bill_day"] = c4.number_input("Bill Day", min_value=1, max_value=31, value=int(row["bill_day"]), step=1, key=f"m_bill_{idx}")
                if c5.button("Delete", key=f"m_delete_{idx}", use_container_width=True):
                    state["monthly_budgets"].pop(idx)
                    save_state(state, immediate_remote=True)
                    st.rerun()
                left = row["budget"] - row["spent"]
                if left >= 0:
                    st.markdown(f'<span class="good-pill">Budget Left: {money(left)}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="warning-pill">Over Budget: {money(abs(left))}</span>', unsafe_allow_html=True)

        table = monthly_budget_table(state)
        if not table.empty:
            st.markdown("#### Monthly Summary")
            st.dataframe(table, use_container_width=True, hide_index=True)

        recent_leftover = pd.DataFrame(
            [item for item in state.get("leftover_ledger", []) if item.get("kind") in {"monthly_leftover", "income_leftover"}][:8]
        )
        if not recent_leftover.empty:
            st.markdown("#### Recent Monthly Leftover Transfers")
            st.dataframe(recent_leftover, use_container_width=True, hide_index=True)


def weekly_page(state: dict) -> None:
    render_header("Weekly Budget", "Only your weekly budget and weekly insights live here.")
    st.caption(f"Current week: {week_label(week_key())}")
    sync_live_widget_values(state)
    metrics = weekly_metrics(state)
    summary = st.columns(3)
    with summary[0]:
        hero_card("Weekly Budget", money(metrics["budgeted"]))
    with summary[1]:
        tone = "warn" if metrics["spent"] > metrics["budgeted"] else "default"
        hero_card("Weekly Spent", money(metrics["spent"]), tone)
    with summary[2]:
        tone = "good" if metrics["left"] >= 0 else "danger"
        hero_card("Weekly Left", money(metrics["left"]), tone)
    add_col, list_col = st.columns([1, 2], gap="large")
    with add_col:
        st.subheader("Add Weekly Category")
        with st.form("add_weekly"):
            name = st.text_input("Weekly Category Name")
            budget = st.number_input("Weekly Budget Amount", min_value=0.0, step=25.0)
            submitted = st.form_submit_button("Add Weekly Category")
            if submitted and name.strip():
                state["weekly_budgets"].append({"name": name.strip(), "budget": budget, "spent": 0.0})
                save_state(state, immediate_remote=True)
                st.rerun()

    with list_col:
        st.subheader("Weekly Categories")
        rows = normalize_rows(state.get("weekly_budgets", []), weekly=True)
        if not rows:
            st.info("Add a weekly category to begin.")
        for idx, row in enumerate(rows):
            with st.expander(f"{row['name']} - budget {money(row['budget'])}", expanded=True):
                c1, c2, c3, c4 = st.columns([1.6, 1, 1, 0.8])
                state["weekly_budgets"][idx]["name"] = c1.text_input("Name", value=row["name"], key=f"w_name_{idx}")
                state["weekly_budgets"][idx]["budget"] = c2.number_input("Budget", min_value=0.0, value=float(row["budget"]), step=25.0, key=f"w_budget_{idx}")
                state["weekly_budgets"][idx]["spent"] = c3.number_input("Spent", min_value=0.0, value=float(row["spent"]), step=10.0, key=f"w_spent_{idx}")
                if c4.button("Delete", key=f"w_delete_{idx}", use_container_width=True):
                    state["weekly_budgets"].pop(idx)
                    save_state(state, immediate_remote=True)
                    st.rerun()
                left = row["budget"] - row["spent"]
                if left >= 0:
                    st.markdown(f'<span class="good-pill">Budget Left: {money(left)}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="warning-pill">Over Budget: {money(abs(left))}</span>', unsafe_allow_html=True)

        table = weekly_budget_table(state)
        if not table.empty:
            insight_left, insight_right = st.columns(2)
            with insight_left:
                st.markdown("#### Weekly Insights")
                over_rows = table[table["Left"] < 0]
                if not over_rows.empty:
                    for _, over in over_rows.iterrows():
                        st.markdown(
                            f'<span class="warning-pill">{over["Category"]} is over by {money(abs(float(over["Left"])))}</span>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown('<span class="good-pill">All weekly categories are on track.</span>', unsafe_allow_html=True)
                if metrics["left"] >= 0:
                    st.markdown(
                        f'<div class="mini-line"><div class="line-title">{money(metrics["left"])} is still available this week.</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="mini-line"><div class="line-title">Weekly spending is over plan by {money(abs(metrics["left"]))}.</div></div>',
                        unsafe_allow_html=True,
                    )
            with insight_right:
                st.markdown("#### Weekly Budget")
                st.dataframe(table, use_container_width=True, hide_index=True)


def debt_page(state: dict) -> None:
    render_header("Debt", "Track debt categories, due days, and total balances in one place.")
    sync_live_widget_values(state)
    debts = normalize_debts(state.get("debts", []))
    due_debt = min(debts, key=lambda item: item["due_day"]) if debts else None
    summary = st.columns(3)
    with summary[0]:
        hero_card("Total Debt", money(total_debt(state)), "warn" if total_debt(state) > 0 else "default")
    with summary[1]:
        soft_card("Debt Categories", str(len(debts)), "Active tracked debts")
    with summary[2]:
        helper = f"Due day {due_debt['due_day']}" if due_debt else "No debt payments yet"
        soft_card("Next Debt Payment", money(due_debt["payment"]) if due_debt else money(0), helper)

    add_col, list_col = st.columns([1, 2], gap="large")
    with add_col:
        st.subheader("Add Debt Category")
        with st.form("add_debt"):
            name = st.text_input("Debt Name")
            balance = st.number_input("Balance", min_value=0.0, step=25.0)
            payment = st.number_input("Payment Amount", min_value=0.0, step=25.0)
            due_day = st.number_input("Due Day", min_value=1, max_value=31, step=1, value=1)
            submitted = st.form_submit_button("Add Debt")
            if submitted and name.strip():
                state["debts"].append({"name": name.strip(), "balance": balance, "payment": payment, "due_day": int(due_day)})
                save_state(state, immediate_remote=True)
                st.rerun()

    with list_col:
        st.subheader("Debt Categories")
        debts = normalize_debts(state.get("debts", []))
        if not debts:
            st.info("Add a debt category to begin.")
        for idx, row in enumerate(debts):
            with st.expander(f"{row['name']} - balance {money(row['balance'])}", expanded=True):
                c1, c2, c3, c4, c5 = st.columns([1.4, 1, 1, 1, 0.8])
                state["debts"][idx]["name"] = c1.text_input("Name", value=row["name"], key=f"d_name_{idx}")
                state["debts"][idx]["balance"] = c2.number_input("Balance", min_value=0.0, value=float(row["balance"]), step=25.0, key=f"d_balance_{idx}")
                state["debts"][idx]["payment"] = c3.number_input("Payment", min_value=0.0, value=float(row["payment"]), step=25.0, key=f"d_payment_{idx}")
                state["debts"][idx]["due_day"] = c4.number_input("Due Day", min_value=1, max_value=31, value=int(row["due_day"]), step=1, key=f"d_due_{idx}")
                if c5.button("Delete", key=f"d_delete_{idx}", use_container_width=True):
                    state["debts"].pop(idx)
                    save_state(state, immediate_remote=True)
                    st.rerun()

        if debts:
            debt_df = pd.DataFrame(debts).rename(
                columns={"name": "Debt", "balance": "Balance", "payment": "Payment", "due_day": "Due Day"}
            )
            st.markdown("#### Debt Summary")
            st.dataframe(debt_df, use_container_width=True, hide_index=True)


def insights_page(state: dict) -> None:
    render_header("Insights & History", "See saved versus overspent periods, leftover transfers, and monthly financial patterns.")
    monthly = monthly_metrics(state)
    weekly = weekly_metrics(state)
    top = st.columns(3)
    with top[0]:
        hero_card("This Month", money(monthly["spent"]), "warn" if monthly["spent"] > monthly["budgeted"] else "good")
    with top[1]:
        hero_card("This Week", money(weekly["spent"]), "warn" if weekly["spent"] > weekly["budgeted"] else "good")
    with top[2]:
        hero_card("Leftover Balance", money(leftover_balance(state)))

    tabs = st.tabs(["Monthly History", "Weekly History", "Leftover Ledger"])
    with tabs[0]:
        history = pd.DataFrame(state.get("monthly_history", []))
        if history.empty:
            st.info("Monthly history will appear after your first rollover.")
        else:
            history["month"] = history["month"].astype(str)
            st.dataframe(history, use_container_width=True, hide_index=True)

    with tabs[1]:
        history = pd.DataFrame(state.get("weekly_history", []))
        if history.empty:
            st.info("Weekly history will appear after your first Sunday rollover.")
        else:
            history["week"] = history["week"].apply(week_label)
            st.dataframe(history, use_container_width=True, hide_index=True)

    with tabs[2]:
        ledger = pd.DataFrame(state.get("leftover_ledger", []))
        if ledger.empty:
            st.info("Unused monthly or weekly money will show up here.")
        else:
            ledger = ledger.rename(columns={"date": "Date", "source": "Source", "amount": "Amount", "kind": "Type", "period": "Period"})
            st.dataframe(ledger, use_container_width=True, hide_index=True)


def main() -> None:
    pages = ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt", "Insights & History"]
    state = load_state()
    state["monthly_budgets"] = normalize_rows(state.get("monthly_budgets", []), weekly=False)
    state["weekly_budgets"] = normalize_rows(state.get("weekly_budgets", []), weekly=True)
    state["debts"] = normalize_debts(state.get("debts", []))
    process_rollovers(state)

    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Dark"
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "auth_verified" not in st.session_state:
        st.session_state["auth_verified"] = False
    apply_theme(st.session_state.theme_mode)

    if not auth_page(state):
        save_state(state, immediate_remote=True)
        return

    rollover_watch(state)
    debounced_sync_watch(state)
    live_sync_watch()

    with st.sidebar:
        st.markdown(f'<div class="brand-row">{AURA_MARK}<div style="font-size:1.3rem;font-weight:700;">Aura</div></div>', unsafe_allow_html=True)
        profile = state.setdefault("profile", {"name": "Your Name", "title": "Personal Finance Owner", "photo": ""})
        with st.expander("Edit Profile"):
            profile["name"] = st.text_input("Name", value=profile.get("name", "Your Name"), key="profile_name")
            profile["title"] = st.text_input("Title", value=profile.get("title", "Personal Finance Owner"), key="profile_title")
            profile["photo"] = st.text_input("Photo URL", value=profile.get("photo", ""), key="profile_photo")
            uploaded_photo = st.file_uploader("Upload Photo", type=["png", "jpg", "jpeg", "webp"], key="profile_photo_upload")
            if uploaded_photo is not None:
                profile["photo"] = uploaded_file_to_data_url(uploaded_photo)
        st.markdown('<div class="profile-box">', unsafe_allow_html=True)
        if profile.get("photo"):
            st.image(profile["photo"], width=56)
        else:
            st.markdown(
                f'<div class="profile-avatar">{profile.get("name", "Y")[:2].upper()}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="profile-name">{profile.get("name","Your Name")}</div><div class="profile-title">{profile.get("title","Personal Finance Owner")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        theme_mode = st.selectbox("Theme", ["Light", "Dark"], index=0 if st.session_state.theme_mode == "Light" else 1)
        if theme_mode != st.session_state.theme_mode:
            st.session_state.theme_mode = theme_mode
            st.rerun()
        st.radio(
            "Navigation",
            pages,
            index=pages.index(st.session_state.page),
            key="page",
            label_visibility="collapsed",
        )
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state["auth_verified"] = False
            for key in ["login_username", "login_password"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        st.caption("Luxury personal finance, organized around what matters most.")

    page = st.session_state.page
    st.caption(f"Current page debug: {page}")

    if page == "Dashboard":
        dashboard_page(state)
    elif page == "Monthly Budget":
        monthly_page(state)
    elif page == "Weekly Budget":
        weekly_page(state)
    elif page == "Debt":
        debt_page(state)
    else:
        insights_page(state)

    save_state(state)


if __name__ == "__main__":
    main()
