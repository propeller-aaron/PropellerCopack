STATUS_CSS = """
.utility-sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0;}

html, body {
  height: 100%;
}

body {
  overflow: hidden;
}

.status-app {
  display: flex;
  height: 100vh;
  width: 100%;
}

.status-sidebar {
  flex-shrink: 0;
  width: 232px;
  display: flex;
  flex-direction: column;
  background: #0b3a5b;
  color: #dce9f4;
  padding: 1.35rem 1rem;
  overflow-y: auto;
}

.status-brand {
  display: block;
  margin: 0 0 1.25rem;
  padding: 0 0.5rem;
}

.status-brand-title {
  display: block;
  color: #fff;
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.3;
}

.status-brand-sub {
  display: block;
  margin-top: 0.15rem;
  color: #9db9cf;
  font-size: 0.75rem;
}

.status-nav {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.status-nav-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  width: 100%;
  padding: 0.6rem 0.65rem;
  border: 0;
  border-radius: 7px;
  background: none;
  color: #cfe3f2;
  font: inherit;
  font-size: 0.9rem;
  text-align: left;
  cursor: pointer;
}

.status-nav-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.status-nav-btn.is-active {
  background: #f2f8fd;
  color: #0b3a5b;
  font-weight: 700;
}

.status-nav-count {
  padding: 0.05rem 0.4rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  color: #dce9f4;
  font-size: 0.72rem;
  font-weight: 700;
}

.status-nav-btn.is-active .status-nav-count {
  background: #dbe9f4;
  color: #0b3a5b;
}

.status-nav-divider {
  height: 1px;
  margin: 0.5rem 0.65rem;
  background: rgba(255, 255, 255, 0.15);
  list-style: none;
}

.status-nav-link {
  text-decoration: none;
  box-sizing: border-box;
}

.status-nav-arrow {
  color: #9db9cf;
  font-size: 0.85rem;
}

.status-sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.status-sidebar-footer p {
  margin: 0 0 0.35rem;
  color: #9db9cf;
  font-size: 0.75rem;
}

.status-sidebar-footer code {
  display: block;
  padding: 0.4rem 0.5rem;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.2);
  color: #cfe3f2;
  font-size: 0.72rem;
  word-break: break-all;
}

.status-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.status-topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1.5rem;
  border-bottom: 1px solid #e5e5e5;
  background: #fff;
}

.status-topbar-title {
  margin: 0;
  font-size: 1.05rem;
  color: #0b3a5b;
}

.status-topbar-meta {
  margin: 0.15rem 0 0;
  color: #666;
  font-size: 0.82rem;
}

.status-topbar-score {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.85rem;
  border: 2px solid #0b3a5b;
  border-radius: 999px;
  background: #f7fbff;
  flex-shrink: 0;
}

.status-topbar-score-value {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1;
  color: #0b3a5b;
}

.status-topbar-score-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #666;
}

.status-panels {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem 2.5rem;
}

.status-tab-panel[hidden] {
  display: none;
}

@media (max-width: 760px) {
  body {
    overflow: auto;
  }

  .status-app {
    flex-direction: column;
    height: auto;
  }

  .status-sidebar {
    width: auto;
    flex-direction: row;
    align-items: center;
    overflow-x: auto;
    padding: 0.85rem 1rem;
  }

  .status-brand {
    margin: 0 1rem 0 0;
    flex-shrink: 0;
  }

  .status-nav {
    flex-direction: row;
    flex-shrink: 0;
  }

  .status-nav-btn {
    white-space: nowrap;
  }

  .status-nav-divider {
    display: none;
  }

  .status-sidebar-footer {
    display: none;
  }

  .status-main {
    height: auto;
  }

  .status-panels {
    overflow-y: visible;
  }
}

.status-shell {
  padding: 0;
}

.status-header {
  display: none;
}

.status-kicker {
  margin: 0 0 0.35rem;
  color: #666;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.status-meta {
  margin: 0;
  color: #666;
}

.status-score {
  display: grid;
  place-items: center;
  min-width: 6rem;
  padding: 0.75rem 1rem;
  border: 2px solid #0b3a5b;
  border-radius: 8px;
  background: #f7fbff;
}

.status-score-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: #0b3a5b;
}

.status-score-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #666;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.status-card,
.status-panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 1rem 1.1rem;
}

.status-panel {
  margin-bottom: 1.5rem;
}

.status-panel h2 {
  margin: 0 0 0.85rem;
  font-size: 1.1rem;
  color: #0b3a5b;
}

.status-metric {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #0b3a5b;
}

.status-detail {
  margin: 0.35rem 0 0;
  color: #666;
  font-size: 0.9rem;
}

.status-checks,
.status-rank-list,
.status-findings,
.status-suggestions,
.status-meta-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.status-check {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.45rem 0;
  border-bottom: 1px solid #e5e5e5;
}

.status-check:last-child {
  border-bottom: 0;
}

.status-check.is-ok .status-check-label::before {
  content: "✓ ";
  color: #1b7f3b;
}

.status-check.is-fail .status-check-label::before {
  content: "✕ ";
  color: #b42318;
}

.status-check-detail {
  color: #666;
  text-align: right;
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem 1rem;
  margin: 0;
}

.status-summary div {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.45rem 0;
  border-bottom: 1px solid #e5e5e5;
}

.status-summary dt,
.status-summary dd {
  margin: 0;
}

.status-summary dd {
  font-weight: 700;
  color: #0b3a5b;
}

.status-rank-list li,
.status-prompts details {
  padding: 0.45rem 0;
  border-bottom: 1px solid #e5e5e5;
}

.status-rank-list li:last-child,
.status-prompts details:last-child {
  border-bottom: 0;
}

.status-rank-list a {
  font-weight: 600;
}

.status-rank-list span {
  display: block;
  color: #666;
  font-size: 0.9rem;
}

.status-prompts summary {
  cursor: pointer;
  font-weight: 600;
  color: #0b3a5b;
}

.status-prompts p {
  margin: 0.65rem 0 0;
  color: #2c2c2c;
}

.status-pages-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.status-pages-head h2 {
  margin: 0;
}

.status-filter input {
  width: min(100%, 320px);
  padding: 0.55rem 0.75rem;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  font: inherit;
}

.status-table-wrap {
  overflow-x: auto;
}

.status-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

.status-table th,
.status-table td {
  padding: 0.75rem;
  border-top: 1px solid #e5e5e5;
  vertical-align: top;
  text-align: left;
}

.status-table thead th {
  border-top: 0;
  background: #f5f5f5;
  color: #0b3a5b;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.status-page-cell code,
.status-source {
  display: block;
  margin-top: 0.25rem;
  color: #666;
  font-size: 0.82rem;
  word-break: break-all;
}

.status-page-cell code {
  font-family: Consolas, "Courier New", monospace;
}

.status-rank-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: #eef4fa;
  color: #0b3a5b;
  font-weight: 700;
}

.status-rank-detail,
.status-muted {
  display: block;
  margin-top: 0.25rem;
  color: #666;
  font-size: 0.82rem;
}

.status-ok-label {
  color: #1b7f3b;
  font-weight: 600;
}

.status-findings li {
  display: inline-block;
  margin: 0 0.35rem 0.35rem 0;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: lowercase;
}

.status-findings .severity-high {
  background: #fde8e8;
  color: #9b1c1c;
}

.status-findings .severity-medium {
  background: #fff4e5;
  color: #9a6700;
}

.status-findings .severity-low {
  background: #eef4fa;
  color: #0b3a5b;
}

.status-suggestions li + li {
  margin-top: 0.45rem;
}

.status-suggestions li {
  color: #2c2c2c;
}

.status-dashboard {
  margin-bottom: 1.5rem;
}

.status-dashboard-hero {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.status-odometer-card,
.status-gauge-card {
  background: linear-gradient(180deg, #f7fbff 0%, #fff 100%);
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  padding: 1rem 1.1rem;
  text-align: center;
}

.status-odometer-card-gain {
  background: linear-gradient(180deg, #f4fff8 0%, #fff 100%);
}

.status-odometer-kicker {
  margin: 0 0 0.75rem;
  color: #666;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-odometer-caption {
  margin: 0.75rem 0 0;
  color: #666;
  font-size: 0.9rem;
}

.status-odometer {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.65rem 0.8rem;
  border: 2px solid #0b3a5b;
  border-radius: 8px;
  background: #0b3a5b;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.25);
}

.status-odometer-gain {
  border-color: #1b7f3b;
  background: #145a2a;
}

.status-odometer-prefix {
  color: #9fe8b8;
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.status-odometer-wheel {
  display: inline-block;
  width: 1.35rem;
  height: 2.4rem;
  overflow: hidden;
  border-radius: 4px;
  background: #052238;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.status-odometer-gain .status-odometer-wheel {
  background: #0d3d1d;
}

.status-odometer-strip {
  display: flex;
  flex-direction: column;
  transform: translateY(0);
  transition: transform 0.9s cubic-bezier(0.22, 1, 0.36, 1);
}

.status-odometer-strip span {
  display: grid;
  place-items: center;
  height: 2.4rem;
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.status-gauge-svg {
  width: min(100%, 160px);
  height: auto;
  margin: 0 auto;
  display: block;
}

.status-gauge-ring {
  fill: none;
  stroke-width: 10;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
  transition: stroke-dashoffset 1.1s cubic-bezier(0.22, 1, 0.36, 1);
}

.status-gauge-ring-bg {
  stroke: #edf2f7;
}

.status-gauge-ring-potential {
  stroke: #dbeafe;
}

.status-gauge-ring-current {
  stroke: #0b3a5b;
  stroke-linecap: round;
}

.status-gauge-value,
.status-gauge-sub {
  text-anchor: middle;
  fill: #0b3a5b;
  font-weight: 700;
}

.status-gauge-value {
  font-size: 1.55rem;
}

.status-gauge-sub {
  font-size: 0.72rem;
  fill: #666;
  font-weight: 600;
}

.status-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.status-kpi {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 0.85rem 0.95rem;
}

.status-kpi-label {
  margin: 0;
  color: #666;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.status-kpi-value {
  margin: 0.25rem 0 0;
  color: #0b3a5b;
  font-size: 1.55rem;
  font-weight: 700;
  line-height: 1.1;
}

.status-kpi-detail {
  margin: 0.25rem 0 0.55rem;
  color: #666;
  font-size: 0.85rem;
}

.status-kpi-bar {
  height: 6px;
  border-radius: 999px;
  background: #eef2f6;
  overflow: hidden;
}

.status-kpi-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #0b3a5b;
}

.status-kpi-warn .status-kpi-bar span {
  background: #d68910;
}

.status-kpi-good .status-kpi-bar span {
  background: #1b7f3b;
}

.status-kpi-gain .status-kpi-bar span {
  background: #27ae60;
}

.status-charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.status-chart-panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 1rem 1.1rem;
}

.status-chart-panel h3 {
  margin: 0 0 0.85rem;
  font-size: 1rem;
  color: #0b3a5b;
}

.status-donut-wrap {
  position: relative;
  width: 150px;
  height: 150px;
  margin: 0 auto 0.85rem;
}

.status-donut {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.status-donut-center {
  position: absolute;
  inset: 22%;
  display: grid;
  place-content: center;
  border-radius: 50%;
  background: #fff;
  text-align: center;
}

.status-donut-center strong {
  color: #0b3a5b;
  font-size: 1.35rem;
}

.status-donut-center span {
  color: #666;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.status-legend,
.status-health-legend {
  margin: 0;
  padding: 0;
  list-style: none;
}

.status-legend li,
.status-health-legend li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  color: #2c2c2c;
  font-size: 0.9rem;
}

.status-legend-swatch {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 2px;
  flex-shrink: 0;
}

.status-bar-chart {
  display: grid;
  gap: 0.65rem;
}

.status-bar-row {
  display: grid;
  gap: 0.3rem;
}

.status-bar-label {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.88rem;
  color: #2c2c2c;
}

.status-bar-label strong {
  color: #0b3a5b;
}

.status-bar-track {
  height: 10px;
  border-radius: 999px;
  background: #eef2f6;
  overflow: hidden;
}

.status-bar-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #d68910;
}

.status-bar-track-score span {
  background: #0b3a5b;
}

.status-health-chart {
  display: grid;
  gap: 0.85rem;
}

.status-health-bar {
  display: flex;
  height: 18px;
  border-radius: 999px;
  overflow: hidden;
  background: #eef2f6;
}

.status-health-clean {
  background: #1b7f3b;
}

.status-health-issues {
  background: #d68910;
}

.status-health-clean-swatch {
  background: #1b7f3b;
}

.status-health-issues-swatch {
  background: #d68910;
}

.status-metric-trigger {
  display: block;
  width: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: inherit;
  cursor: pointer;
}

.status-metric-trigger:hover,
.status-metric-trigger:focus-visible {
  outline: 2px solid #0b3a5b;
  outline-offset: 2px;
}

.status-kpi-trigger .status-kpi {
  display: block;
  width: 100%;
}

.status-hero-trigger {
  width: 100%;
  border-radius: 10px;
}

.status-hero-trigger .status-odometer-card,
.status-hero-trigger .status-gauge-card {
  display: block;
  width: 100%;
}

.status-card-trigger .status-card {
  display: block;
  height: 100%;
}

.status-card-heading {
  display: block;
  margin: 0 0 0.85rem;
  font-size: 1.1rem;
  color: #0b3a5b;
  font-weight: 700;
}

.status-donut-trigger {
  position: absolute;
  inset: 0;
  z-index: 1;
  border-radius: 50%;
}

.status-donut-trigger .status-donut,
.status-donut-trigger .status-donut-center {
  pointer-events: none;
}

.status-donut-trigger .status-donut-center {
  position: absolute;
  inset: 22%;
  display: grid;
  place-content: center;
  border-radius: 50%;
  background: #fff;
  text-align: center;
}

.status-bar-trigger,
.status-legend-trigger,
.status-check-trigger,
.status-summary-trigger,
.status-rank-trigger {
  width: 100%;
  text-align: left;
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem 1rem;
}

.status-summary-trigger .status-summary-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
  padding: 0.45rem 0;
  border-bottom: 1px solid #e5e5e5;
}

.status-summary-value {
  font-weight: 700;
  color: #0b3a5b;
}

.status-rank-url {
  display: block;
  font-weight: 600;
  color: #0b3a5b;
}

.status-modal {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: grid;
  place-items: center;
  padding: 1rem;
}

.status-modal[hidden] {
  display: none;
}

body.status-modal-open {
  overflow: hidden;
}

.status-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(11, 58, 91, 0.55);
}

.status-modal-dialog {
  position: relative;
  width: min(720px, 100%);
  max-height: min(85vh, 900px);
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e5e5;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
  padding: 1.25rem 1.35rem 1.35rem;
}

.status-modal-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 2rem;
  height: 2rem;
  border: 0;
  border-radius: 999px;
  background: #eef2f6;
  color: #0b3a5b;
  font-size: 1.35rem;
  line-height: 1;
  cursor: pointer;
}

.status-modal-kicker {
  margin: 0 0 0.35rem;
  color: #666;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-modal-dialog h2 {
  margin: 0 0 0.35rem;
  color: #0b3a5b;
  font-size: 1.35rem;
  padding-right: 2rem;
}

.status-modal-value {
  margin: 0 0 0.35rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0b3a5b;
}

.status-modal-desc {
  margin: 0 0 1rem;
  color: #666;
}

.status-modal-section-title {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
  color: #0b3a5b;
}

.status-modal-culprits {
  margin: 0 0 1rem;
  padding: 0;
  list-style: none;
  max-height: 240px;
  overflow: auto;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
}

.status-modal-culprits li {
  padding: 0.75rem 0.85rem;
  border-bottom: 1px solid #e5e5e5;
}

.status-modal-culprits li:last-child {
  border-bottom: 0;
}

.status-modal-culprit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.status-modal-culprits code {
  display: block;
  margin-top: 0.25rem;
  color: #666;
  font-size: 0.82rem;
  word-break: break-all;
}

.status-modal-culprits p {
  margin: 0.35rem 0 0;
  color: #2c2c2c;
  font-size: 0.9rem;
}

.status-modal-culprits a {
  font-weight: 600;
}

.status-modal-severity {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-modal-severity.severity-high {
  background: #fde8e8;
  color: #9b1c1c;
}

.status-modal-severity.severity-medium {
  background: #fff4e5;
  color: #9a6700;
}

.status-modal-severity.severity-low {
  background: #eef4fa;
  color: #0b3a5b;
}

.status-modal-empty {
  color: #666;
}

.status-modal-prompt pre {
  margin: 0 0 0.75rem;
  padding: 0.85rem;
  border-radius: 8px;
  background: #f7fbff;
  border: 1px solid #dbe7f3;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #2c2c2c;
}

.status-copy-prompt {
  padding: 0.55rem 0.9rem;
  border: 0;
  border-radius: 6px;
  background: #0b3a5b;
  color: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.status-copy-prompt:hover,
.status-copy-prompt:focus-visible {
  filter: brightness(1.08);
}

.status-copy-feedback {
  margin-left: 0.65rem;
  color: #1b7f3b;
  font-size: 0.9rem;
  font-weight: 600;
}

@media (max-width: 760px) {
  .status-header,
  .status-pages-head {
    flex-direction: column;
    align-items: stretch;
  }

  .status-score {
    justify-self: start;
  }

  .status-dashboard-hero {
    grid-template-columns: 1fr;
  }
}
"""

