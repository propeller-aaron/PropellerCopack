"""Refresh /it SAAS status data (Apollo.io credit usage).

Reads APOLLO_API_KEY from the environment or a repo-root .env file.
Writes JSON snapshots under it/data/ for the static dashboard.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "it" / "data"
APOLLO_BASE = "https://api.apollo.io/api/v1"

CREDIT_LABELS = {
    "lead_credit": "Lead / email credits",
    "direct_dial_credit": "Mobile / direct dial credits",
    "export_credit": "Export credits",
    "conversation_credit": "Conversation credits",
    "ai_credit": "AI credits",
    "power_up_credit": "Power-up credits",
    "inbound_website_visitor_credit": "Inbound website visitor credits",
    "dialer": "Dialer minutes",
    "web_search_record_credit": "Web search record credits",
    "contact_website_visitor_credit": "Contact website visitor credits",
}


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def apollo_request(api_key: str, method: str, path: str, body: dict | None = None) -> dict:
    url = f"{APOLLO_BASE}{path}"
    data = None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Apollo {method} {path} failed: {exc.code} {detail}") from exc


def status_for_remaining(left: int, limit: int) -> str:
    if limit <= 0:
        return "muted"
    pct = left / limit
    if left <= 0:
        return "bad"
    if pct <= 0.2:
        return "warn"
    return "good"


def simplify_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "name": user.get("name")
        or " ".join(
            part for part in (user.get("first_name"), user.get("last_name")) if part
        ).strip()
        or user.get("email"),
        "email": user.get("email"),
        "credit_limit": user.get("credit_limit"),
        "direct_dial_credit_limit": user.get("direct_dial_credit_limit"),
        "export_credit_limit": user.get("export_credit_limit"),
        "ai_credit_limit": user.get("ai_credit_limit"),
        "num_credits_remaining": user.get("num_credits_remaining"),
        "effective_num_lead_credits": user.get("effective_num_lead_credits"),
        "num_lead_credits_used": user.get("num_lead_credits_used"),
        "effective_num_direct_dial_credits": user.get("effective_num_direct_dial_credits"),
        "num_direct_dial_credits_used": user.get("num_direct_dial_credits_used"),
        "effective_num_export_credits": user.get("effective_num_export_credits"),
        "num_export_credits_used": user.get("num_export_credits_used"),
        "effective_num_ai_credits": user.get("effective_num_ai_credits"),
        "num_ai_credits_used": user.get("num_ai_credits_used"),
        "total_unified_credits_used": user.get("total_unified_credits_used"),
    }


def build_credit_rows(stats: dict, *, using_unified_credits: bool = False) -> list[dict]:
    rows = []
    for key, bucket in stats.items():
        if not isinstance(bucket, dict):
            continue
        limit = int(bucket.get("limit") or 0)
        consumed = int(bucket.get("consumed") or 0)
        left = int(
            bucket.get("left_over")
            if bucket.get("left_over") is not None
            else max(limit - consumed, 0)
        )
        # Unified plans debit mobile reveals from the lead pool; the
        # direct_dial leftover field is not a useful KPI on its own.
        if using_unified_credits and key == "direct_dial_credit":
            status = "muted"
            label = CREDIT_LABELS.get(key, key) + " (via unified lead pool)"
        else:
            status = status_for_remaining(left, limit) if limit else "muted"
            label = CREDIT_LABELS.get(key, key.replace("_", " ").title())
        rows.append(
            {
                "key": key,
                "label": label,
                "limit": limit,
                "consumed": consumed,
                "left_over": left,
                "status": status,
            }
        )
    return rows


def fetch_apollo(api_key: str) -> dict:
    today = date.today()
    min_date = (today - timedelta(days=90)).isoformat()
    max_date = today.isoformat()

    profile = apollo_request(
        api_key, "GET", "/users/api_profile?include_credit_usage=true"
    )
    usage = apollo_request(api_key, "POST", "/usage_stats/credit_usage_stats", {})
    users_payload = apollo_request(api_key, "GET", "/users/search?per_page=100")
    team_id = profile.get("team_id")
    team_payload = (
        apollo_request(api_key, "GET", f"/teams/{team_id}") if team_id else {"team": {}}
    )

    detailed_users = []
    for user in users_payload.get("users") or []:
        uid = user.get("id")
        if not uid:
            continue
        try:
            detail = apollo_request(api_key, "GET", f"/users/{uid}")
            detailed_users.append(simplify_user(detail.get("user") or user))
        except RuntimeError:
            detailed_users.append(simplify_user(user))

    history_qs = urllib.parse.urlencode(
        {
            "page": 1,
            "per_page": 100,
            "min_date": min_date,
            "max_date": max_date,
            "include_refunds": "true",
        }
    )
    try:
        history = apollo_request(
            api_key, "POST", f"/data_requests/search?{history_qs}", {}
        )
    except RuntimeError as exc:
        # History endpoint is best-effort; balances still power the KPI dashboard.
        history = {
            "pagination": {"page": 1, "per_page": 100, "total_entries": 0, "total_pages": 0},
            "data_requests": [],
            "error": str(exc),
        }

    credit_stats = usage.get("credit_usage_stats") or {}
    team = team_payload.get("team") or {}
    credit_rows = build_credit_rows(
        credit_stats, using_unified_credits=bool(team.get("using_unified_credits"))
    )
    lead = next((row for row in credit_rows if row["key"] == "lead_credit"), None)
    cycle = usage.get("current_credit_cycle") or {}

    if lead:
        kpi = {
            "label": "Lead credits remaining",
            "value": lead["left_over"],
            "limit": lead["limit"],
            "consumed": lead["consumed"],
            "unit": "credits",
            "status": lead["status"],
            "display": f"{lead['left_over']:,} / {lead['limit']:,}",
        }
    else:
        remaining = int(profile.get("num_credits_remaining") or 0)
        limit = int(profile.get("effective_num_lead_credits") or remaining)
        consumed = int(profile.get("num_lead_credits_used") or 0)
        kpi = {
            "label": "Lead credits remaining",
            "value": remaining,
            "limit": limit,
            "consumed": consumed,
            "unit": "credits",
            "status": status_for_remaining(remaining, limit),
            "display": f"{remaining:,} / {limit:,}",
        }

    history_url = (
        "https://app.apollo.io/#/settings/credits/history"
        f"?minDate={min_date}&maxDate={max_date}&datePreset=last_90_days"
        "&includeRefunds=yes"
    )

    return {
        "id": "apollo",
        "name": "Apollo.io",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "kpi": kpi,
        "cycle": cycle,
        "credits": credit_rows,
        "credit_usage_stats": credit_stats,
        "profile": {
            "id": profile.get("id"),
            "name": " ".join(
                part
                for part in (profile.get("first_name"), profile.get("last_name"))
                if part
            ).strip(),
            "email": profile.get("email"),
            "team_id": profile.get("team_id"),
            "num_credits_remaining": profile.get("num_credits_remaining"),
            "effective_num_lead_credits": profile.get("effective_num_lead_credits"),
            "num_lead_credits_used": profile.get("num_lead_credits_used"),
            "total_unified_credits_used": profile.get("total_unified_credits_used"),
        },
        "team": {
            "id": team.get("id"),
            "name": team.get("name"),
            "domain": team.get("domain"),
            "status": team.get("status"),
            "using_unified_credits": team.get("using_unified_credits"),
            "billing_cycle_price": team.get("billing_cycle_price"),
            "seats_limit": team.get("seats_limit"),
            "current_billing_cycle_start_date": team.get(
                "current_billing_cycle_start_date"
            ),
            "current_billing_cycle_end_date": team.get("current_billing_cycle_end_date"),
            "effective_num_lead_credits": team.get("effective_num_lead_credits"),
            "num_lead_credits_used": team.get("num_lead_credits_used"),
            "total_unified_credits_used": team.get("total_unified_credits_used"),
            "num_credits": team.get("num_credits"),
            "additional_email_credits": team.get("additional_email_credits"),
        },
        "users": detailed_users,
        "history": {
            "min_date": min_date,
            "max_date": max_date,
            "pagination": history.get("pagination") or {},
            "data_requests": history.get("data_requests") or [],
        },
        "links": {
            "apollo_history": history_url,
            "apollo_credits": "https://app.apollo.io/#/settings/credits/plans",
            "detail": "/it/apollo/",
        },
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("APOLLO_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "APOLLO_API_KEY is required. Set it in the environment or in a .env file."
        )

    apollo = fetch_apollo(api_key)
    write_json(DATA_DIR / "apollo.json", apollo)

    saas = {
        "updated_at": apollo["fetched_at"],
        "services": [
            {
                "id": apollo["id"],
                "name": apollo["name"],
                "href": apollo["links"]["detail"],
                "kpi_label": apollo["kpi"]["label"],
                "kpi_display": apollo["kpi"]["display"],
                "status": apollo["kpi"]["status"],
                "detail": (
                    f"Cycle through {apollo['cycle'].get('end_date', 'n/a')[:10]}"
                    if apollo.get("cycle")
                    else "Credit usage"
                ),
            }
        ],
    }
    write_json(DATA_DIR / "saas.json", saas)
    print(f"Wrote {DATA_DIR / 'apollo.json'}")
    print(f"Wrote {DATA_DIR / 'saas.json'}")
    print(f"KPI: {apollo['kpi']['display']} ({apollo['kpi']['status']})")


if __name__ == "__main__":
    main()
