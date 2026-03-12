(() => {
  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d", { alpha: false });

  const startBtn = document.getElementById("startBtn");
  const hudTarget = document.getElementById("hudTarget");
  const hudStep = document.getElementById("hudStep");
  const hudFps = document.getElementById("hudFps");
  const hudWinner = document.getElementById("hudWinner");
  const hudStatus = document.getElementById("hudStatus");

  let rows = 1;
  let cols = 4;
  let targetDistance = 0.0;
  let groundWorldY = 0.0;

  let racers = [];
  let latestStep = 0;
  let latestFps = 0;
  let raceStarted = false;
  let raceFinished = false;
  let finishOrder = [];

  function resizeCanvas() {
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const w = Math.floor(window.innerWidth * dpr);
    const h = Math.floor(window.innerHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
  }

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  function computeBBox(positions) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const p of positions) {
      const x = p[0], y = p[1];
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    if (!isFinite(minX)) return { minX: 0, maxX: 1, minY: 0, maxY: 1 };
    return { minX, maxX, minY, maxY };
  }

  function rgbToCss(rgb) {
    return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
  }

  function roundRectPath(x, y, w, h, r) {
    const rr = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.lineTo(x + w - rr, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + rr);
    ctx.lineTo(x + w, y + h - rr);
    ctx.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
    ctx.lineTo(x + rr, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
    ctx.lineTo(x, y + rr);
    ctx.quadraticCurveTo(x, y, x + rr, y);
    ctx.closePath();
  }

  function drawBackground() {
    const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    grad.addColorStop(0, "#88d0ff");
    grad.addColorStop(1, "#dff6ff");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  function drawCrown(cx, cy, scale = 1) {
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale, scale);

    ctx.fillStyle = "#FFD700";
    ctx.strokeStyle = "#9A6B00";
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.moveTo(-28, 14);
    ctx.lineTo(-22, -8);
    ctx.lineTo(-10, 3);
    ctx.lineTo(0, -16);
    ctx.lineTo(10, 3);
    ctx.lineTo(22, -8);
    ctx.lineTo(28, 14);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillRect(-30, 14, 60, 10);
    ctx.strokeRect(-30, 14, 60, 10);

    // gems
    ctx.fillStyle = "#ff4d4d";
    ctx.beginPath();
    ctx.arc(0, 5, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#4da6ff";
    ctx.beginPath();
    ctx.arc(-14, 7, 3.2, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(14, 7, 3.2, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  function drawFinishLine(finishX, laneY, laneH) {
    const finishTop = laneY + 14;
    const finishBottom = laneY + laneH - 14;

    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(finishX, finishTop);
    ctx.lineTo(finishX, finishBottom);
    ctx.stroke();

    const blockH = 16;
    const blockW = 10;
    for (let y = finishTop; y < finishBottom; y += blockH) {
      const idx = Math.floor((y - finishTop) / blockH);

      ctx.fillStyle = idx % 2 === 0 ? "#000" : "#fff";
      ctx.fillRect(finishX - blockW, y, blockW, blockH);

      ctx.fillStyle = idx % 2 === 0 ? "#fff" : "#000";
      ctx.fillRect(finishX, y, blockW, blockH);
    }

    ctx.fillStyle = "#111";
    ctx.font = "bold 13px Arial";
    ctx.textAlign = "center";
    ctx.fillText("FINISH", finishX, laneY + 24);
    ctx.textAlign = "start";
  }

  function drawPlacementBadge(laneX, laneY, laneW, laneH, racer) {
    if (!racer.finished || !racer.rank) return;

    const centerX = laneX + laneW * 0.52;
    const centerY = laneY + laneH * 0.43;

    if (racer.rank === 1) {
      ctx.fillStyle = "rgba(255, 215, 0, 0.14)";
      roundRectPath(laneX, laneY, laneW, laneH, 18);
      ctx.fill();

      drawCrown(centerX, centerY - 28, 1.05);

      ctx.fillStyle = "rgba(255, 215, 0, 0.98)";
      ctx.font = "bold 30px Arial";
      ctx.textAlign = "center";
      ctx.fillText("1st Place!", centerX, centerY + 28);

      ctx.font = "bold 16px Arial";
      ctx.fillStyle = "#5c4300";
      ctx.fillText("WINNER", centerX, centerY + 54);
      ctx.textAlign = "start";
      return;
    }

    const suffix = racer.rank === 2 ? "nd" : racer.rank === 3 ? "rd" : "th";
    const boxW = 132;
    const boxH = 58;

    ctx.fillStyle = "rgba(255,255,255,0.95)";
    ctx.strokeStyle = "rgba(0,0,0,0.25)";
    ctx.lineWidth = 2.5;
    roundRectPath(centerX - boxW / 2, centerY - boxH / 2, boxW, boxH, 14);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#111";
    ctx.font = "bold 28px Arial";
    ctx.textAlign = "center";
    ctx.fillText(`${racer.rank}${suffix}`, centerX, centerY + 8);
    ctx.textAlign = "start";
  }

  function drawLaneBorder(laneX, laneY, laneW, laneH, racer) {
    if (!racer.finished) {
      ctx.strokeStyle = "rgba(0,0,0,0.16)";
      ctx.lineWidth = 2;
      roundRectPath(laneX, laneY, laneW, laneH, 18);
      ctx.stroke();
      return;
    }

    if (racer.rank === 1) {
      ctx.strokeStyle = "rgba(255, 215, 0, 0.98)";
      ctx.lineWidth = 6;
      roundRectPath(laneX + 2, laneY + 2, laneW - 4, laneH - 4, 18);
      ctx.stroke();
    } else {
      ctx.strokeStyle = "rgba(255,255,255,0.96)";
      ctx.lineWidth = 4;
      roundRectPath(laneX + 2, laneY + 2, laneW - 4, laneH - 4, 18);
      ctx.stroke();
    }
  }

  function drawEmptyCell(cellX, cellY, cellW, cellH, label) {
    const pad = 20;
    const laneX = cellX + pad;
    const laneY = cellY + pad;
    const laneW = cellW - pad * 2;
    const laneH = cellH - pad * 2;

    ctx.fillStyle = "rgba(255,255,255,0.08)";
    roundRectPath(laneX, laneY, laneW, laneH, 18);
    ctx.fill();

    ctx.strokeStyle = "rgba(255,255,255,0.14)";
    ctx.lineWidth = 2;
    roundRectPath(laneX, laneY, laneW, laneH, 18);
    ctx.stroke();

    ctx.fillStyle = "rgba(255,255,255,0.55)";
    ctx.font = "bold 16px Arial";
    ctx.fillText(label, laneX + 14, laneY + 28);
  }

  function drawLane(cellX, cellY, cellW, cellH, racer) {
    const pad = 20;
    const laneX = cellX + pad;
    const laneY = cellY + pad;
    const laneW = cellW - pad * 2;
    const laneH = cellH - pad * 2;

    // lane background
    ctx.fillStyle = "#dff8ff";
    roundRectPath(laneX, laneY, laneW, laneH, 18);
    ctx.fill();

    // subtle glossy top
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    roundRectPath(laneX + 1, laneY + 1, laneW - 2, laneH * 0.26, 18);
    ctx.fill();

    // ground
    const groundY = laneY + laneH * 0.80;
    ctx.fillStyle = "#79d07d";
    ctx.fillRect(laneX, groundY, laneW, laneY + laneH - groundY);

    // lane stripes
    ctx.globalAlpha = 0.10;
    ctx.fillStyle = "#000";
    for (let i = 0; i < 6; i++) {
      const sy = groundY + i * 12;
      ctx.fillRect(laneX, sy, laneW, 4);
    }
    ctx.globalAlpha = 1.0;

    const startX = laneX + laneW * 0.08;
    const finishX = laneX + laneW * 0.88;

    // start line
    ctx.strokeStyle = "rgba(0,0,0,0.28)";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(startX, laneY + 14);
    ctx.lineTo(startX, laneY + laneH - 14);
    ctx.stroke();

    // finish line
    drawFinishLine(finishX, laneY, laneH);

    // name + progress
    ctx.fillStyle = "#111";
    ctx.font = "bold 18px Arial";
    ctx.fillText(racer.name, laneX + 12, laneY + 24);

    ctx.font = "14px Arial";
    ctx.fillText(
      `distance: ${racer.distance.toFixed(2)} / ${targetDistance.toFixed(2)}`,
      laneX + 12,
      laneY + 48
    );

    if (!racer.positions) {
      drawLaneBorder(laneX, laneY, laneW, laneH, racer);
      drawPlacementBadge(laneX, laneY, laneW, laneH, racer);
      return;
    }

    const bbox = computeBBox(racer.positions);
    const bw = Math.max(1e-6, bbox.maxX - bbox.minX);
    const bh = Math.max(1e-6, bbox.maxY - bbox.minY);

    // Make finish line appear on the right side instead of near the center.
    const usableW = laneW * 0.88;
    const usableH = laneH * 0.46;
    const worldViewW = Math.max(targetDistance * 1.1, bw * 2.8, 1.0);

    const zoomX = usableW / worldViewW;
    const zoomY = usableH / Math.max(bh, 0.35);
    const zoom = Math.min(zoomX, zoomY);

    function worldToScreen(x, y) {
      const sx = startX + x * zoom;
      const sy = groundY - (y - groundWorldY) * zoom;
      return [sx, sy];
    }

    // springs
    ctx.lineWidth = Math.max(1.0, zoom * 0.05);
    ctx.strokeStyle = "rgba(0,0,0,0.20)";
    ctx.beginPath();
    for (const s of racer.springs) {
      const a = s[0], b = s[1];
      const pa = racer.positions[a];
      const pb = racer.positions[b];
      if (!pa || !pb) continue;

      const [ax, ay] = worldToScreen(pa[0], pa[1]);
      const [bx, by] = worldToScreen(pb[0], pb[1]);
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
    }
    ctx.stroke();

    // voxels
    ctx.strokeStyle = "rgba(0,0,0,0.28)";
    ctx.lineWidth = Math.max(0.8, zoom * 0.03);
    for (const v of racer.voxels) {
      const ids = v.mass_ids;
      const p0 = racer.positions[ids[0]];
      const p1 = racer.positions[ids[1]];
      const p2 = racer.positions[ids[2]];
      const p3 = racer.positions[ids[3]];
      if (!p0 || !p1 || !p2 || !p3) continue;

      const [x0, y0] = worldToScreen(p0[0], p0[1]);
      const [x1, y1] = worldToScreen(p1[0], p1[1]);
      const [x2, y2] = worldToScreen(p2[0], p2[1]);
      const [x3, y3] = worldToScreen(p3[0], p3[1]);

      ctx.fillStyle = rgbToCss(v.color);
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
      ctx.lineTo(x3, y3);
      ctx.lineTo(x2, y2);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // target hint arrow near finish
    ctx.fillStyle = "rgba(0,0,0,0.18)";
    ctx.beginPath();
    ctx.moveTo(finishX - 24, groundY - 28);
    ctx.lineTo(finishX - 6, groundY - 20);
    ctx.lineTo(finishX - 24, groundY - 12);
    ctx.closePath();
    ctx.fill();

    drawLaneBorder(laneX, laneY, laneW, laneH, racer);
    drawPlacementBadge(laneX, laneY, laneW, laneH, racer);
  }

  function render() {
    resizeCanvas();
    drawBackground();

    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const topbarPx = Math.floor(58 * dpr);
    const gridTop = topbarPx + 8 * dpr;
    const gridBottomPad = 8 * dpr;
    const gridH = canvas.height - gridTop - gridBottomPad;
    const cellW = canvas.width / cols;
    const cellH = gridH / rows;

    const totalCells = rows * cols;
    for (let idx = 0; idx < totalCells; idx++) {
      const row = Math.floor(idx / cols);
      const col = idx % cols;
      const cellX = col * cellW;
      const cellY = gridTop + row * cellH;

      if (idx < racers.length) {
        drawLane(cellX, cellY, cellW, cellH, racers[idx]);
      } else {
        drawEmptyCell(cellX, cellY, cellW, cellH, "empty");
      }
    }

    hudTarget.textContent = Number(targetDistance || 0).toFixed(2);
    hudStep.textContent = String(latestStep);
    hudFps.textContent = Number(latestFps || 0).toFixed(1);

    if (finishOrder.length > 0 && racers[finishOrder[0]]) {
      hudWinner.textContent = racers[finishOrder[0]].name;
    } else {
      hudWinner.textContent = "-";
    }

    if (!raceStarted) {
      hudStatus.textContent = "waiting";
    } else if (raceFinished) {
      hudStatus.textContent = "finished";
    } else {
      hudStatus.textContent = "racing";
    }

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);

  startBtn.addEventListener("click", async () => {
    try {
      await fetch("/start", { method: "POST" });
    } catch (err) {
      console.error("Failed to start race:", err);
    }
  });

  const ev = new EventSource("/stream");
  ev.onmessage = (msg) => {
    let data;
    try {
      data = JSON.parse(msg.data);
    } catch {
      return;
    }

    if (data.type === "init") {
      rows = data.rows || 1;
      cols = data.cols || 4;
      targetDistance = data.target_distance || 0.0;
      groundWorldY = typeof data.ground_height === "number" ? data.ground_height : 0.0;

      raceStarted = !!data.started;
      raceFinished = !!data.race_finished;
      finishOrder = [];

      racers = (data.racers || []).map(r => ({
        id: r.id,
        name: r.name || `pokemon_${r.id}`,
        springs: r.springs || [],
        voxels: r.voxels || [],
        positions: null,
        distance: 0.0,
        finished: false,
        rank: null,
      }));

      latestStep = 0;
      latestFps = 0;
      return;
    }

    if (data.type === "step") {
      latestStep = data.step || 0;
      latestFps = data.fps || 0.0;
      raceStarted = !!data.started;
      raceFinished = !!data.race_finished;
      finishOrder = data.finish_order || [];

      for (const rr of data.racers || []) {
        const racer = racers[rr.id];
        if (!racer) continue;
        racer.positions = rr.positions || null;
        racer.distance = rr.distance || 0.0;
        racer.finished = !!rr.finished;
        racer.rank = rr.rank ?? null;
      }
    }
  };
})();