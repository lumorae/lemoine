(function () {
  const LEMON_BODY_D = "M193.96,264.42h-.02c-41.42,0-79.49-24.29-97-61.86-.74-1.58-1.43-3.19-2.1-4.82l-.25-.51c-2.07-3.65-4.07-6.94-7.34-9.7-1.37-1.16-3.46-2.25-5.69-3.39-5.69-2.95-13.48-6.98-17.46-16.72-1.44-3.51-1.79-8.64-1.67-11.23.44-9.38,7.43-19.52,16.25-23.61.56-.26,1.22-.55,1.95-.86,1.52-.65,3.42-1.45,4.57-2.29,4.48-3.22,7.07-7.23,9.75-12.63,15.27-37.22,49.58-62.48,89.61-65.98.75-.07,1.49-.12,2.24-.17.95-.06,1.92-.12,2.88-.16,1.16-.05,2.31-.07,3.47-.09l.8-.02.79.02c1.55.02,2.96.05,4.37.11l.58.04c11.96.66,23.38,3.21,34.24,7.59,3.26,1.31,6.47,2.8,9.56,4.42,14.84,7.59,27.17,17.72,35.58,29.28,3.11,4.28,6.7,10.33,9.15,14.66,1.26,2.2,2.36,4.45,3.42,6.61,3.35,6.82,6.25,12.7,13.38,17.23.61.39,1.63.85,2.71,1.33,3.95,1.76,9.91,4.44,14.06,11.56,5.02,8.62,4.88,20.45-.36,28.79-4.26,6.76-10.23,9.56-14.59,11.61-2.14.99-3.98,1.86-5.38,3-4.15,3.36-6.45,7.05-8.58,11.56-.9,2.17-1.86,4.29-2.85,6.3-1.86,3.8-4.01,7.59-6.41,11.26-8.2,12.57-19.2,23.51-31.81,31.63-10.56,6.8-22.13,11.65-34.38,14.4-7.74,1.73-15.64,2.62-23.48,2.62ZM194.09,68.52h-.8c-.96.02-1.92.05-2.89.09-.79.03-1.59.07-2.39.13-.64.05-1.26.09-1.88.14-33.34,2.91-61.91,24.01-74.54,55.08l-.26.59c-3.33,6.75-7.51,13.8-15.54,19.59-2.8,2.01-5.84,3.31-8.07,4.25-.52.22-1,.43-1.41.61-3.06,1.42-5.69,5.87-5.79,8.03-.05,1.05.19,3.05.4,3.71,1.33,3.25,4.14,4.84,8.97,7.34,2.86,1.49,6.11,3.17,9.03,5.63,5.55,4.69,8.7,9.81,11.45,14.65.27.49.5.96.73,1.43l.41.9c.57,1.43,1.18,2.83,1.83,4.22,14.55,31.23,46.19,51.41,80.6,51.42h.02c6.51,0,13.08-.74,19.53-2.19,10.16-2.28,19.76-6.3,28.54-11.95,10.48-6.76,19.63-15.85,26.45-26.3,1.99-3.06,3.78-6.21,5.33-9.35.84-1.71,1.67-3.54,2.43-5.42l.19-.42c2.65-5.63,6.35-12.2,13.67-18.12,3.11-2.51,6.28-4,9.08-5.32,3.63-1.7,5.59-2.69,6.96-4.87,1.89-3.01,1.49-7.55.04-10.04-1.17-2-2.71-2.76-5.82-4.15-1.55-.69-3.3-1.48-5.02-2.57-11.42-7.25-16.12-16.83-19.91-24.52-.99-2.01-1.92-3.91-2.91-5.64-3.16-5.55-6.01-10.16-8.06-12.96-8.51-11.7-20.61-19.43-29.25-23.85-2.64-1.38-5.31-2.62-8.02-3.71-9-3.63-18.49-5.75-28.19-6.29l-.74-.05c-1.14-.05-2.32-.07-3.5-.08l-.65-.02Z";
  const LEAF_D = "M89.87,61.01c-2.9-4.85-6.67-10.58-10.92-10.58-4.61,0-9.54,8.53-11.77,12.77-1.98,3.77-2.85,6.48-3.7,10.08-.83,3.53-1.12,6.59-1.07,9.83-.05,3.25.24,6.3,1.07,9.83.84,3.6,1.72,6.32,3.7,10.07,2.22,4.24,7.16,12.77,11.77,12.77,4.25,0,8.02-5.74,10.92-10.58,3.85-6.43,5.74-14.26,5.7-22.1.03-7.84-1.85-15.67-5.7-22.1Z";

  const VIEW_W = 387.17;
  const VIEW_H = 314.92;
  const CORAL = "#CC3565";
  const CREAM = "#f3efe1";
  const BG = "#191919";

  const logoPath = new Path2D(LEMON_BODY_D);
  const leafPath = new Path2D(LEAF_D);

  const digitalPalette = [
    "#CC3565",
    "#e95b78",
    "#d66d45",
    "#d6a33a",
    "#63a879",
    "#4c8eab",
    "#7760b6",
    "#e58aa8",
    "#c98c72",
    "#9eb38c",
    "#f2cfc8",
    CREAM
  ];

  const organicPalette = [
    "#CC3565",
    "#e95b78",
    "#d66d45",
    "#d6a33a",
    "#63a879",
    "#4c8eab",
    "#7760b6",
    "#e58aa8",
    "#c98c72",
    "#9eb38c",
    "#4e8f84",
    "#aa8e73",
    "#f2cfc8",
    CREAM
  ];

  const sacredPalette = [
    CORAL,
    "#e0a240",
    "#c98c72",
    "#f2cfc8",
    CREAM,
    "#63a879",
    "#4c8eab",
    "#7760b6"
  ];

  function init() {
    const root = document.getElementById("lemoine_explosion_root");
    if (!root || root.dataset.ready === "true") return;
    root.dataset.ready = "true";

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    root.appendChild(canvas);

    Object.assign(canvas.style, {
      display: "block",
      width: "100%",
      height: "100%",
      touchAction: "none",
      userSelect: "none"
    });

    let w = 1;
    let h = 1;
    let dpr = 1;
    let logoScale = 1;
    let logoX = 0;
    let logoY = 0;
    let logoCenterX = 0;
    let logoCenterY = 0;
    let logoWorldHalf = 1;
    let pressing = false;
    let pressOnLogo = false;
    let pointerX = 0;
    let pointerY = 0;
    let pressVisual = 0;
    let lastTime = performance.now();
    let autoTimer = 0;
    let nextAuto = 24 + Math.random() * 16;
    let dragAccumulator = 0;

    const particles = [];
    const sacred = [];
    const maxParticles = 4300;
    const maxSacred = 46;

    function resize() {
      const rect = root.getBoundingClientRect();
      w = Math.max(1, rect.width);
      h = Math.max(1, rect.height);
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const targetLogoH = Math.min(h * 0.46, w * 0.34, 420);
      logoScale = targetLogoH / VIEW_H;
      logoX = w / 2 - (VIEW_W * logoScale) / 2;
      logoY = h / 2 - (VIEW_H * logoScale) / 2;
      logoCenterX = logoX + (VIEW_W * logoScale) / 2;
      logoCenterY = logoY + (VIEW_H * logoScale) / 2;
      logoWorldHalf = (VIEW_W * logoScale) / 2;
    }

    function rand(min, max) {
      return min + Math.random() * (max - min);
    }

    function pick(arr) {
      return arr[Math.floor(Math.random() * arr.length)];
    }

    function clamp01(n) {
      return Math.max(0, Math.min(1, n));
    }

    function smoothstep(e0, e1, x) {
      const t = clamp01((x - e0) / (e1 - e0));
      return t * t * (3 - 2 * t);
    }

    function toLocal(x, y) {
      return {
        x: (x - logoX) / logoScale,
        y: (y - logoY) / logoScale
      };
    }

    function isInsideLogo(x, y) {
      const p = toLocal(x, y);
      try {
        return ctx.isPointInPath(logoPath, p.x, p.y, "evenodd") || ctx.isPointInPath(leafPath, p.x, p.y, "evenodd");
      } catch (error) {
        return p.x >= 0 && p.x <= VIEW_W && p.y >= 0 && p.y <= VIEW_H;
      }
    }

    function sideBlend(x) {
      const rel = (x - logoCenterX) / Math.max(1, logoWorldHalf);
      return smoothstep(-0.25, 0.35, rel);
    }

    function addParticle(p) {
      particles.push(p);
      if (particles.length > maxParticles) particles.splice(0, particles.length - maxParticles);
    }

    function emitPixel(x, y, strength = 1) {
      const angle = rand(0, Math.PI * 2);
      const speed = rand(65, 420) * strength;
      const chunky = Math.random() < 0.18;
      addParticle({
        type: Math.random() < 0.15 ? "cube" : "pixel",
        x: x + rand(-8, 8),
        y: y + rand(-8, 8),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: rand(1.4, 4.4),
        maxLife: 0,
        size: chunky ? rand(8, 16) : rand(2, 7),
        color: pick(digitalPalette),
        alpha: 0,
        rot: rand(0, Math.PI * 2),
        spin: rand(-4.5, 4.5),
        seed: rand(0, 1000),
        dissolve: chunky && Math.random() < 0.55
      });
      particles[particles.length - 1].maxLife = particles[particles.length - 1].life;
    }

    function emitSoftPaint(x, y, strength = 1, burst = false) {
      const angle = rand(0, Math.PI * 2);
      const speed = rand(45, burst ? 520 : 280) * strength;
      const isBloom = Math.random() < (burst ? 0.34 : 0.18);
      addParticle({
        type: isBloom ? "bloom" : Math.random() < 0.55 ? "splatter" : "mist",
        x: x + rand(-12, 12),
        y: y + rand(-12, 12),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed + rand(-40, 40),
        life: isBloom ? rand(1.2, 3.2) : rand(1.6, 5.6),
        maxLife: 0,
        size: isBloom ? rand(28, 92) : rand(4, 26),
        color: pick(organicPalette),
        alpha: 0,
        rot: rand(0, Math.PI * 2),
        spin: rand(-1.4, 1.4),
        seed: rand(0, 1000),
        lobes: 5 + Math.floor(Math.random() * 6)
      });
      particles[particles.length - 1].maxLife = particles[particles.length - 1].life;
    }

    function emitStreak(x, y, strength = 1) {
      const angle = rand(-0.75, 0.75);
      const speed = rand(180, 560) * strength;
      addParticle({
        type: "streak",
        x: x + rand(-12, 12),
        y: y + rand(-12, 12),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed + rand(-90, 90),
        life: rand(0.7, 2.0),
        maxLife: 0,
        size: rand(10, 34),
        length: rand(24, 96),
        color: pick(organicPalette),
        alpha: 0,
        rot: angle,
        spin: rand(-0.4, 0.4),
        seed: rand(0, 1000)
      });
      particles[particles.length - 1].maxLife = particles[particles.length - 1].life;
    }

    function sacredAnchor(x, y, leftStrength) {
      const anchors = [
        { x: logoCenterX - logoWorldHalf * 0.98, y: logoCenterY - logoWorldHalf * 0.46 },
        { x: logoCenterX - logoWorldHalf * 0.82, y: logoCenterY - logoWorldHalf * 0.22 },
        { x: logoCenterX - logoWorldHalf * 0.96, y: logoCenterY + logoWorldHalf * 0.04 },
        { x: logoCenterX - logoWorldHalf * 0.70, y: logoCenterY + logoWorldHalf * 0.30 },
        { x: logoCenterX - logoWorldHalf * 0.98, y: logoCenterY + logoWorldHalf * 0.48 },
        { x: logoCenterX - logoWorldHalf * 0.42, y: logoCenterY - logoWorldHalf * 0.42 },
        { x: logoCenterX - logoWorldHalf * 0.36, y: logoCenterY + logoWorldHalf * 0.44 }
      ];

      if (Math.random() < 0.82) {
        const a = pick(anchors);
        return {
          x: a.x + rand(-40, 40),
          y: a.y + rand(-40, 40)
        };
      }

      return {
        x: x - rand(80, logoWorldHalf * (0.42 + leftStrength * 0.32)),
        y: y + rand(-110, 110)
      };
    }

    function emitSacred(x, y, count = 1, leftStrength = 1) {
      for (let i = 0; i < count; i++) {
        const a = sacredAnchor(x, y, leftStrength);
        const angle = Math.PI + rand(-1.2, 1.2);
        const speed = rand(8, 44) * (0.7 + leftStrength);
        sacred.push({
          kind: Math.floor(Math.random() * 4),
          x: a.x,
          y: a.y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: rand(3.8, 7.2),
          maxLife: 0,
          scale: rand(42, 112),
          color: pick(sacredPalette),
          rot: rand(0, Math.PI * 2),
          spin: rand(-0.85, 0.85),
          phase: rand(0, 1000),
          wobble: rand(0.8, 1.6),
          line: rand(0.7, 1.45)
        });
        sacred[sacred.length - 1].maxLife = sacred[sacred.length - 1].life;
      }
      if (sacred.length > maxSacred) sacred.splice(0, sacred.length - maxSacred);
    }

    function emit(x, y, count, organicChance, options = {}) {
      const rightBoost = organicChance;
      const leftStrength = 1 - organicChance;
      const burst = !!options.burst;

      for (let i = 0; i < count; i++) {
        const r = Math.random();
        if (r < rightBoost) {
          if (Math.random() < 0.22 + rightBoost * 0.24) emitStreak(x, y, 0.7 + rightBoost * 0.8);
          else emitSoftPaint(x, y, 0.8 + rightBoost * 0.9, burst || rightBoost > 0.62);
        } else {
          emitPixel(x, y, 0.7 + leftStrength * 0.8);
        }
      }

      if (leftStrength > 0.35 && count > 60 && Math.random() < 0.86) {
        emitSacred(x, y, 1 + Math.floor(Math.random() * 2), leftStrength);
      }

      if (rightBoost > 0.52 && count > 60) {
        const extra = Math.floor(18 + rightBoost * 56);
        for (let i = 0; i < extra; i++) emitSoftPaint(x, y, 1 + rightBoost, true);
      }
    }

    function emitAmbient() {
      const zone = Math.random();
      let x;
      let y;
      let organic;

      if (zone < 0.34) {
        x = logoCenterX - logoWorldHalf * rand(0.45, 0.96);
        y = logoCenterY + rand(-logoWorldHalf * 0.42, logoWorldHalf * 0.48);
        organic = rand(0.08, 0.28);
      } else if (zone < 0.72) {
        x = logoCenterX + logoWorldHalf * rand(0.25, 0.92);
        y = logoCenterY + rand(-logoWorldHalf * 0.42, logoWorldHalf * 0.48);
        organic = rand(0.68, 0.96);
      } else {
        x = logoCenterX + rand(-logoWorldHalf * 0.32, logoWorldHalf * 0.32);
        y = logoCenterY + rand(-logoWorldHalf * 0.32, logoWorldHalf * 0.32);
        organic = rand(0.34, 0.66);
      }

      emit(x, y, 100 + Math.floor(Math.random() * 150), organic, { burst: true });
      if (organic < 0.45 && Math.random() < 0.72) emitSacred(x, y, 1 + Math.floor(Math.random() * 2), 1 - organic);
    }

    function pointerPos(event) {
      const rect = canvas.getBoundingClientRect();
      return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      };
    }

    canvas.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      const p = pointerPos(event);
      pointerX = p.x;
      pointerY = p.y;
      if (!isInsideLogo(pointerX, pointerY)) return;

      pressing = true;
      pressOnLogo = true;
      canvas.setPointerCapture?.(event.pointerId);
      const organic = sideBlend(pointerX);
      emit(pointerX, pointerY, 280, organic, { burst: true });
      if (Math.random() < 0.35) emitSacred(pointerX, pointerY, 1, 1 - organic);
    });

    canvas.addEventListener("pointermove", (event) => {
      const p = pointerPos(event);
      pointerX = p.x;
      pointerY = p.y;
      const inside = isInsideLogo(pointerX, pointerY);
      canvas.style.cursor = inside ? "pointer" : "default";
      if (pressing) pressOnLogo = inside;
    });

    window.addEventListener("pointerup", () => {
      pressing = false;
      pressOnLogo = false;
      dragAccumulator = 0;
    });

    window.addEventListener("pointercancel", () => {
      pressing = false;
      pressOnLogo = false;
      dragAccumulator = 0;
    });

    function drawLogo(time) {
      const target = pressing && pressOnLogo ? 1 : 0;
      pressVisual += (target - pressVisual) * 0.18;
      const pulse = 1 - pressVisual * 0.018;
      const breathe = 1 + Math.sin(time * 0.0007) * 0.0025;
      const s = logoScale * pulse * breathe;
      const x = logoCenterX - (VIEW_W * s) / 2;
      const y = logoCenterY - (VIEW_H * s) / 2;

      ctx.save();
      ctx.translate(x, y);
      ctx.scale(s, s);
      ctx.fillStyle = CORAL;
      ctx.shadowColor = "rgba(204, 53, 101, 0.34)";
      ctx.shadowBlur = 24 * pressVisual;
      ctx.fill(logoPath, "evenodd");
      ctx.fill(leafPath, "evenodd");
      ctx.restore();
    }

    function updateParticle(p, dt, time) {
      p.life -= dt;
      if (p.life <= 0) return false;

      const age = 1 - p.life / p.maxLife;
      const fadeIn = Math.min(1, age * 8);
      const fadeOut = Math.pow(p.life / p.maxLife, p.type === "bloom" ? 1.9 : 1.25);
      p.alpha = Math.min(fadeIn, fadeOut);

      const turb = Math.sin(time * 0.0014 + p.seed) * 18 + Math.sin(time * 0.003 + p.seed * 0.4) * 7;

      if (p.type === "mist" || p.type === "bloom" || p.type === "splatter") {
        p.vx += Math.cos(p.seed + time * 0.001) * dt * 18;
        p.vy += Math.sin(p.seed + time * 0.0012) * dt * 18 - dt * 10;
        p.vx *= 0.984;
        p.vy *= 0.984;
      } else if (p.type === "streak") {
        p.vx *= 0.975;
        p.vy *= 0.975;
      } else {
        p.vx += turb * dt;
        p.vy += Math.cos(time * 0.0016 + p.seed) * dt * 16;
        p.vx *= 0.982;
        p.vy *= 0.982;
      }

      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.rot += p.spin * dt;
      return true;
    }

    function drawParticle(p) {
      const a = p.alpha;
      if (a <= 0.01) return;

      ctx.save();
      ctx.globalAlpha = a;
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);

      if (p.type === "pixel") {
        const dissolve = p.dissolve && p.life / p.maxLife < 0.62;
        ctx.fillStyle = p.color;
        const cells = dissolve ? 3 : 1;
        const cell = p.size / cells;
        for (let ix = 0; ix < cells; ix++) {
          for (let iy = 0; iy < cells; iy++) {
            if (dissolve && Math.random() > p.life / p.maxLife + 0.18) continue;
            ctx.fillRect(-p.size / 2 + ix * cell, -p.size / 2 + iy * cell, cell * 0.9, cell * 0.9);
          }
        }
      }

      if (p.type === "cube") {
        ctx.strokeStyle = p.color;
        ctx.lineWidth = Math.max(1, p.size * 0.09);
        ctx.globalAlpha = a * 0.9;
        ctx.strokeRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.beginPath();
        ctx.moveTo(-p.size / 2, 0);
        ctx.lineTo(p.size / 2, 0);
        ctx.moveTo(0, -p.size / 2);
        ctx.lineTo(0, p.size / 2);
        ctx.stroke();
      }

      if (p.type === "mist" || p.type === "bloom") {
        const r = p.size * (p.type === "bloom" ? 1 + (1 - p.life / p.maxLife) * 0.7 : 1);
        const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
        g.addColorStop(0, p.color);
        g.addColorStop(0.42, p.color + "99");
        g.addColorStop(1, p.color + "00");
        ctx.globalAlpha = a * (p.type === "bloom" ? 0.42 : 0.62);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fill();
      }

      if (p.type === "splatter") {
        ctx.fillStyle = p.color;
        ctx.globalAlpha = a * 0.78;
        ctx.beginPath();
        const lobes = p.lobes || 7;
        for (let i = 0; i <= lobes; i++) {
          const t = (i / lobes) * Math.PI * 2;
          const rr = p.size * (0.52 + 0.44 * Math.sin(i * 12.989 + p.seed));
          const xx = Math.cos(t) * rr;
          const yy = Math.sin(t) * rr;
          if (i === 0) ctx.moveTo(xx, yy);
          else ctx.lineTo(xx, yy);
        }
        ctx.closePath();
        ctx.fill();
      }

      if (p.type === "streak") {
        ctx.strokeStyle = p.color;
        ctx.lineWidth = Math.max(1, p.size * 0.18);
        ctx.lineCap = "round";
        ctx.globalAlpha = a * 0.75;
        ctx.beginPath();
        ctx.moveTo(-p.length * 0.5, 0);
        ctx.lineTo(p.length * 0.5, 0);
        ctx.stroke();
      }

      ctx.restore();
    }

    function drawCircle(cx, cy, r, segments = 72) {
      ctx.beginPath();
      for (let i = 0; i <= segments; i++) {
        const t = (i / segments) * Math.PI * 2;
        const x = cx + Math.cos(t) * r;
        const y = cy + Math.sin(t) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    function drawGoldenSpiral() {
      ctx.beginPath();
      const turns = 4.35;
      const steps = 180;
      for (let i = 0; i <= steps; i++) {
        const t = (i / steps) * Math.PI * 2 * turns;
        const r = 0.018 * Math.pow(1.618, t / (Math.PI / 2));
        const x = Math.cos(t) * r;
        const y = Math.sin(t) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      drawCircle(0, 0, 0.82, 96);
      drawCircle(0, 0, 0.42, 96);
    }

    function drawFlowerOfLife() {
      const r = 0.28;
      const centers = [{ x: 0, y: 0 }];
      for (let i = 0; i < 6; i++) centers.push({ x: Math.cos((Math.PI * 2 * i) / 6) * r, y: Math.sin((Math.PI * 2 * i) / 6) * r });
      for (let i = 0; i < 6; i++) centers.push({ x: Math.cos((Math.PI * 2 * i) / 6) * r * 2, y: Math.sin((Math.PI * 2 * i) / 6) * r * 2 });
      for (let i = 0; i < 6; i++) centers.push({ x: Math.cos((Math.PI * 2 * i) / 6 + Math.PI / 6) * r * 1.72, y: Math.sin((Math.PI * 2 * i) / 6 + Math.PI / 6) * r * 1.72 });
      centers.forEach((c) => drawCircle(c.x, c.y, r, 72));
      drawCircle(0, 0, r * 3, 108);
    }

    function drawMetatron() {
      const nodes = [{ x: 0, y: 0 }];
      const r = 0.46;
      for (let i = 0; i < 6; i++) nodes.push({ x: Math.cos((Math.PI * 2 * i) / 6) * r, y: Math.sin((Math.PI * 2 * i) / 6) * r });
      for (let i = 0; i < 6; i++) nodes.push({ x: Math.cos((Math.PI * 2 * i) / 6 + Math.PI / 6) * r * 1.78, y: Math.sin((Math.PI * 2 * i) / 6 + Math.PI / 6) * r * 1.78 });
      nodes.forEach((n) => drawCircle(n.x, n.y, 0.14, 44));
      ctx.beginPath();
      for (let i = 1; i < nodes.length; i++) {
        ctx.moveTo(0, 0);
        ctx.lineTo(nodes[i].x, nodes[i].y);
      }
      for (let i = 1; i <= 6; i++) {
        const n = nodes[i];
        const next = nodes[i === 6 ? 1 : i + 1];
        ctx.moveTo(n.x, n.y);
        ctx.lineTo(next.x, next.y);
      }
      for (let i = 7; i < nodes.length; i++) {
        const n = nodes[i];
        const next = nodes[i === nodes.length - 1 ? 7 : i + 1];
        ctx.moveTo(n.x, n.y);
        ctx.lineTo(next.x, next.y);
      }
      ctx.stroke();
    }

    function drawTorusWire(time, phase) {
      for (let j = 0; j < 18; j++) {
        const ph = (j / 18) * Math.PI * 2 + Math.sin(time * 0.001 + phase) * 0.12;
        ctx.beginPath();
        for (let i = 0; i <= 86; i++) {
          const t = (i / 86) * Math.PI * 2;
          const warp = Math.sin(t * 2 + ph) * 0.12;
          const rx = 0.82 + warp;
          const ry = 0.45 + Math.cos(ph) * 0.08;
          const x = Math.cos(t + ph * 0.1) * rx;
          const y = Math.sin(t) * ry;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      drawCircle(0, 0, 0.9, 108);
      drawCircle(0, 0, 0.46, 108);
    }

    function updateSacredShape(s, dt) {
      s.life -= dt;
      if (s.life <= 0) return false;
      s.vx *= 0.988;
      s.vy *= 0.988;
      s.x += s.vx * dt;
      s.y += s.vy * dt;
      s.rot += s.spin * dt;
      return true;
    }

    function drawSacredShape(s, time) {
      const age = 1 - s.life / s.maxLife;
      const fadeIn = Math.min(1, age * 5);
      const fadeOut = Math.min(1, (s.life / s.maxLife) * 2.1);
      const alpha = Math.min(fadeIn, fadeOut) * 0.68;
      const driftX = Math.sin(time * 0.0012 + s.phase) * 7 + Math.sin(time * 0.0024 + s.phase * 0.7) * 3;
      const driftY = Math.cos(time * 0.001 + s.phase) * 7 + Math.cos(time * 0.0021 + s.phase * 0.9) * 3;
      const pulse = 1 + Math.sin(time * 0.0022 + s.phase) * 0.08 + Math.sin(time * 0.0051 + s.phase) * 0.026;

      ctx.save();
      ctx.translate(s.x + driftX, s.y + driftY);
      ctx.rotate(s.rot + Math.sin(time * 0.0007 + s.phase) * 0.18);
      ctx.scale(s.scale * pulse, s.scale * pulse);
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = s.color;
      ctx.lineWidth = s.line / s.scale;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      if (s.kind === 0) drawGoldenSpiral();
      else if (s.kind === 1) drawFlowerOfLife();
      else if (s.kind === 2) drawMetatron();
      else drawTorusWire(time, s.phase);

      ctx.restore();
    }

    function drawGrain() {
      ctx.save();
      ctx.globalAlpha = 0.035;
      ctx.fillStyle = CREAM;
      const count = Math.floor((w * h) / 26000);
      for (let i = 0; i < count; i++) {
        ctx.fillRect(Math.random() * w, Math.random() * h, 1, 1);
      }
      ctx.restore();
    }

    function frame(time) {
      const dt = Math.min(0.05, (time - lastTime) / 1000 || 0.016);
      lastTime = time;

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = BG;
      ctx.fillRect(0, 0, w, h);

      if (pressing && pressOnLogo) {
        const organic = sideBlend(pointerX);
        dragAccumulator += dt * 720;
        const amount = Math.floor(dragAccumulator);
        dragAccumulator -= amount;
        if (amount > 0) emit(pointerX, pointerY, amount, organic, { burst: organic > 0.55 });
      }

      if (!pressing) {
        autoTimer += dt;
        if (autoTimer >= nextAuto) {
          autoTimer = 0;
          nextAuto = 24 + Math.random() * 16;
          emitAmbient();
        }
      }

      for (let i = particles.length - 1; i >= 0; i--) {
        if (!updateParticle(particles[i], dt, time)) particles.splice(i, 1);
      }

      for (let i = sacred.length - 1; i >= 0; i--) {
        if (!updateSacredShape(sacred[i], dt)) sacred.splice(i, 1);
      }

      for (const p of particles) drawParticle(p);
      for (const s of sacred) drawSacredShape(s, time);
      drawLogo(time);
      drawGrain();

      requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener("resize", resize);
    requestAnimationFrame(frame);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
