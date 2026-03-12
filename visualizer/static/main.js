(() => {
  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d", { alpha: false });

  const hudName = document.getElementById("hudName");
  const hudStep = document.getElementById("hudStep");
  const hudFps  = document.getElementById("hudFps");

  // ---------- DPI-aware resize ----------
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

  // ---------- Camera / Zoom ----------
  // where the world origin appears on screen
  const X_ANCHOR = 0.30;  // object tends to enter from left
  const Y_ANCHOR = 0.62;

  const PAD_PX = 90;
  const ZOOM_SMOOTH = 0.12;
  const ZOOM_MIN = 20;
  const ZOOM_MAX = 2000;

  // Pan sweep settings
  const PAN_SMOOTH = 0.10;
  const PAN_SPAN_MULT = 10.0; // sweep distance = robot_width * mult

  let camX = 0, camY = 0;  // world center used by mapping
  let zoom = 250;

  let runStartCamX = 0;
  let runEndCamX = 0;

  let maxSteps = 1;

  function computeBBox(positions) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const p of positions) {
      const x = p[0], y = p[1];
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
    if (!isFinite(minX)) minX = 0, maxX = 1, minY = 0, maxY = 1;
    return { minX, maxX, minY, maxY };
  }

  function resetPanRange(positions) {
    const { minX, maxX, minY, maxY } = computeBBox(positions);
    const w = Math.max(1e-6, maxX - minX);

    // start a bit before the robot
    runStartCamX = minX - w * 1.0;
    runEndCamX = runStartCamX + w * PAN_SPAN_MULT;

    // initialize camera near start
    camX = runStartCamX;
    camY = 0.5 * (minY + maxY);
  }

  function updateCameraAndZoom(positions, step) {
    const { minX, maxX, minY, maxY } = computeBBox(positions);

    // zoom = fit bbox to screen
    const bw = Math.max(1e-6, maxX - minX);
    const bh = Math.max(1e-6, maxY - minY);

    const zx = (canvas.width  - 2 * PAD_PX) / bw;
    const zy = (canvas.height - 2 * PAD_PX) / bh;
    let targetZoom = Math.min(zx, zy);
    targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, targetZoom));
    zoom += (targetZoom - zoom) * ZOOM_SMOOTH;

    // X: sweep left -> right by progress
    const p = Math.max(0, Math.min(1, step / Math.max(1, maxSteps)));
    const targetCamX = runStartCamX + (runEndCamX - runStartCamX) * p;
    camX += (targetCamX - camX) * PAN_SMOOTH;

    // Y: gentle follow (keeps it in view)
    const cy = 0.5 * (minY + maxY);
    camY += (cy - camY) * 0.15;
  }

  function worldToScreen(x, y) {
    const sx = (x - camX) * zoom + canvas.width * X_ANCHOR;
    const sy = canvas.height * Y_ANCHOR - (y - camY) * zoom;
    return [sx, sy];
  }

  // ---------- State from server ----------
  let springs = [];
  let voxels = [];
  let pokemonName = "robot";

  let latestPositions = null;
  let latestStep = 0;
  let latestFps = 0;
  let havePanRange = false;

  // ---------- Drawing ----------
  function drawBackground() {
    const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
    g.addColorStop(0, "#8fd0ff");
    g.addColorStop(1, "#d9f0ff");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const groundY = Math.floor(canvas.height * 0.78);
    ctx.fillStyle = "#7ad07a";
    ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);

    ctx.globalAlpha = 0.12;
    ctx.fillStyle = "#000";
    for (let i = 0; i < 7; i++) {
      const y = groundY + i * 28;
      ctx.fillRect(0, y, canvas.width, 10);
    }
    ctx.globalAlpha = 1.0;
  }

  function rgbToCss(rgb) {
    return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
  }

  function drawSprings(positions) {
    ctx.lineWidth = Math.max(1.0, zoom * 0.005);
    ctx.strokeStyle = "rgba(0,0,0,0.22)";
    ctx.beginPath();
    for (const s of springs) {
      const a = s[0], b = s[1];
      const pa = positions[a], pb = positions[b];
      if (!pa || !pb) continue;
      const [ax, ay] = worldToScreen(pa[0], pa[1]);
      const [bx, by] = worldToScreen(pb[0], pb[1]);
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
    }
    ctx.stroke();
  }

  function drawVoxels(positions) {
    const outline = Math.max(0.8, zoom * 0.003);
    ctx.lineWidth = outline;
    ctx.strokeStyle = "rgba(0,0,0,0.28)";

    for (const v of voxels) {
      const ids = v.mass_ids;
      const p0 = positions[ids[0]];
      const p1 = positions[ids[1]];
      const p2 = positions[ids[2]];
      const p3 = positions[ids[3]];
      if (!p0 || !p1 || !p2 || !p3) continue;

      const [x0, y0] = worldToScreen(p0[0], p0[1]);
      const [x1, y1] = worldToScreen(p1[0], p1[1]);
      const [x3, y3] = worldToScreen(p3[0], p3[1]);
      const [x2, y2] = worldToScreen(p2[0], p2[1]);

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
  }

  function render() {
    resizeCanvas();
    drawBackground();

    if (latestPositions) {
      if (!havePanRange) {
        resetPanRange(latestPositions);
        havePanRange = true;
      }
      updateCameraAndZoom(latestPositions, latestStep);
      drawSprings(latestPositions);
      drawVoxels(latestPositions);
    }

    hudName.textContent = pokemonName;
    hudStep.textContent = String(latestStep);
    hudFps.textContent = (latestFps || 0).toFixed(1);

    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);

  // ---------- SSE ----------
  const ev = new EventSource("/stream");
  ev.onmessage = (msg) => {
    let data;
    try { data = JSON.parse(msg.data); } catch { return; }

    if (data.type === "init") {
      springs = data.springs || [];
      voxels = data.voxels || [];
      pokemonName = data.pokemon_name || "robot";
      maxSteps = data.max_steps || 1;

      latestPositions = null;
      latestStep = 0;
      latestFps = 0;
      havePanRange = false;

      camX = 0; camY = 0; zoom = 250;
      return;
    }

    if (data.type === "step") {
      latestPositions = data.positions || null;
      latestStep = data.step || 0;
      latestFps = data.fps || 0;

      // if backend says reset, rebuild sweep window next frame
      if (data.reset) {
        havePanRange = false;
      }
      return;
    }
  };
})();