STATUS_JS = r"""
(function () {
  var metrics = {};
  try {
    metrics = JSON.parse(document.getElementById("status-metrics-json").textContent || "{}");
  } catch (error) {
    console.warn("Failed to parse status metrics", error);
  }

  function animateOdometers() {
    document.querySelectorAll(".status-odometer").forEach(function (odometer) {
      var wheels = odometer.querySelectorAll(".status-odometer-wheel");
      wheels.forEach(function (wheel, index) {
        var digit = parseInt(wheel.getAttribute("data-digit"), 10);
        var strip = wheel.querySelector(".status-odometer-strip");
        if (!strip || Number.isNaN(digit)) return;
        window.setTimeout(function () {
          strip.style.transform = "translateY(" + (-digit * 10) + "%)";
        }, 120 + index * 90);
      });
    });

    document.querySelectorAll(".status-gauge-ring-current").forEach(function (ring) {
      var offset = ring.getAttribute("stroke-dashoffset");
      if (!offset) return;
      ring.style.strokeDashoffset = ring.getAttribute("stroke-dasharray");
      window.requestAnimationFrame(function () {
        ring.style.strokeDashoffset = offset;
      });
    });
  }

  animateOdometers();

  var modal = document.getElementById("status-modal");
  var modalTitle = document.getElementById("status-modal-title");
  var modalValue = document.querySelector(".status-modal-value");
  var modalDesc = document.querySelector(".status-modal-desc");
  var modalCulprits = document.getElementById("status-modal-culprits");
  var modalPrompt = document.getElementById("status-modal-prompt");
  var copyButton = document.getElementById("status-copy-prompt");
  var copyFeedback = document.getElementById("status-copy-feedback");
  var lastFocus = null;

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderCulprits(culprits) {
    if (!modalCulprits) return;
    if (!culprits || !culprits.length) {
      modalCulprits.innerHTML = '<li class="status-modal-empty">No culprits listed.</li>';
      return;
    }
    modalCulprits.innerHTML = culprits.map(function (item) {
      var title = escapeHtml(item.title || item.url || item.file || "Unknown");
      var detail = escapeHtml(item.detail || "");
      var file = escapeHtml(item.file || "");
      var url = item.url ? '<a href="' + escapeHtml(item.url) + '">' + escapeHtml(item.url) + "</a>" : "";
      var severity = item.severity ? '<span class="status-modal-severity severity-' + escapeHtml(item.severity) + '">' + escapeHtml(item.severity) + "</span>" : "";
      return '<li><div class="status-modal-culprit-head"><strong>' + title + "</strong>" + severity + "</div>" + (url ? "<div>" + url + "</div>" : "") + (file ? "<code>" + file + "</code>" : "") + (detail ? "<p>" + detail + "</p>" : "") + "</li>";
    }).join("");
  }

  function openMetric(id) {
    var metric = metrics[id];
    if (!metric || !modal) return;
    lastFocus = document.activeElement;
    modalTitle.textContent = metric.title || id;
    modalValue.textContent = metric.value || "";
    modalDesc.textContent = metric.description || "";
    renderCulprits(metric.culprits || []);
    modalPrompt.textContent = metric.prompt || "";
    if (copyFeedback) copyFeedback.hidden = true;
    modal.hidden = false;
    document.body.classList.add("status-modal-open");
    modal.querySelector(".status-modal-close").focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove("status-modal-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  document.addEventListener("click", function (event) {
    var trigger = event.target.closest("[data-metric-id]");
    if (trigger) {
      event.preventDefault();
      openMetric(trigger.getAttribute("data-metric-id"));
      return;
    }
    if (event.target.closest("[data-close-modal]")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && modal && !modal.hidden) {
      closeModal();
    }
  });

  if (copyButton && modalPrompt) {
    copyButton.addEventListener("click", function () {
      var text = modalPrompt.textContent || "";
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          if (copyFeedback) {
            copyFeedback.hidden = false;
            window.setTimeout(function () {
              copyFeedback.hidden = true;
            }, 1800);
          }
        });
        return;
      }
      var area = document.createElement("textarea");
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      document.body.removeChild(area);
      if (copyFeedback) copyFeedback.hidden = false;
    });
  }

  var input = document.getElementById("status-filter");
  var rows = document.querySelectorAll("#status-table tbody tr");
  if (input && rows.length) {
    input.addEventListener("input", function () {
      var needle = input.value.toLowerCase().trim();
      rows.forEach(function (row) {
        var haystack = (row.getAttribute("data-search") || "").toLowerCase();
        row.hidden = needle && haystack.indexOf(needle) === -1;
      });
    });
  }

  var navButtons = document.querySelectorAll(".status-nav-btn");
  var panels = document.querySelectorAll(".status-tab-panel");
  var panelsWrap = document.querySelector(".status-panels");
  var STORAGE_KEY = "copack-status-tab";

  function activateTab(tabId, focusPanel) {
    if (!tabId) return;
    var matched = false;
    panels.forEach(function (panel) {
      var isMatch = panel.getAttribute("data-tab-panel") === tabId;
      if (isMatch) matched = true;
      panel.hidden = !isMatch;
    });
    if (!matched) return;
    navButtons.forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-tab-target") === tabId);
    });
    try {
      window.localStorage.setItem(STORAGE_KEY, tabId);
    } catch (error) {
      /* storage unavailable */
    }
    if (panelsWrap) panelsWrap.scrollTop = 0;
    if (focusPanel) {
      var active = document.querySelector('.status-tab-panel[data-tab-panel="' + tabId + '"]');
      if (active) active.focus();
    }
  }

  navButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      activateTab(btn.getAttribute("data-tab-target"), true);
    });
  });

  if (navButtons.length && panels.length) {
    var initial = "";
    try {
      initial = window.localStorage.getItem(STORAGE_KEY) || "";
    } catch (error) {
      initial = "";
    }
    var hasInitial = initial && document.querySelector('.status-tab-panel[data-tab-panel="' + initial + '"]');
    activateTab(hasInitial ? initial : navButtons[0].getAttribute("data-tab-target"));
  }
})();
"""
