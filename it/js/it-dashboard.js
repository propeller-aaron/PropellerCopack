(function () {
  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function statusClass(status) {
    if (status === "good" || status === "warn" || status === "bad") return status;
    return "muted-status";
  }

  function formatNumber(value) {
    if (value == null || value === "") return "—";
    var n = Number(value);
    if (Number.isNaN(n)) return String(value);
    return n.toLocaleString();
  }

  function formatDate(value) {
    if (!value) return "—";
    var d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value).slice(0, 10);
    return d.toLocaleString();
  }

  function formatDay(value) {
    if (!value) return "—";
    return String(value).slice(0, 10);
  }

  async function fetchJson(url) {
    var res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to load " + url + " (" + res.status + ")");
    return res.json();
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderSaasCards(services, mount) {
    if (!services || !services.length) {
      mount.innerHTML = '<p class="muted">No SAAS services configured yet.</p>';
      return;
    }
    mount.innerHTML = services
      .map(function (s) {
        return (
          '<a class="saas-card" href="' +
          s.href +
          '">' +
          '<p class="name">' +
          escapeHtml(s.name) +
          ' <span class="status-pill ' +
          statusClass(s.status) +
          '">' +
          escapeHtml(s.status || "ok") +
          "</span></p>" +
          '<p class="kpi-label">' +
          escapeHtml(s.kpi_label || "KPI") +
          "</p>" +
          '<p class="kpi-value ' +
          statusClass(s.status) +
          '">' +
          escapeHtml(s.kpi_display || "—") +
          "</p>" +
          '<p class="detail">' +
          escapeHtml(s.detail || "") +
          "</p>" +
          '<p class="cta">View details →</p>' +
          "</a>"
        );
      })
      .join("");
  }

  function creditRowsHtml(rows) {
    if (!rows || !rows.length) {
      return '<p class="muted">No credit buckets returned.</p>';
    }
    var body = rows
      .map(function (row) {
        return (
          "<tr>" +
          "<td>" +
          escapeHtml(row.label) +
          "</td>" +
          '<td class="num">' +
          formatNumber(row.consumed) +
          "</td>" +
          '<td class="num">' +
          formatNumber(row.left_over) +
          "</td>" +
          '<td class="num">' +
          formatNumber(row.limit) +
          "</td>" +
          "<td><span class=\"status-pill " +
          statusClass(row.status) +
          '">' +
          escapeHtml(row.status) +
          "</span></td>" +
          "</tr>"
        );
      })
      .join("");
    return (
      "<table><thead><tr>" +
      "<th>Credit type</th><th class=\"num\">Used</th><th class=\"num\">Remaining</th>" +
      "<th class=\"num\">Limit</th><th>Status</th>" +
      "</tr></thead><tbody>" +
      body +
      "</tbody></table>"
    );
  }

  function usersHtml(users) {
    if (!users || !users.length) {
      return '<p class="muted">No team members found.</p>';
    }
    var body = users
      .map(function (u) {
        return (
          "<tr>" +
          "<td>" +
          escapeHtml(u.name) +
          "<div class=\"muted\">" +
          escapeHtml(u.email || "") +
          "</div></td>" +
          '<td class="num">' +
          formatNumber(u.num_lead_credits_used) +
          "</td>" +
          '<td class="num">' +
          formatNumber(u.num_credits_remaining) +
          "</td>" +
          '<td class="num">' +
          formatNumber(u.effective_num_lead_credits) +
          "</td>" +
          '<td class="num">' +
          formatNumber(u.num_direct_dial_credits_used) +
          "</td>" +
          '<td class="num">' +
          formatNumber(u.total_unified_credits_used) +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
    return (
      "<table><thead><tr>" +
      "<th>User</th><th class=\"num\">Lead used</th><th class=\"num\">Lead remaining</th>" +
      "<th class=\"num\">Lead limit</th><th class=\"num\">Mobile used</th>" +
      "<th class=\"num\">Unified used</th>" +
      "</tr></thead><tbody>" +
      body +
      "</tbody></table>"
    );
  }

  function historyHtml(history) {
    var rows = (history && history.data_requests) || [];
    if (!rows.length) {
      return (
        '<p class="muted">No credit usage events in the last 90 days via the Apollo API. ' +
        "If you expect history, open the Apollo UI link below — some ledger detail may only appear there.</p>"
      );
    }
    var body = rows
      .map(function (row) {
        return (
          "<tr>" +
          "<td>" +
          escapeHtml(formatDate(row.created_at || row.request_created_at || row.date)) +
          "</td>" +
          "<td>" +
          escapeHtml(row.feature || row.feature_name || row.type || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(row.action || row.action_name || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(row.description || row.note || "—") +
          "</td>" +
          '<td class="num">' +
          formatNumber(row.credits || row.num_credits || row.credit_delta) +
          "</td>" +
          "<td>" +
          escapeHtml(
            (row.user && (row.user.name || row.user.email)) ||
              row.user_name ||
              row.user_id ||
              "—"
          ) +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
    return (
      "<table><thead><tr>" +
      "<th>Date</th><th>Feature</th><th>Action</th><th>Description</th>" +
      "<th class=\"num\">Credits</th><th>User</th>" +
      "</tr></thead><tbody>" +
      body +
      "</tbody></table>"
    );
  }

  function setStatus(el, message, isError) {
    if (!el) return;
    el.textContent = message || "";
    el.className = "key-status" + (isError ? " error-text" : "");
  }

  function syncKeyPanel(form) {
    if (!form || !window.ItApollo) return;
    var key = window.ItApollo.getApiKey();
    var input = $("#apollo-api-key", form);
    var meta = $("#apollo-key-meta", form);
    if (input && document.activeElement !== input) {
      input.value = key;
      input.placeholder = key ? "API key saved in this browser" : "Paste Apollo API key";
    }
    if (meta) {
      meta.textContent = key
        ? "Saved locally as " + window.ItApollo.maskApiKey(key)
        : "No API key saved yet — enter one to refresh live.";
    }
  }

  function wireKeyPanel(opts) {
    var form = $("#apollo-key-form");
    if (!form || !window.ItApollo) return;

    var input = $("#apollo-api-key", form);
    var status = $("#apollo-key-status", form);
    var saveBtn = $("#apollo-key-save", form);
    var refreshBtn = $("#apollo-key-refresh", form);
    var clearBtn = $("#apollo-key-clear", form);

    syncKeyPanel(form);

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var key = window.ItApollo.setApiKey(input ? input.value : "");
      if (!key) {
        setStatus(status, "Enter an API key first.", true);
        return;
      }
      syncKeyPanel(form);
      setStatus(status, "API key saved in this browser.");
      if (opts && opts.onRefresh) opts.onRefresh(key);
    });

    if (refreshBtn) {
      refreshBtn.addEventListener("click", function () {
        var key = window.ItApollo.setApiKey(input ? input.value : "") ||
          window.ItApollo.getApiKey();
        if (!key) {
          setStatus(status, "Enter an API key first.", true);
          return;
        }
        syncKeyPanel(form);
        if (opts && opts.onRefresh) opts.onRefresh(key);
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        window.ItApollo.clearApiKey();
        if (input) input.value = "";
        syncKeyPanel(form);
        setStatus(status, "API key cleared from this browser.");
      });
    }

    if (saveBtn) {
      /* submit handler covers save */
    }
  }

  function renderApolloDetail(data) {
    var root = $("#apollo-detail");
    if (!root) return;
    var kpi = data.kpi || {};
    var cycle = data.cycle || {};
    var team = data.team || {};

    $("#apollo-kpi", root).innerHTML =
      '<div class="score">' +
      '<div class="muted">' +
      escapeHtml(kpi.label || "Lead credits remaining") +
      "</div>" +
      '<div class="big ' +
      statusClass(kpi.status) +
      '">' +
      escapeHtml(kpi.display || "—") +
      "</div>" +
      "<p class=\"muted\" style=\"margin:0.45rem 0 0\">Billing cycle " +
      escapeHtml(formatDay(cycle.start_date)) +
      " → " +
      escapeHtml(formatDay(cycle.end_date)) +
      (team.using_unified_credits ? " · unified credits" : "") +
      "</p></div>";

    $("#apollo-team", root).innerHTML =
      "<table><tbody>" +
      "<tr><th>Team</th><td>" +
      escapeHtml(team.name || "—") +
      " (" +
      escapeHtml(team.domain || "") +
      ")</td></tr>" +
      "<tr><th>Plan status</th><td>" +
      escapeHtml(team.status || "—") +
      "</td></tr>" +
      "<tr><th>Seats</th><td>" +
      formatNumber(team.seats_limit) +
      "</td></tr>" +
      "<tr><th>Lead used / effective</th><td>" +
      formatNumber(team.num_lead_credits_used) +
      " / " +
      formatNumber(team.effective_num_lead_credits) +
      "</td></tr>" +
      "<tr><th>Unified credits used</th><td>" +
      formatNumber(team.total_unified_credits_used) +
      "</td></tr>" +
      "<tr><th>Additional email credits</th><td>" +
      formatNumber(team.additional_email_credits) +
      "</td></tr>" +
      "</tbody></table>";

    $("#apollo-credits", root).innerHTML = creditRowsHtml(data.credits);
    $("#apollo-users", root).innerHTML = usersHtml(data.users);
    $("#apollo-history", root).innerHTML = historyHtml(data.history);

    var history = data.history || {};
    $("#apollo-history-range", root).textContent =
      "Showing " +
      formatDay(history.min_date) +
      " → " +
      formatDay(history.max_date) +
      " (" +
      formatNumber((history.pagination && history.pagination.total_entries) || 0) +
      " events)";

    var links = data.links || {};
    var actions = $("#apollo-actions", root);
    if (actions) {
      actions.innerHTML =
        '<a class="btn primary" href="' +
        escapeHtml(links.apollo_history || "#") +
        '" target="_blank" rel="noopener">Open Apollo credit history</a>' +
        '<a class="btn" href="' +
        escapeHtml(links.apollo_credits || "#") +
        '" target="_blank" rel="noopener">Apollo credit plans</a>' +
        '<a class="btn" href="/it/">Back to SAAS status</a>';
    }

    var meta = $("#apollo-updated");
    if (meta) {
      meta.textContent = data.fetched_at
        ? "Last refreshed " + formatDate(data.fetched_at)
        : "";
    }
  }

  async function refreshApolloLive(apiKey) {
    var status = $("#apollo-key-status");
    var refreshBtn = $("#apollo-key-refresh");
    setStatus(status, "Refreshing from Apollo…");
    if (refreshBtn) refreshBtn.disabled = true;
    try {
      var data = await window.ItApollo.fetchLiveApollo(apiKey);
      try {
        sessionStorage.setItem("it.apollo.live", JSON.stringify(data));
        sessionStorage.setItem(
          "it.saas.live",
          JSON.stringify(window.ItApollo.toSaasCard(data))
        );
      } catch (e) {
        /* ignore */
      }
      if ($("#apollo-detail")) renderApolloDetail(data);
      var mount = $("#saas-cards");
      if (mount) {
        var saas = window.ItApollo.toSaasCard(data);
        renderSaasCards(saas.services || [], mount);
        var dashMeta = $("#saas-updated");
        if (dashMeta) {
          dashMeta.textContent = "Live refresh " + formatDate(saas.updated_at);
        }
      }
      setStatus(status, "Live data loaded " + formatDate(data.fetched_at));
      return data;
    } catch (err) {
      setStatus(status, err.message || String(err), true);
      throw err;
    } finally {
      if (refreshBtn) refreshBtn.disabled = false;
    }
  }

  async function initDashboard() {
    var mount = $("#saas-cards");
    var meta = $("#saas-updated");
    if (!mount) return;

    wireKeyPanel({
      onRefresh: function (key) {
        refreshApolloLive(key).catch(function () {
          /* status already set */
        });
      }
    });

    try {
      var live = sessionStorage.getItem("it.saas.live");
      if (live) {
        var liveData = JSON.parse(live);
        renderSaasCards(liveData.services || [], mount);
        if (meta) {
          meta.textContent = liveData.updated_at
            ? "Live session " + formatDate(liveData.updated_at)
            : "";
        }
        return;
      }
    } catch (e) {
      /* fall through */
    }

    try {
      var data = await fetchJson("/it/data/saas.json");
      renderSaasCards(data.services || [], mount);
      if (meta) {
        meta.textContent = data.updated_at
          ? "Cached snapshot " + formatDate(data.updated_at)
          : "";
      }
    } catch (err) {
      mount.innerHTML =
        '<div class="error">No SAAS snapshot yet. Enter an Apollo API key above and click Refresh.</div>';
      console.error(err);
    }
  }

  async function initApolloDetail() {
    var root = $("#apollo-detail");
    if (!root) return;

    wireKeyPanel({
      onRefresh: function (key) {
        refreshApolloLive(key).catch(function () {
          /* status already set */
        });
      }
    });

    try {
      var live = sessionStorage.getItem("it.apollo.live");
      if (live) {
        renderApolloDetail(JSON.parse(live));
        return;
      }
    } catch (e) {
      /* fall through */
    }

    try {
      var data = await fetchJson("/it/data/apollo.json");
      renderApolloDetail(data);
    } catch (err) {
      root.innerHTML =
        '<div class="error">No cached Apollo data. Enter your API key above and click Save &amp; refresh.</div>';
      console.error(err);
    }

    // Auto-refresh when a key is already saved.
    if (window.ItApollo && window.ItApollo.getApiKey()) {
      refreshApolloLive(window.ItApollo.getApiKey()).catch(function () {
        /* keep cached view */
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initDashboard();
    initApolloDetail();
  });
})();
