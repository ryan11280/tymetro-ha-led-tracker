
class TYMetroTrackerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._config = {};
    this._built = false;
    this._markers = new Map();
    this._selectedTrainKey = null;
  }

  static getStubConfig() {
    return {
      entity: "sensor.tymetro_tracker",
      direction_entity: "input_select.tymetro_direction",
      live_entity: "input_boolean.tymetro_live_mode",
      timer_entity: "timer.tymetro_live_session",
      static_entity: "sensor.tymetro_static_model_raw",
      liveboard_entity: "sensor.tymetro_liveboard_raw",
    };
  }

  setConfig(config) {
    this._config = { ...TYMetroTrackerCard.getStubConfig(), ...config };
    if (this._built) this._update();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
    this._update();
  }

  getCardSize() {
    return 7;
  }

  _build() {
    this._built = true;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          color: var(--primary-text-color);
          --ty-purple: #b678ff;
          --ty-purple-strong: #c996ff;
          --ty-purple-soft: color-mix(in srgb, var(--ty-purple) 17%, transparent);
          --ty-green: var(--success-color, #4caf50);
          --ty-orange: var(--warning-color, #ff9800);
          --ty-red: var(--error-color, #f44336);
          --ty-blue: var(--info-color, #42a5f5);
          --ty-muted: var(--secondary-text-color);
          --ty-border: color-mix(in srgb, var(--divider-color, #777) 68%, transparent);
          --ty-surface: var(--ha-card-background, var(--card-background-color, #202124));
        }

        * {
          box-sizing: border-box;
        }

        ha-card {
          overflow: hidden;
          border-radius: var(--ha-card-border-radius, 16px);
          background: var(--ty-surface);
          border: 1px solid var(--ha-card-border-color, transparent);
          box-shadow: var(--ha-card-box-shadow, none);
        }

        .wrap {
          padding: 20px 22px 16px;
        }

        .header {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 18px;
          align-items: start;
        }

        .title {
          margin: 0;
          font-size: clamp(22px, 3vw, 29px);
          line-height: 1.15;
          font-weight: 800;
          letter-spacing: -.02em;
        }

        .subtitle {
          margin-top: 6px;
          color: var(--ty-muted);
          font-size: 13px;
        }

        .badges {
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 7px;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          min-height: 30px;
          padding: 0 11px;
          border-radius: 999px;
          background: color-mix(in srgb, var(--primary-text-color) 9%, transparent);
          color: var(--primary-text-color);
          font-size: 12px;
          font-weight: 750;
          white-space: nowrap;
        }

        .badge.schedule { color: var(--ty-blue); }
        .badge.live { color: var(--ty-green); }
        .badge.pending { color: var(--ty-orange); }
        .badge.stale { color: var(--ty-red); }

        .controls {
          display: grid;
          grid-template-columns: 1fr 1fr minmax(180px, .82fr);
          gap: 10px;
          margin-top: 18px;
        }

        button {
          font: inherit;
        }

        .control {
          min-height: 58px;
          padding: 10px 13px;
          border: 1px solid var(--ty-border);
          border-radius: 14px;
          background: color-mix(in srgb, var(--primary-text-color) 4%, transparent);
          color: var(--primary-text-color);
          cursor: pointer;
          transition: background 150ms ease, border-color 150ms ease, transform 120ms ease;
        }

        .control:hover {
          background: color-mix(in srgb, var(--primary-text-color) 7%, transparent);
        }

        .control:active {
          transform: scale(.987);
        }

        .control.active {
          border-color: color-mix(in srgb, var(--ty-purple) 72%, transparent);
          background: var(--ty-purple-soft);
        }

        .control.live-on {
          border-color: color-mix(in srgb, var(--ty-green) 58%, transparent);
          background: color-mix(in srgb, var(--ty-green) 11%, transparent);
        }

        .control-main {
          font-size: 14px;
          font-weight: 800;
        }

        .control-sub {
          margin-top: 4px;
          color: var(--ty-muted);
          font-size: 11px;
        }

        .warning {
          display: none;
          margin-top: 14px;
          padding: 11px 13px;
          border: 1px solid color-mix(in srgb, var(--ty-red) 42%, transparent);
          border-radius: 12px;
          background: color-mix(in srgb, var(--ty-red) 12%, transparent);
          font-size: 12px;
          line-height: 1.45;
        }

        .warning.show {
          display: block;
        }

        .warning strong {
          color: var(--ty-red);
        }

        .section-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 12px;
          margin-top: 23px;
          margin-bottom: 7px;
        }

        .section-title {
          margin: 0;
          font-size: 19px;
          font-weight: 800;
        }

        .section-meta {
          color: var(--ty-muted);
          font-size: 11px;
          text-align: right;
          white-space: nowrap;
        }

        /* ---------- Rail ---------- */

        .rail-shell {
          position: relative;
          width: 100%;
          min-width: 0;
          padding: 4px 0 2px;
        }

        .rail {
          position: relative;
          width: 100%;
          height: 202px;
          min-width: 0;
        }

        .track-line {
          position: absolute;
          left: 2%;
          right: 2%;
          top: 97px;
          height: 5px;
          border-radius: 999px;
          background: linear-gradient(
            90deg,
            color-mix(in srgb, var(--ty-purple) 88%, white 0%),
            color-mix(in srgb, var(--ty-purple-strong) 88%, white 0%)
          );
          box-shadow: 0 0 0 1px color-mix(in srgb, var(--ty-purple) 22%, transparent);
        }

        .stations {
          position: absolute;
          inset: 0 2%;
        }

        .station {
          position: absolute;
          top: 83px;
          transform: translateX(-50%);
          width: 1px;
          text-align: center;
          overflow: visible;
        }

        .station-dot {
          position: relative;
          width: 17px;
          height: 17px;
          left: 50%;
          transform: translateX(-50%);
          border-radius: 50%;
          background: var(--ty-surface);
          border: 3px solid var(--ty-purple);
          box-shadow: 0 0 0 2px color-mix(in srgb, var(--ty-surface) 92%, transparent);
        }

        .station-code {
          position: absolute;
          top: 25px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 12px;
          font-weight: 850;
          white-space: nowrap;
        }

        .station-name {
          position: absolute;
          top: 44px;
          left: 50%;
          transform: translateX(-50%);
          width: 84px;
          color: var(--ty-muted);
          font-size: 9px;
          line-height: 1.15;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .trains {
          position: absolute;
          inset: 0 2%;
          pointer-events: none;
        }

        .train {
          --lane-y: -44px;
          appearance: none;
          position: absolute;
          z-index: 8;
          top: 99px;
          left: 0%;
          transform: translate(-50%, var(--lane-y));
          padding: 0;
          border: 0;
          background: none;
          color: white;
          pointer-events: auto;
          cursor: pointer;
          opacity: 1;
          transition:
            left 4.8s linear,
            opacity .28s ease,
            transform .22s ease;
        }

        .train.lane-1 { --lane-y: 34px; }
        .train.lane-2 { --lane-y: -67px; }
        .train.lane-3 { --lane-y: 57px; }

        .marker {
          position: relative;
          min-width: 31px;
          height: 25px;
          padding: 0 7px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          background: var(--ty-purple);
          color: white;
          border: 2px solid color-mix(in srgb, white 48%, transparent);
          box-shadow: 0 3px 10px color-mix(in srgb, black 30%, transparent);
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .03em;
        }

        .train::after {
          content: "";
          position: absolute;
          left: 50%;
          width: 1px;
          height: 19px;
          background: color-mix(in srgb, var(--ty-purple) 65%, transparent);
          transform: translateX(-50%);
        }

        .train:not(.lane-1):not(.lane-3)::after {
          top: 25px;
        }

        .train.lane-1::after,
        .train.lane-3::after {
          bottom: 25px;
        }

        .train.live .marker::after {
          content: "L";
          position: absolute;
          top: -7px;
          right: -7px;
          width: 14px;
          height: 14px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background: var(--ty-green);
          color: white;
          font-size: 8px;
          font-weight: 900;
          border: 1px solid color-mix(in srgb, white 55%, transparent);
        }

        .train.selected .marker {
          outline: 3px solid color-mix(in srgb, var(--primary-text-color) 38%, transparent);
          outline-offset: 2px;
        }

        .train.leaving {
          opacity: 0;
        }

        .detail {
          min-height: 24px;
          margin-top: -2px;
          color: var(--ty-muted);
          font-size: 11px;
          text-align: center;
        }

        /* ---------- Train list ---------- */

        .train-list {
          display: grid;
          gap: 5px;
          margin-top: 8px;
        }

        .train-row {
          display: grid;
          grid-template-columns: 58px minmax(100px, 170px) 1fr 54px;
          gap: 11px;
          align-items: center;
          min-height: 39px;
          padding: 6px 8px;
          border-radius: 9px;
          background: color-mix(in srgb, var(--primary-text-color) 3%, transparent);
        }

        .train-type {
          font-size: 11px;
          font-weight: 850;
        }

        .train-position {
          min-width: 0;
          font-size: 12px;
          font-weight: 700;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .progress {
          height: 6px;
          overflow: hidden;
          border-radius: 999px;
          background: color-mix(in srgb, var(--primary-text-color) 11%, transparent);
        }

        .progress-bar {
          height: 100%;
          width: 0%;
          border-radius: inherit;
          background: var(--ty-purple);
        }

        .train-meta {
          color: var(--ty-muted);
          font-size: 10px;
          text-align: right;
          white-space: nowrap;
        }

        .live-tag {
          color: var(--ty-green);
          margin-left: 3px;
          font-size: 9px;
        }

        .empty {
          padding: 14px 8px;
          color: var(--ty-muted);
          font-size: 12px;
          text-align: center;
        }

        /* ---------- System footer ---------- */

        .system {
          display: flex;
          flex-wrap: wrap;
          gap: 7px 13px;
          margin-top: 16px;
          padding-top: 12px;
          border-top: 1px solid var(--ty-border);
          color: var(--ty-muted);
          font-size: 10px;
        }

        .ok { color: var(--ty-green); }
        .warn { color: var(--ty-orange); }
        .bad { color: var(--ty-red); }

        @media (max-width: 760px) {
          .wrap {
            padding: 16px 14px 13px;
          }

          .header {
            grid-template-columns: 1fr;
          }

          .badges {
            justify-content: flex-start;
          }

          .controls {
            grid-template-columns: 1fr 1fr;
          }

          .live-control {
            grid-column: 1 / -1;
          }

          .rail {
            height: 174px;
          }

          .track-line {
            top: 85px;
          }

          .station {
            top: 71px;
          }

          .station-name {
            display: none;
          }

          .train {
            top: 87px;
            --lane-y: -39px;
          }

          .train.lane-1 { --lane-y: 30px; }
          .train.lane-2 { --lane-y: -58px; }
          .train.lane-3 { --lane-y: 48px; }

          .marker {
            min-width: 28px;
            height: 23px;
            font-size: 9px;
          }

          .train-row {
            grid-template-columns: 46px minmax(86px, 130px) 1fr 42px;
            gap: 7px;
          }
        }

        @media (max-width: 430px) {
          .station-code {
            font-size: 10px;
          }

          .station-dot {
            width: 14px;
            height: 14px;
            border-width: 2px;
          }

          .train-row {
            grid-template-columns: 42px 1fr 42px;
          }

          .progress {
            grid-column: 1 / -1;
            grid-row: 2;
          }

          .train-meta {
            grid-column: 3;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .train,
          .control {
            transition: none !important;
          }
        }
      </style>

      <ha-card>
        <div class="wrap">
          <div class="header">
            <div>
              <h2 class="title">桃園機場捷運 A1–A9</h2>
              <div class="subtitle">Animated Tracker · 實體 LED 同步</div>
            </div>

            <div class="badges">
              <span id="modeBadge" class="badge schedule">Schedule</span>
              <span id="directionBadge" class="badge">← A1</span>
              <span id="countBadge" class="badge">0 班</span>
              <span id="timerBadge" class="badge">Live Off</span>
            </div>
          </div>

          <div class="controls">
            <button id="dirA1" class="control" type="button">
              <div class="control-main">← 往 A1 台北</div>
              <div class="control-sub">北上</div>
            </button>

            <button id="dirA9" class="control" type="button">
              <div class="control-main">往 A9 林口 →</div>
              <div class="control-sub">南下</div>
            </button>

            <button id="liveBtn" class="control live-control" type="button">
              <div class="control-main">TDX 即時模式</div>
              <div id="liveSub" class="control-sub">時刻表模擬</div>
            </button>
          </div>

          <div id="warning" class="warning"></div>

          <div class="section-head">
            <h3 class="section-title">列車位置</h3>
            <div id="directionText" class="section-meta">← 往 A1 台北</div>
          </div>

          <div class="rail-shell">
            <div id="rail" class="rail">
              <div class="track-line"></div>
              <div id="stations" class="stations"></div>
              <div id="trains" class="trains"></div>
            </div>
          </div>

          <div id="detail" class="detail">點擊列車可查看詳細位置</div>

          <div class="section-head">
            <h3 class="section-title">目前列車</h3>
            <div id="updatedText" class="section-meta"></div>
          </div>

          <div id="trainList" class="train-list"></div>
          <div id="system" class="system"></div>
        </div>
      </ha-card>
    `;

    this._stationNames = [
      "台北車站",
      "三重",
      "新北產業園區",
      "新莊副都心",
      "泰山",
      "泰山貴和",
      "體育大學",
      "長庚醫院",
      "林口",
    ];

    const stations = this.shadowRoot.getElementById("stations");
    this._stationNames.forEach((name, idx) => {
      const station = document.createElement("div");
      station.className = "station";
      station.style.left = `${(idx / 8) * 100}%`;
      station.innerHTML = `
        <div class="station-dot"></div>
        <div class="station-code">A${idx + 1}</div>
        <div class="station-name" title="${name}">${name}</div>
      `;
      stations.appendChild(station);
    });

    this.shadowRoot.getElementById("dirA1").addEventListener("click", () => {
      this._setDirection("← 往 A1 台北");
    });

    this.shadowRoot.getElementById("dirA9").addEventListener("click", () => {
      this._setDirection("往 A9 林口 →");
    });

    this.shadowRoot.getElementById("liveBtn").addEventListener("click", () => {
      if (!this._hass) return;
      const entity = this._config.live_entity;
      const isOn = this._hass.states[entity]?.state === "on";
      this._hass.callService(
        "input_boolean",
        isOn ? "turn_off" : "turn_on",
        { entity_id: entity }
      );
    });
  }

  _setDirection(option) {
    if (!this._hass) return;
    this._hass.callService("input_select", "select_option", {
      entity_id: this._config.direction_entity,
      option,
    });
  }

  _stationIndex(id) {
    if (typeof id !== "string") return null;
    const match = id.match(/^A(\d+)$/);
    if (!match) return null;
    const n = Number(match[1]);
    if (!Number.isFinite(n) || n < 1 || n > 9) return null;
    return n - 1;
  }

  _trainX(train) {
    if (!train || typeof train !== "object") return null;

    if (train.state === "station") {
      const idx = this._stationIndex(train.station || train.from);
      return idx === null ? null : (idx / 8) * 100;
    }

    const from = this._stationIndex(train.from);
    const to = this._stationIndex(train.to);
    if (from === null || to === null) return null;

    let p = Number(train.progress);
    if (!Number.isFinite(p)) p = 0;
    p = Math.max(0, Math.min(1, p));

    const position = from + (to - from) * p;
    return (position / 8) * 100;
  }

  _modeInfo(mode, liveOn) {
    if (mode === "live") return { text: "Live", cls: "live" };
    if (mode === "schedule_live_stale") return { text: "Live Stale", cls: "stale" };
    if (mode === "schedule_live_pending") return { text: "Live Pending", cls: "pending" };
    if (liveOn) return { text: "Live Pending", cls: "pending" };
    return { text: "Schedule", cls: "schedule" };
  }

  _trainKey(train, index = 0) {
    return String(
      train?.key ||
      `${train?.type || "train"}|${train?.anchor || index}|${train?.from || ""}|${train?.to || ""}`
    );
  }

  _describeTrain(train) {
    const type = Number(train.train_type) === 2 ? "直達" : "普通";
    let position;

    if (train.state === "station") {
      position = `${train.station || train.from || "?"} · 停站`;
    } else {
      const pct = Math.round((Number(train.progress) || 0) * 100);
      position = `${train.from || "?"} → ${train.to || "?"} · ${pct}%`;
    }

    if (train.live_corrected) {
      const delay = Number(train.delay_minutes) || 0;
      if (Math.abs(delay) >= 0.1) {
        position += ` · Live ${delay > 0 ? "+" : ""}${delay.toFixed(1)}m`;
      } else {
        position += " · Live";
      }
    }

    return `${type} · ${position}`;
  }

  _latestTrain(key) {
    const tracker = this._hass?.states[this._config.entity];
    const trains = Array.isArray(tracker?.attributes?.trains)
      ? tracker.attributes.trains
      : [];

    return trains.find((train, index) => this._trainKey(train, index) === key) || null;
  }

  _update() {
    if (!this._hass || !this._built) return;

    const tracker = this._hass.states[this._config.entity];
    const directionEntity = this._hass.states[this._config.direction_entity];
    const liveEntity = this._hass.states[this._config.live_entity];
    const timerEntity = this._hass.states[this._config.timer_entity];
    const staticEntity = this._hass.states[this._config.static_entity];
    const liveboardEntity = this._hass.states[this._config.liveboard_entity];

    const attrs = tracker?.attributes || {};
    const mode = tracker?.state || attrs.mode || "unavailable";
    const liveOn = liveEntity?.state === "on";
    const trains = Array.isArray(attrs.trains) ? attrs.trains : [];

    const direction =
      attrs.direction ||
      (directionEntity?.state?.includes("A1") ? "to_a1" : "to_a9");

    const info = this._modeInfo(mode, liveOn);
    const modeBadge = this.shadowRoot.getElementById("modeBadge");
    modeBadge.textContent = info.text;
    modeBadge.className = `badge ${info.cls}`;

    this.shadowRoot.getElementById("directionBadge").textContent =
      direction === "to_a1" ? "← A1" : "A9 →";

    this.shadowRoot.getElementById("countBadge").textContent =
      `${Number(attrs.train_count ?? trains.length) || 0} 班`;

    const remaining = timerEntity?.attributes?.remaining;
    this.shadowRoot.getElementById("timerBadge").textContent =
      liveOn ? (remaining || "Live On") : "Live Off";

    this.shadowRoot.getElementById("dirA1")
      .classList.toggle("active", direction === "to_a1");

    this.shadowRoot.getElementById("dirA9")
      .classList.toggle("active", direction === "to_a9");

    const liveBtn = this.shadowRoot.getElementById("liveBtn");
    liveBtn.classList.toggle("live-on", liveOn);

    this.shadowRoot.getElementById("liveSub").textContent =
      !liveOn
        ? "時刻表模擬"
        : mode === "live"
          ? "即時校正中"
          : mode === "schedule_live_stale"
            ? "來源資料過期"
            : "等待即時校正";

    const directionText =
      attrs.direction_label ||
      (direction === "to_a1" ? "← 往 A1 台北" : "往 A9 林口 →");

    this.shadowRoot.getElementById("directionText").textContent = directionText;

    const warning = this.shadowRoot.getElementById("warning");
    if (mode === "schedule_live_stale") {
      const age = Number(attrs.live_source_age_seconds);
      const ageText = Number.isFinite(age)
        ? `${Math.round(age / 60)} 分鐘`
        : "過久";

      warning.innerHTML =
        `<strong>TDX 即時資料暫時不可用</strong> · 桃捷來源已過期 ${ageText}，目前使用官方時刻表模擬，Live 將自動結束。`;
      warning.classList.add("show");
    } else {
      warning.classList.remove("show");
      warning.textContent = "";
    }

    this._updateMarkers(trains);
    this._updateTrainList(trains);

    if (attrs.updated_at) {
      const d = new Date(attrs.updated_at);
      this.shadowRoot.getElementById("updatedText").textContent =
        Number.isNaN(d.getTime())
          ? ""
          : `更新 ${d.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}`;
    } else {
      this.shadowRoot.getElementById("updatedText").textContent = "";
    }

    const staticOk = staticEntity?.state === "ready";
    const sourceAge = Number(attrs.live_source_age_seconds);
    const sourceAgeText = Number.isFinite(sourceAge)
      ? `${Math.round(sourceAge / 60)}m`
      : "--";

    const liveboardStatus =
      mode === "schedule_live_stale"
        ? `Stale ${sourceAgeText}`
        : liveOn
          ? (liveboardEntity?.attributes?.http_status || "Pending")
          : "Standby";

    const liveboardClass =
      mode === "schedule_live_stale"
        ? "bad"
        : liveOn
          ? "warn"
          : "";

    this.shadowRoot.getElementById("system").innerHTML = `
      <span class="${staticOk ? "ok" : "bad"}">Static ${staticOk ? "Ready" : "Error"}</span>
      <span class="${liveboardClass}">LiveBoard ${liveboardStatus}</span>
      <span>Tracker ${mode}</span>
      <span>Frame A ${attrs.frame_a ?? "?"} / B ${attrs.frame_b ?? "?"}</span>
    `;
  }

  _updateMarkers(trains) {
    const layer = this.shadowRoot.getElementById("trains");

    const positioned = trains
      .map((train, index) => ({
        train,
        index,
        key: this._trainKey(train, index),
        x: this._trainX(train),
      }))
      .filter(item => item.x !== null);

    const activeKeys = new Set();

    positioned.forEach((item, index) => {
      activeKeys.add(item.key);

      const closeBefore = positioned
        .slice(0, index)
        .filter(other => Math.abs(other.x - item.x) < 4.2)
        .length;

      const lane = closeBefore % 4;
      const laneClass = lane === 0 ? "" : `lane-${lane}`;

      let marker = this._markers.get(item.key);

      if (!marker) {
        marker = document.createElement("button");
        marker.type = "button";
        marker.className = "train";
        marker.style.left = `${item.x}%`;
        marker.style.opacity = "0";
        marker.innerHTML = `<span class="marker"></span>`;

        marker.addEventListener("click", () => {
          this._selectedTrainKey = item.key;

          for (const [key, node] of this._markers.entries()) {
            node.classList.toggle("selected", key === item.key);
          }

          const latest = this._latestTrain(item.key);
          this.shadowRoot.getElementById("detail").textContent =
            latest ? this._describeTrain(latest) : "列車資料已更新";
        });

        layer.appendChild(marker);
        this._markers.set(item.key, marker);

        requestAnimationFrame(() => {
          marker.style.opacity = "1";
        });
      }

      marker.className =
        `train ${laneClass}` +
        `${item.train.live_corrected ? " live" : ""}` +
        `${this._selectedTrainKey === item.key ? " selected" : ""}`;

      marker.querySelector(".marker").textContent =
        Number(item.train.train_type) === 2 ? "直" : "普";

      marker.title = this._describeTrain(item.train);

      requestAnimationFrame(() => {
        marker.style.left = `${item.x}%`;
      });
    });

    for (const [key, marker] of this._markers.entries()) {
      if (!activeKeys.has(key)) {
        marker.classList.add("leaving");

        setTimeout(() => {
          marker.remove();
          this._markers.delete(key);

          if (this._selectedTrainKey === key) {
            this._selectedTrainKey = null;
            this.shadowRoot.getElementById("detail").textContent =
              "點擊列車可查看詳細位置";
          }
        }, 300);
      }
    }
  }

  _updateTrainList(trains) {
    const list = this.shadowRoot.getElementById("trainList");

    if (!trains.length) {
      list.innerHTML = `
        <div class="empty">
          目前 A1–A9 沒有列車，等待下一班進入顯示範圍。
        </div>
      `;
      return;
    }

    list.innerHTML = trains.map(train => {
      const type = Number(train.train_type) === 2 ? "直達" : "普通";
      let position = "";
      let pct = 0;
      let meta = "";

      if (train.state === "station") {
        position = `${train.station || train.from || "?"} · 停站`;
        pct = 100;
        meta = "停站";
      } else {
        pct = Math.max(
          0,
          Math.min(100, Math.round((Number(train.progress) || 0) * 100))
        );
        position = `${train.from || "?"} → ${train.to || "?"}`;
        meta = `${pct}%`;
      }

      if (train.live_corrected) {
        const delay = Number(train.delay_minutes) || 0;
        meta += Math.abs(delay) >= 0.1
          ? ` · ${delay > 0 ? "+" : ""}${delay.toFixed(1)}m`
          : " · Live";
      }

      return `
        <div class="train-row">
          <div class="train-type">
            ${type}${train.live_corrected ? `<span class="live-tag">LIVE</span>` : ""}
          </div>
          <div class="train-position">${position}</div>
          <div class="progress" title="${pct}%">
            <div class="progress-bar" style="width:${pct}%"></div>
          </div>
          <div class="train-meta">${meta}</div>
        </div>
      `;
    }).join("");
  }
}

if (!customElements.get("tymetro-tracker-card")) {
  customElements.define("tymetro-tracker-card", TYMetroTrackerCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "tymetro-tracker-card")) {
  window.customCards.push({
    type: "tymetro-tracker-card",
    name: "TYMetro Tracker Card",
    description: "Animated A1–A9 Taoyuan Airport MRT tracker for Home Assistant.",
    preview: false,
  });
}
