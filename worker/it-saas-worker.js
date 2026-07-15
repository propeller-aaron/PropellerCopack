/**
 * Cloudflare Worker: proxy Apollo credit data for the /it SAAS dashboard.
 *
 * API key resolution (first match wins):
 *   1. Request header X-Api-Key (from the /it module UI)
 *   2. JSON body { apiKey } or { api_key } on POST
 *   3. Worker binding APOLLO_API_KEY (optional fallback)
 *
 * Routes:
 *   GET  /              health
 *   GET|/POST /apollo   full Apollo snapshot
 *   GET|/POST /saas     SAAS card list
 *   OPTIONS /*          CORS preflight
 */

const APOLLO_BASE = "https://api.apollo.io/api/v1";

const CREDIT_LABELS = {
  lead_credit: "Lead / email credits",
  direct_dial_credit: "Mobile / direct dial credits",
  export_credit: "Export credits",
  conversation_credit: "Conversation credits",
  ai_credit: "AI credits",
  power_up_credit: "Power-up credits",
  inbound_website_visitor_credit: "Inbound website visitor credits",
  dialer: "Dialer minutes",
  web_search_record_credit: "Web search record credits",
  contact_website_visitor_credit: "Contact website visitor credits"
};

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Api-Key"
  };
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      ...corsHeaders()
    }
  });
}

function statusForRemaining(left, limit) {
  if (!limit) return "muted";
  const pct = left / limit;
  if (left <= 0) return "bad";
  if (pct <= 0.2) return "warn";
  return "good";
}

