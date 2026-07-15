/**
 * Browser-side Apollo credit snapshot builder.
 * Calls Apollo through a same-origin proxy (preferred) or directly.
 */
(function (global) {
  var APOLLO_BASE = "https://api.apollo.io/api/v1";
  var STORAGE_KEY = "it.apollo.apiKey";
  var PROXY_STORAGE_KEY = "it.apollo.proxyUrl";

  var CREDIT_LABELS = {
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

  function getApiKey() {
    try {
      return (localStorage.getItem(STORAGE_KEY) || "").trim();
    } catch (e) {
      return "";
    }
  }

  function setApiKey(value) {
    var key = String(value || "").trim();
    try {
      if (key) localStorage.setItem(STORAGE_KEY, key);
      else localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      /* ignore quota / private mode */
    }
    return key;
  }

  function clearApiKey() {
    setApiKey("");
  }

  function maskApiKey(key) {
    if (!key) return "";
    if (key.length <= 8) return "••••••••";
    return key.slice(0, 4) + "••••" + key.slice(-4);
  }

  function getProxyUrl() {
    try {
      var stored = (localStorage.getItem(PROXY_STORAGE_KEY) || "").trim();
      if (stored) return stored.replace(/\/+$/, "");
    } catch (e) {
      /* ignore */
    }
    return "/it/api/apollo";
  }

  function statusForRemaining(left, limit) {
    if (!limit) return "muted";
    var pct = left / limit;
    if (left <= 0) return "bad";
    if (pct <= 0.2) return "warn";
    return "good";
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
    return Object.keys(stats || {}).map(function (key) {
      var bucket = stats[key] || {};
      var limit = Number(bucket.limit || 0);
      var consumed = Number(bucket.consumed || 0);
      var left =
        bucket.left_over != null
          ? Number(bucket.left_over)
          : Math.max(limit - consumed, 0);
      var unifiedDial = usingUnifiedCredits && key === "direct_dial_credit";
      return {
        key: key,
        label: unifiedDial
          ? (CREDIT_LABELS[key] || key) + " (via unified lead pool)"
          : CREDIT_LABELS[key] || key.replace(/_/g, " "),
        limit: limit,
        consumed: consumed,
        left_over: left,
        status: unifiedDial
          ? "muted"
          : limit
            ? statusForRemaining(left, limit)
            : "muted"
      };
    });
  }

  async function apolloRequestDirect(apiKey, method, path, body) {
    var res = await fetch(APOLLO_BASE + path, {
      method: method,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": apiKey
      },
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    var text = await res.text();
    var data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      data = { raw: text };
    }
    if (!res.ok) {
      throw new Error("Apollo " + method + " " + path + ": " + res.status + " " + text);
    }
    return data;
  }

  async function buildApolloSnapshot(apiKey, requestFn) {
    var call = requestFn || apolloRequestDirect.bind(null, apiKey);
    var today = new Date();
    var maxDate = today.toISOString().slice(0, 10);
    var minDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);

    var profile = await call(
      "GET",
      "/users/api_profile?include_credit_usage=true"
    );
    var usage = await call("POST", "/usage_stats/credit_usage_stats", {});
    var usersPayload = await call("GET", "/users/search?per_page=100");
    var teamPayload = profile.team_id
      ? await call("GET", "/teams/" + profile.team_id)
      : { team: {} };

    var detailedUsers = [];
    var users = usersPayload.users || [];
    for (var i = 0; i < users.length; i++) {
      var user = users[i];
      if (!user.id) continue;
      try {
        var detail = await call("GET", "/users/" + user.id);
        detailedUsers.push(simplifyUser(detail.user || user));
      } catch (e) {
        detailedUsers.push(simplifyUser(user));
      }
    }

    var historyQs =
      "page=1&per_page=100&min_date=" +
      encodeURIComponent(minDate) +
      "&max_date=" +
      encodeURIComponent(maxDate) +
      "&include_refunds=true";
    var history;
    try {
      history = await call("POST", "/data_requests/search?" + historyQs, {});
    } catch (e) {
      history = {
        pagination: {
          page: 1,
          per_page: 100,
          total_entries: 0,
          total_pages: 0
        },
        data_requests: [],
        error: String(e.message || e)
      };
    }

    var creditStats = usage.credit_usage_stats || {};
    var team = teamPayload.team || {};
    var creditRows = buildCreditRows(
      creditStats,
      !!team.using_unified_credits
    );
    var lead = creditRows.filter(function (r) {
      return r.key === "lead_credit";
    })[0];
    var cycle = usage.current_credit_cycle || {};

    var kpi;
    if (lead) {
      kpi = {
        label: "Lead credits remaining",
        value: lead.left_over,
        limit: lead.limit,
        consumed: lead.consumed,
        unit: "credits",
        status: lead.status,
        display:
          Number(lead.left_over).toLocaleString() +
          " / " +
          Number(lead.limit).toLocaleString()
      };
    } else {
      var remaining = Number(profile.num_credits_remaining || 0);
      var limit = Number(profile.effective_num_lead_credits || remaining);
      kpi = {
        label: "Lead credits remaining",
        value: remaining,
        limit: limit,
        consumed: Number(profile.num_lead_credits_used || 0),
        unit: "credits",
        status: statusForRemaining(remaining, limit),
        display: remaining.toLocaleString() + " / " + limit.toLocaleString()
      };
    }

    return {
      id: "apollo",
      name: "Apollo.io",
      fetched_at: new Date().toISOString(),
      kpi: kpi,
      cycle: cycle,
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
        apollo_history:
          "https://app.apollo.io/#/settings/credits/history?minDate=" +
          minDate +
          "&maxDate=" +
          maxDate +
          "&datePreset=last_90_days&includeRefunds=yes",
        apollo_credits: "https://app.apollo.io/#/settings/credits/plans",
        detail: "/it/apollo/"
      }
    };
  }

  function toSaasCard(apollo) {
    return {
      updated_at: apollo.fetched_at,
      services: [
        {
          id: apollo.id,
          name: apollo.name,
          href: apollo.links.detail,
          kpi_label: apollo.kpi.label,
          kpi_display: apollo.kpi.display,
          status: apollo.kpi.status,
          detail: apollo.cycle && apollo.cycle.end_date
            ? "Cycle through " + String(apollo.cycle.end_date).slice(0, 10)
            : "Credit usage"
        }
      ]
    };
  }

  async function fetchViaProxy(apiKey) {
    var proxyUrl = getProxyUrl();
    var res = await fetch(proxyUrl, {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": apiKey
      },
      body: JSON.stringify({ apiKey: apiKey })
    });
    var text = await res.text();
    var data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error("Proxy returned non-JSON (" + res.status + ")");
    }
    if (!res.ok) {
      throw new Error(data.error || "Proxy error " + res.status);
    }
    return data;
  }

  async function fetchLiveApollo(apiKey) {
    // Prefer same-origin / Worker proxy (bypasses Apollo CORS).
    try {
      return await fetchViaProxy(apiKey);
    } catch (proxyErr) {
      try {
        return await buildApolloSnapshot(apiKey);
      } catch (directErr) {
        var msg =
          "Could not refresh Apollo live. " +
          (proxyErr && proxyErr.message ? proxyErr.message : "Proxy unavailable") +
          ". Direct call: " +
          (directErr && directErr.message ? directErr.message : String(directErr));
        throw new Error(msg);
      }
    }
  }

  global.ItApollo = {
    STORAGE_KEY: STORAGE_KEY,
    getApiKey: getApiKey,
    setApiKey: setApiKey,
    clearApiKey: clearApiKey,
    maskApiKey: maskApiKey,
    getProxyUrl: getProxyUrl,
    fetchLiveApollo: fetchLiveApollo,
    toSaasCard: toSaasCard,
    buildApolloSnapshot: buildApolloSnapshot
  };
})(window);