async function apolloRequest(apiKey, method, path, body) {
  const res = await fetch(`${APOLLO_BASE}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Cache-Control": "no-cache",
      "X-Api-Key": apiKey
    },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    throw new Error(`Apollo ${method} ${path}: ${res.status} ${text}`);
  }
  return data;
}

function simplifyUser(user) {
  return {
    id: user.id,
    name:
      user.name ||
      [user.first_name, user.last_name].filter(Boolean).join(" ") ||
      user.email,
    email: user.email,
    credit_limit: user.credit_limit,
    direct_dial_credit_limit: user.direct_dial_credit_limit,
    export_credit_limit: user.export_credit_limit,
    ai_credit_limit: user.ai_credit_limit,
    num_credits_remaining: user.num_credits_remaining,
    effective_num_lead_credits: user.effective_num_lead_credits,
    num_lead_credits_used: user.num_lead_credits_used,
    effective_num_direct_dial_credits: user.effective_num_direct_dial_credits,
    num_direct_dial_credits_used: user.num_direct_dial_credits_used,
    effective_num_export_credits: user.effective_num_export_credits,
    num_export_credits_used: user.num_export_credits_used,
    effective_num_ai_credits: user.effective_num_ai_credits,
    num_ai_credits_used: user.num_ai_credits_used,
    total_unified_credits_used: user.total_unified_credits_used
  };
}

function buildCreditRows(stats, usingUnifiedCredits) {
  return Object.entries(stats || {}).map(([key, bucket]) => {
    const limit = Number(bucket.limit || 0);
    const consumed = Number(bucket.consumed || 0);
    const left =
      bucket.left_over != null ? Number(bucket.left_over) : Math.max(limit - consumed, 0);
    const unifiedDial = usingUnifiedCredits && key === "direct_dial_credit";
    return {
      key,
      label: unifiedDial
        ? `${CREDIT_LABELS[key] || key} (via unified lead pool)`
        : CREDIT_LABELS[key] || key.replace(/_/g, " "),
      limit,
      consumed,
      left_over: left,
      status: unifiedDial ? "muted" : limit ? statusForRemaining(left, limit) : "muted"
    };
  });
}

async function buildApolloSnapshot(apiKey) {
  const today = new Date();
  const maxDate = today.toISOString().slice(0, 10);
  const minDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10);

  const profile = await apolloRequest(
    apiKey,
    "GET",
    "/users/api_profile?include_credit_usage=true"
  );
  const usage = await apolloRequest(apiKey, "POST", "/usage_stats/credit_usage_stats", {});
  const usersPayload = await apolloRequest(apiKey, "GET", "/users/search?per_page=100");
  const teamPayload = profile.team_id
    ? await apolloRequest(apiKey, "GET", `/teams/${profile.team_id}`)
    : { team: {} };

  const detailedUsers = [];
  for (const user of usersPayload.users || []) {
    if (!user.id) continue;
    try {
      const detail = await apolloRequest(apiKey, "GET", `/users/${user.id}`);
      detailedUsers.push(simplifyUser(detail.user || user));
    } catch {
      detailedUsers.push(simplifyUser(user));
    }
  }

  const historyQs = new URLSearchParams({
    page: "1",
    per_page: "100",
    min_date: minDate,
    max_date: maxDate,
    include_refunds: "true"
  });
  const history = await apolloRequest(
    apiKey,
    "POST",
    `/data_requests/search?${historyQs}`,
    {}
  );

  const creditStats = usage.credit_usage_stats || {};
  const team = teamPayload.team || {};
  const creditRows = buildCreditRows(creditStats, !!team.using_unified_credits);
  const lead = creditRows.find((r) => r.key === "lead_credit");
  const cycle = usage.current_credit_cycle || {};

  const kpi = lead
    ? {
        label: "Lead credits remaining",
        value: lead.left_over,
        limit: lead.limit,
        consumed: lead.consumed,
        unit: "credits",
        status: lead.status,
        display: `${lead.left_over.toLocaleString()} / ${lead.limit.toLocaleString()}`
      }
    : {
        label: "Lead credits remaining",
        value: profile.num_credits_remaining || 0,
        limit: profile.effective_num_lead_credits || 0,
        consumed: profile.num_lead_credits_used || 0,
        unit: "credits",
        status: statusForRemaining(
          profile.num_credits_remaining || 0,
          profile.effective_num_lead_credits || 0
        ),
        display: `${Number(profile.num_credits_remaining || 0).toLocaleString()} / ${Number(
          profile.effective_num_lead_credits || 0
        ).toLocaleString()}`
      };

  return {
    id: "apollo",
    name: "Apollo.io",
    fetched_at: new Date().toISOString(),
    kpi,
    cycle,
    credits: creditRows,
    credit_usage_stats: creditStats,
    profile: {
      id: profile.id,
      name: [profile.first_name, profile.last_name].filter(Boolean).join(" "),
      email: profile.email,
      team_id: profile.team_id,
      num_credits_remaining: profile.num_credits_remaining,
      effective_num_lead_credits: profile.effective_num_lead_credits,
      num_lead_credits_used: profile.num_lead_credits_used,
      total_unified_credits_used: profile.total_unified_credits_used
    },
    team: {
      id: team.id,
      name: team.name,
      domain: team.domain,
      status: team.status,
      using_unified_credits: team.using_unified_credits,
      billing_cycle_price: team.billing_cycle_price,
      seats_limit: team.seats_limit,
      current_billing_cycle_start_date: team.current_billing_cycle_start_date,
      current_billing_cycle_end_date: team.current_billing_cycle_end_date,
      effective_num_lead_credits: team.effective_num_lead_credits,
      num_lead_credits_used: team.num_lead_credits_used,
      total_unified_credits_used: team.total_unified_credits_used,
      num_credits: team.num_credits,
      additional_email_credits: team.additional_email_credits
    },
    users: detailedUsers,
    history: {
      min_date: minDate,
      max_date: maxDate,
      pagination: history.pagination || {},
      data_requests: history.data_requests || []
    },
    links: {
      apollo_history: `https://app.apollo.io/#/settings/credits/history?minDate=${minDate}&maxDate=${maxDate}&datePreset=last_90_days&includeRefunds=yes`,
      apollo_credits: "https://app.apollo.io/#/settings/credits/plans",
      detail: "/it/apollo/"
    }
  };
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    if (request.method !== "GET" && request.method !== "POST") {
      return jsonResponse({ error: "Method not allowed." }, 405);
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (path === "/" || path === "") {
      return jsonResponse({ ok: true, service: "it-saas-worker" });
    }

    let body = {};
    if (request.method === "POST") {
      try {
        body = await request.json();
      } catch {
        body = {};
      }
    }

    const apiKey = (
      request.headers.get("X-Api-Key") ||
      body.apiKey ||
      body.api_key ||
      env.APOLLO_API_KEY ||
      ""
    ).trim();

    if (!apiKey) {
      return jsonResponse(
        {
          error:
            "API key required. Enter it in the /it module or set APOLLO_API_KEY on the Worker."
        },
        400
      );
    }

    try {
      if (path === "/apollo" || path.endsWith("/it/api/apollo")) {
        return jsonResponse(await buildApolloSnapshot(apiKey));
      }
      if (path === "/saas") {
        const apollo = await buildApolloSnapshot(apiKey);
        return jsonResponse({
          updated_at: apollo.fetched_at,
          services: [
            {
              id: apollo.id,
              name: apollo.name,
              href: apollo.links.detail,
              kpi_label: apollo.kpi.label,
              kpi_display: apollo.kpi.display,
              status: apollo.kpi.status,
              detail: apollo.cycle?.end_date
                ? `Cycle through ${String(apollo.cycle.end_date).slice(0, 10)}`
                : "Credit usage"
            }
          ]
        });
      }
      return jsonResponse({ error: "Not found." }, 404);
    } catch (err) {
      return jsonResponse({ error: String(err.message || err) }, 502);
    }
  }
};
