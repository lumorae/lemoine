import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

function initLemoineExplosion() {
  const mount = document.getElementById("lemoine_explosion_root");
  if (!mount || mount.dataset.ready === "true") return;
  mount.dataset.ready = "true";

  const LEMON_BODY_D = "M193.96,264.42h-.02c-41.42,0-79.49-24.29-97-61.86-.74-1.58-1.43-3.19-2.1-4.82l-.25-.51c-2.07-3.65-4.07-6.94-7.34-9.7-1.37-1.16-3.46-2.25-5.69-3.39-5.69-2.95-13.48-6.98-17.46-16.72-1.44-3.51-1.79-8.64-1.67-11.23.44-9.38,7.43-19.52,16.25-23.61.56-.26,1.22-.55,1.95-.86,1.52-.65,3.42-1.45,4.57-2.29,4.48-3.22,7.07-7.23,9.75-12.63,15.27-37.22,49.58-62.48,89.61-65.98.75-.07,1.49-.12,2.24-.17.95-.06,1.92-.12,2.88-.16,1.16-.05,2.31-.07,3.47-.09l.8-.02.79.02c1.55.02,2.96.05,4.37.11l.58.04c11.96.66,23.38,3.21,34.24,7.59,3.26,1.31,6.47,2.8,9.56,4.42,14.84,7.59,27.17,17.72,35.58,29.28,3.11,4.28,6.7,10.33,9.15,14.66,1.26,2.2,2.36,4.45,3.42,6.61,3.35,6.82,6.25,12.7,13.38,17.23.61.39,1.63.85,2.71,1.33,3.95,1.76,9.91,4.44,14.06,11.56,5.02,8.62,4.88,20.45-.36,28.79-4.26,6.76-10.23,9.56-14.59,11.61-2.14.99-3.98,1.86-5.38,3-4.15,3.36-6.45,7.05-8.58,11.56-.9,2.17-1.86,4.29-2.85,6.3-1.86,3.8-4.01,7.59-6.41,11.26-8.2,12.57-19.2,23.51-31.81,31.63-10.56,6.8-22.13,11.65-34.38,14.4-7.74,1.73-15.64,2.62-23.48,2.62ZM194.09,68.52h-.8c-.96.02-1.92.05-2.89.09-.79.03-1.59.07-2.39.13-.64.05-1.26.09-1.88.14-33.34,2.91-61.91,24.01-74.54,55.08l-.26.59c-3.33,6.75-7.51,13.8-15.54,19.59-2.8,2.01-5.84,3.31-8.07,4.25-.52.22-1,.43-1.41.61-3.06,1.42-5.69,5.87-5.79,8.03-.05,1.05.19,3.05.4,3.71,1.33,3.25,4.14,4.84,8.97,7.34,2.86,1.49,6.11,3.17,9.03,5.63,5.55,4.69,8.7,9.81,11.45,14.65.27.49.5.96.73,1.43l.41.9c.57,1.43,1.18,2.83,1.83,4.22,14.55,31.23,46.19,51.41,80.6,51.42h.02c6.51,0,13.08-.74,19.53-2.19,10.16-2.28,19.76-6.3,28.54-11.95,10.48-6.76,19.63-15.85,26.45-26.3,1.99-3.06,3.78-6.21,5.33-9.35.84-1.71,1.67-3.54,2.43-5.42l.19-.42c2.65-5.63,6.35-12.2,13.67-18.12,3.11-2.51,6.28-4,9.08-5.32,3.63-1.7,5.59-2.69,6.96-4.87,1.89-3.01,1.49-7.55.04-10.04-1.17-2-2.71-2.76-5.82-4.15-1.55-.69-3.3-1.48-5.02-2.57-11.42-7.25-16.12-16.83-19.91-24.52-.99-2.01-1.92-3.91-2.91-5.64-3.16-5.55-6.01-10.16-8.06-12.96-8.51-11.7-20.61-19.43-29.25-23.85-2.64-1.38-5.31-2.62-8.02-3.71-9-3.63-18.49-5.75-28.19-6.29l-.74-.05c-1.14-.05-2.32-.07-3.5-.08l-.65-.02Z";
  const LEAF_D = "M89.87,61.01c-2.9-4.85-6.67-10.58-10.92-10.58-4.61,0-9.54,8.53-11.77,12.77-1.98,3.77-2.85,6.48-3.7,10.08-.83,3.53-1.12,6.59-1.07,9.83-.05,3.25.24,6.3,1.07,9.83.84,3.6,1.72,6.32,3.7,10.07,2.22,4.24,7.16,12.77,11.77,12.77,4.25,0,8.02-5.74,10.92-10.58,3.85-6.43,5.74-14.26,5.7-22.1.03-7.84-1.85-15.67-5.7-22.1Z";

  const VIEW_W = 387.17;
  const VIEW_H = 314.92;
  const CORAL_HEX = "#CC3565";
  const PALE_PINK = [0.949, 0.812, 0.784];
  const BRAND_CREAM = [0.953, 0.937, 0.882];

  const digitalPalette = [
    { c: [0.80, 0.21, 0.40], w: 6 },
    { c: [0.95, 0.22, 0.42], w: 2 },
    { c: [0.96, 0.44, 0.26], w: 2 },
    { c: [0.90, 0.68, 0.22], w: 2 },
    { c: [0.32, 0.68, 0.52], w: 2 },
    { c: [0.22, 0.56, 0.78], w: 2 },
    { c: [0.48, 0.36, 0.78], w: 1 },
    { c: [0.88, 0.48, 0.68], w: 2 },
    { c: [0.78, 0.55, 0.45], w: 2 },
    { c: [0.55, 0.65, 0.55], w: 2 },
    { c: PALE_PINK, w: 2 },
    { c: BRAND_CREAM, w: 2 }
  ];

  const organicPalette = [
    [0.80, 0.21, 0.40],
    [0.95, 0.22, 0.42],
    [0.96, 0.44, 0.26],
    [0.90, 0.68, 0.22],
    [0.32, 0.68, 0.52],
    [0.22, 0.56, 0.78],
    [0.48, 0.36, 0.78],
    [0.88, 0.48, 0.68],
    [0.78, 0.55, 0.45],
    [0.55, 0.65, 0.55],
    [0.30, 0.55, 0.50],
    [0.65, 0.55, 0.45],
    PALE_PINK,
    BRAND_CREAM
  ];

  const sacredPalette = [
    { c: [0.80, 0.21, 0.40], w: 5 },  // Lemoine coral #CC3565
    { c: [0.92, 0.63, 0.18], w: 4 },  // warm gold
    { c: BRAND_CREAM, w: 2 },          // cream, never pure white
    { c: PALE_PINK, w: 2 },
    { c: [0.30, 0.55, 0.50], w: 2 },
    { c: [0.22, 0.56, 0.78], w: 2 },
    { c: [0.48, 0.36, 0.78], w: 1 }
  ];

  const sacredTotalW = sacredPalette.reduce((sum, item) => sum + item.w, 0);

  function pickSacredColor() {
    let r = Math.random() * sacredTotalW;
    for (const p of sacredPalette) {
      r -= p.w;
      if (r <= 0) return p.c;
    }
    return sacredPalette[0].c;
  }

  const totalW = digitalPalette.reduce((sum, item) => sum + item.w, 0);

  function pickDigitalColor() {
    let r = Math.random() * totalW;
    for (const p of digitalPalette) {
      r -= p.w;
      if (r <= 0) return p.c;
    }
    return digitalPalette[0].c;
  }

  function smoothstep(e0, e1, x) {
    const t = Math.max(0, Math.min(1, (x - e0) / (e1 - e0)));
    return t * t * (3 - 2 * t);
  }

  let width = mount.clientWidth;
  let height = mount.clientHeight;

  const svgNS = "http://www.w3.org/2000/svg";
  const svgEl = document.createElementNS(svgNS, "svg");
  svgEl.setAttribute("viewBox", `0 0 ${VIEW_W} ${VIEW_H}`);
  svgEl.setAttribute("width", String(VIEW_W));
  svgEl.setAttribute("height", String(VIEW_H));
  svgEl.style.position = "absolute";
  svgEl.style.left = "-99999px";
  svgEl.style.top = "0";
  svgEl.style.pointerEvents = "none";
  document.body.appendChild(svgEl);

  const zmIdx = LEMON_BODY_D.indexOf("ZM");
  const outerD = LEMON_BODY_D.substring(0, zmIdx + 1);

  const outerPathEl = document.createElementNS(svgNS, "path");
  outerPathEl.setAttribute("d", outerD);
  svgEl.appendChild(outerPathEl);

  const leafPathEl = document.createElementNS(svgNS, "path");
  leafPathEl.setAttribute("d", LEAF_D);
  svgEl.appendChild(leafPathEl);

  const outerBBox = outerPathEl.getBBox();
  const leafBBox = leafPathEl.getBBox();
  const targetHeight = 1.85;
  const scale = targetHeight / outerBBox.height;
  const cx = outerBBox.x + outerBBox.width / 2;
  const cy = outerBBox.y + outerBBox.height / 2;
  const toSVG = (wx, wy) => [wx / scale + cx, -wy / scale + cy];
  const halfWidthWorld = (outerBBox.width / 2) * scale;

  const leafCenterX = (leafBBox.x + leafBBox.width / 2 - cx) * scale;
  const leafCenterY = -(leafBBox.y + leafBBox.height / 2 - cy) * scale;
  const leafRadiusWorld = Math.min(leafBBox.width, leafBBox.height) * 0.4 * scale;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x191919);

  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.z = 7;

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  mount.appendChild(renderer.domElement);

  const fillRes = 6;
  const fillCanvas = document.createElement("canvas");
  fillCanvas.width = Math.ceil(VIEW_W * fillRes);
  fillCanvas.height = Math.ceil(VIEW_H * fillRes);
  const fctx = fillCanvas.getContext("2d");
  fctx.save();
  fctx.scale(fillRes, fillRes);
  fctx.fillStyle = CORAL_HEX;
  fctx.fill(new Path2D(LEMON_BODY_D));
  fctx.fill(new Path2D(LEAF_D));
  fctx.restore();

  const lemonTex = new THREE.CanvasTexture(fillCanvas);
  lemonTex.colorSpace = THREE.SRGBColorSpace;
  lemonTex.minFilter = THREE.LinearFilter;
  lemonTex.magFilter = THREE.LinearFilter;
  if (renderer.capabilities.getMaxAnisotropy) {
    lemonTex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  }

  const planeWidth = VIEW_W * scale;
  const planeHeight = VIEW_H * scale;
  const lemonPlaneGeom = new THREE.PlaneGeometry(planeWidth, planeHeight);
  const lemonPlaneMat = new THREE.MeshBasicMaterial({ map: lemonTex, transparent: true });
  const lemonPlaneMesh = new THREE.Mesh(lemonPlaneGeom, lemonPlaneMat);

  lemonPlaneMesh.position.set(
    (VIEW_W / 2 - cx) * scale,
    -(VIEW_H / 2 - cy) * scale,
    -0.15
  );
  lemonPlaneMesh.renderOrder = 0;

  const lemonGroup = new THREE.Group();
  lemonGroup.add(lemonPlaneMesh);
  scene.add(lemonGroup);

  const iconRes = 256;
  const lemonIconCanvas = document.createElement("canvas");
  lemonIconCanvas.width = iconRes;
  lemonIconCanvas.height = iconRes;
  const lctx = lemonIconCanvas.getContext("2d");
  const iconPadding = 16;
  const availSize = iconRes - iconPadding * 2;
  const iconScale = availSize / Math.max(outerBBox.width, outerBBox.height);

  lctx.save();
  lctx.translate(iconRes / 2, iconRes / 2);
  lctx.scale(iconScale, iconScale);
  lctx.translate(
    -(outerBBox.x + outerBBox.width / 2),
    -(outerBBox.y + outerBBox.height / 2)
  );
  lctx.strokeStyle = "white";
  lctx.lineWidth = 14;
  lctx.lineJoin = "round";
  lctx.lineCap = "round";
  lctx.stroke(new Path2D(LEMON_BODY_D));
  lctx.stroke(new Path2D(LEAF_D));
  lctx.restore();

  const lemonIconTex = new THREE.CanvasTexture(lemonIconCanvas);
  lemonIconTex.colorSpace = THREE.SRGBColorSpace;
  lemonIconTex.minFilter = THREE.LinearFilter;
  lemonIconTex.magFilter = THREE.LinearFilter;

  const orgTexCanvas = document.createElement("canvas");
  orgTexCanvas.width = 128;
  orgTexCanvas.height = 128;
  const orgCtx = orgTexCanvas.getContext("2d");
  const orgGrd = orgCtx.createRadialGradient(64, 64, 0, 64, 64, 64);
  orgGrd.addColorStop(0.0, "rgba(255,255,255,1)");
  orgGrd.addColorStop(0.4, "rgba(255,255,255,0.6)");
  orgGrd.addColorStop(0.8, "rgba(255,255,255,0.15)");
  orgGrd.addColorStop(1.0, "rgba(255,255,255,0)");
  orgCtx.fillStyle = orgGrd;
  orgCtx.fillRect(0, 0, 128, 128);

  const organicTexture = new THREE.CanvasTexture(orgTexCanvas);
  organicTexture.colorSpace = THREE.SRGBColorSpace;

  const FLAT_COUNT = 2000;
  const flat = {
    positions: new Float32Array(FLAT_COUNT * 3),
    colors: new Float32Array(FLAT_COUNT * 3),
    sizes: new Float32Array(FLAT_COUNT),
    alphas: new Float32Array(FLAT_COUNT),
    seeds: new Float32Array(FLAT_COUNT),
    rotations: new Float32Array(FLAT_COUNT),
    rotationSpeeds: new Float32Array(FLAT_COUNT),
    dissolves: new Float32Array(FLAT_COUNT),
    lifeRatios: new Float32Array(FLAT_COUNT),
    velocities: new Float32Array(FLAT_COUNT * 3),
    life: new Float32Array(FLAT_COUNT),
    maxLife: new Float32Array(FLAT_COUNT),
    cursor: 0
  };

  for (let i = 0; i < FLAT_COUNT; i++) {
    flat.life[i] = 0;
    flat.alphas[i] = 0;
  }

  const flatGeom = new THREE.BufferGeometry();
  flatGeom.setAttribute("position", new THREE.BufferAttribute(flat.positions, 3));
  flatGeom.setAttribute("customColor", new THREE.BufferAttribute(flat.colors, 3));
  flatGeom.setAttribute("size", new THREE.BufferAttribute(flat.sizes, 1));
  flatGeom.setAttribute("alpha", new THREE.BufferAttribute(flat.alphas, 1));
  flatGeom.setAttribute("seed", new THREE.BufferAttribute(flat.seeds, 1));
  flatGeom.setAttribute("rotation", new THREE.BufferAttribute(flat.rotations, 1));
  flatGeom.setAttribute("rotationSpeed", new THREE.BufferAttribute(flat.rotationSpeeds, 1));
  flatGeom.setAttribute("dissolve", new THREE.BufferAttribute(flat.dissolves, 1));
  flatGeom.setAttribute("lifeRatio", new THREE.BufferAttribute(flat.lifeRatios, 1));

  const flatMat = new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 } },
    vertexShader: `
      attribute vec3 customColor;
      attribute float size;
      attribute float alpha;
      attribute float seed;
      attribute float rotation;
      attribute float rotationSpeed;
      attribute float dissolve;
      attribute float lifeRatio;
      uniform float uTime;
      varying vec3 vColor;
      varying float vAlpha;
      varying float vRot;
      varying float vDissolve;
      varying float vLifeRatio;
      void main() {
        vColor = customColor;
        vAlpha = alpha;
        vRot = rotation + uTime * rotationSpeed;
        vDissolve = dissolve;
        vLifeRatio = lifeRatio;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (115.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying float vAlpha;
      varying float vRot;
      varying float vDissolve;
      varying float vLifeRatio;
      void main() {
        vec2 uv = gl_PointCoord - 0.5;
        float c = cos(vRot);
        float s = sin(vRot);
        vec2 rotUv = vec2(c * uv.x - s * uv.y, s * uv.x + c * uv.y);
        float maxAxis = max(abs(rotUv.x), abs(rotUv.y));
        if (maxAxis > 0.354) discard;
        if (vDissolve > 0.5) {
          float dissolveStart = 0.7;
          if (vLifeRatio < dissolveStart) {
            float effLife = vLifeRatio / dissolveStart;
            vec2 cellCoord = (rotUv + 0.354) / 0.708;
            vec2 cellIdx = floor(cellCoord * 4.0);
            float cellRand = fract(sin(dot(cellIdx, vec2(12.9898, 78.233))) * 43758.5453);
            if (effLife < cellRand) discard;
          }
        }
        float edge = 1.0 - smoothstep(0.31, 0.354, maxAxis);
        if (edge < 0.02) discard;
        gl_FragColor = vec4(vColor, vAlpha * edge);
      }
    `,
    transparent: true,
    blending: THREE.NormalBlending,
    depthWrite: false,
    depthTest: false
  });

  const flatPoints = new THREE.Points(flatGeom, flatMat);
  flatPoints.renderOrder = 2;
  scene.add(flatPoints);

  const CUBE_COUNT = 260;
  const cubeColors = new Float32Array(CUBE_COUNT * 3);
  const cubeAlphas = new Float32Array(CUBE_COUNT);
  const cubeModes = new Float32Array(CUBE_COUNT);
  const cubeGeom = new THREE.BoxGeometry(1, 1, 1);

  cubeGeom.setAttribute("aColor", new THREE.InstancedBufferAttribute(cubeColors, 3));
  cubeGeom.setAttribute("aAlpha", new THREE.InstancedBufferAttribute(cubeAlphas, 1));
  cubeGeom.setAttribute("aMode", new THREE.InstancedBufferAttribute(cubeModes, 1));

  const cubeMat = new THREE.ShaderMaterial({
    vertexShader: `
      attribute vec3 aColor;
      attribute float aAlpha;
      attribute float aMode;
      varying vec3 vColor;
      varying float vAlpha;
      varying float vMode;
      varying vec2 vUv;
      varying vec3 vLocalNormal;
      void main() {
        vColor = aColor;
        vAlpha = aAlpha;
        vMode = aMode;
        vUv = uv;
        vLocalNormal = normal;
        vec4 pos = instanceMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * modelViewMatrix * pos;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying float vAlpha;
      varying float vMode;
      varying vec2 vUv;
      varying vec3 vLocalNormal;
      void main() {
        float a;
        vec3 col;
        if (vMode > 0.5) {
          bool isSolidFace = vLocalNormal.x > 0.9;
          if (isSolidFace) {
            col = vColor;
            a = 0.96;
          } else {
            float ang = 0.785398;
            vec2 rotUv = vec2(
              vUv.x * cos(ang) - vUv.y * sin(ang),
              vUv.x * sin(ang) + vUv.y * cos(ang)
            );
            float stripe = step(0.55, fract(rotUv.x * 7.0));
            if (stripe < 0.5) discard;
            col = vColor;
            a = 0.9;
          }
        } else {
          vec2 edgeDist = min(vUv, 1.0 - vUv);
          float minEdge = min(edgeDist.x, edgeDist.y);
          float edgeWidth = 0.04;
          float edge = 1.0 - smoothstep(edgeWidth, edgeWidth + 0.015, minEdge);
          float cornerR = 0.18;
          float dCorner = length(edgeDist);
          float corner = 1.0 - smoothstep(cornerR * 0.4, cornerR, dCorner);
          float face = 0.035;
          a = max(face, max(edge * 0.68, corner));
          col = vColor * (0.98 + corner * 0.26);
        }
        if (a < 0.02) discard;
        gl_FragColor = vec4(col, a * vAlpha);
      }
    `,
    transparent: true,
    blending: THREE.NormalBlending,
    depthWrite: false,
    depthTest: true,
    side: THREE.DoubleSide
  });

  const cubeMesh = new THREE.InstancedMesh(cubeGeom, cubeMat, CUBE_COUNT);
  cubeMesh.renderOrder = 1;
  scene.add(cubeMesh);

  const tempMatrix = new THREE.Matrix4();
  const tempEuler = new THREE.Euler();
  const tempScaleVec = new THREE.Vector3();

  tempMatrix.makeScale(0, 0, 0);
  for (let i = 0; i < CUBE_COUNT; i++) cubeMesh.setMatrixAt(i, tempMatrix);
  cubeMesh.instanceMatrix.needsUpdate = true;

  const cube = {
    positions: new Float32Array(CUBE_COUNT * 3),
    velocities: new Float32Array(CUBE_COUNT * 3),
    rotations: new Float32Array(CUBE_COUNT * 3),
    rotationSpeeds: new Float32Array(CUBE_COUNT * 3),
    sizes: new Float32Array(CUBE_COUNT),
    life: new Float32Array(CUBE_COUNT),
    maxLife: new Float32Array(CUBE_COUNT),
    cursor: 0
  };

  for (let i = 0; i < CUBE_COUNT; i++) cube.life[i] = 0;

  const LEMON_ICON_COUNT = 50;
  const lemonIconColors = new Float32Array(LEMON_ICON_COUNT * 3);
  const lemonIconAlphas = new Float32Array(LEMON_ICON_COUNT);
  const lemonIconGeom = new THREE.PlaneGeometry(1, 1);

  lemonIconGeom.setAttribute("aColor", new THREE.InstancedBufferAttribute(lemonIconColors, 3));
  lemonIconGeom.setAttribute("aAlpha", new THREE.InstancedBufferAttribute(lemonIconAlphas, 1));

  const lemonIconMat = new THREE.ShaderMaterial({
    uniforms: { uTex: { value: lemonIconTex } },
    vertexShader: `
      attribute vec3 aColor;
      attribute float aAlpha;
      varying vec3 vColor;
      varying float vAlpha;
      varying vec2 vUv;
      void main() {
        vColor = aColor;
        vAlpha = aAlpha;
        vUv = uv;
        vec4 pos = instanceMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * modelViewMatrix * pos;
      }
    `,
    fragmentShader: `
      uniform sampler2D uTex;
      varying vec3 vColor;
      varying float vAlpha;
      varying vec2 vUv;
      void main() {
        vec4 tex = texture2D(uTex, vUv);
        if (tex.a < 0.04) discard;
        gl_FragColor = vec4(vColor, tex.a * vAlpha);
      }
    `,
    transparent: true,
    blending: THREE.NormalBlending,
    depthWrite: false,
    depthTest: true,
    side: THREE.DoubleSide
  });

  const lemonIconMesh = new THREE.InstancedMesh(
    lemonIconGeom,
    lemonIconMat,
    LEMON_ICON_COUNT
  );
  lemonIconMesh.renderOrder = 1;
  scene.add(lemonIconMesh);

  tempMatrix.makeScale(0, 0, 0);
  for (let i = 0; i < LEMON_ICON_COUNT; i++) lemonIconMesh.setMatrixAt(i, tempMatrix);
  lemonIconMesh.instanceMatrix.needsUpdate = true;

  const lemonIcon = {
    positions: new Float32Array(LEMON_ICON_COUNT * 3),
    velocities: new Float32Array(LEMON_ICON_COUNT * 3),
    rotations: new Float32Array(LEMON_ICON_COUNT * 3),
    rotationSpeeds: new Float32Array(LEMON_ICON_COUNT * 3),
    sizes: new Float32Array(LEMON_ICON_COUNT),
    life: new Float32Array(LEMON_ICON_COUNT),
    maxLife: new Float32Array(LEMON_ICON_COUNT),
    cursor: 0
  };

  for (let i = 0; i < LEMON_ICON_COUNT; i++) lemonIcon.life[i] = 0;

  const ORG_COUNT = 3400;
  const org = {
    positions: new Float32Array(ORG_COUNT * 3),
    colors: new Float32Array(ORG_COUNT * 3),
    sizes: new Float32Array(ORG_COUNT),
    alphas: new Float32Array(ORG_COUNT),
    seeds: new Float32Array(ORG_COUNT),
    velocities: new Float32Array(ORG_COUNT * 3),
    life: new Float32Array(ORG_COUNT),
    maxLife: new Float32Array(ORG_COUNT),
    cursor: 0
  };

  for (let i = 0; i < ORG_COUNT; i++) {
    org.life[i] = 0;
    org.alphas[i] = 0;
  }

  const orgGeom = new THREE.BufferGeometry();
  orgGeom.setAttribute("position", new THREE.BufferAttribute(org.positions, 3));
  orgGeom.setAttribute("customColor", new THREE.BufferAttribute(org.colors, 3));
  orgGeom.setAttribute("size", new THREE.BufferAttribute(org.sizes, 1));
  orgGeom.setAttribute("alpha", new THREE.BufferAttribute(org.alphas, 1));
  orgGeom.setAttribute("seed", new THREE.BufferAttribute(org.seeds, 1));

  const orgMat = new THREE.ShaderMaterial({
    uniforms: {
      pointTexture: { value: organicTexture },
      uTime: { value: 0 }
    },
    vertexShader: `
      attribute vec3 customColor;
      attribute float size;
      attribute float alpha;
      attribute float seed;
      varying vec3 vColor;
      varying float vAlpha;
      varying float vSeed;
      void main() {
        vColor = customColor;
        vAlpha = alpha;
        vSeed = seed;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (80.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      uniform sampler2D pointTexture;
      varying vec3 vColor;
      varying float vAlpha;
      varying float vSeed;
      void main() {
        vec4 tex = texture2D(pointTexture, gl_PointCoord);
        float softness = 0.5 + fract(vSeed * 0.137) * 0.8;
        float a = pow(tex.a, softness);
        if (a < 0.02) discard;
        gl_FragColor = vec4(vColor, a * vAlpha);
      }
    `,
    transparent: true,
    blending: THREE.NormalBlending,
    depthWrite: false,
    depthTest: false
  });

  const orgPoints = new THREE.Points(orgGeom, orgMat);
  orgPoints.renderOrder = 2;
  scene.add(orgPoints);

  function makeLineGeometry(points) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    return geometry;
  }

  function addLine(points, ax, ay, bx, by) {
    points.push(ax, ay, 0, bx, by, 0);
  }

  function addCircle(points, cx, cy, r, segments = 72, start = 0, end = Math.PI * 2) {
    let lastX = cx + Math.cos(start) * r;
    let lastY = cy + Math.sin(start) * r;
    for (let i = 1; i <= segments; i++) {
      const t = start + (end - start) * (i / segments);
      const x = cx + Math.cos(t) * r;
      const y = cy + Math.sin(t) * r;
      addLine(points, lastX, lastY, x, y);
      lastX = x;
      lastY = y;
    }
  }

  function createGoldenSpiralGeometry() {
    const points = [];
    const turns = 4.4;
    const steps = 210;
    let lastX = 0;
    let lastY = 0;

    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * Math.PI * 2 * turns;
      const r = 0.035 * Math.pow(1.618, t / (Math.PI / 2));
      const x = Math.cos(t) * r;
      const y = Math.sin(t) * r;
      if (i > 0) addLine(points, lastX, lastY, x, y);
      lastX = x;
      lastY = y;
    }

    addCircle(points, 0, 0, 0.95, 96);
    return makeLineGeometry(points);
  }

  function createFlowerOfLifeGeometry() {
    const points = [];
    const r = 0.34;
    const ring = r;
    const centers = [{ x: 0, y: 0 }];

    for (let i = 0; i < 6; i++) {
      centers.push({
        x: Math.cos((Math.PI * 2 * i) / 6) * ring,
        y: Math.sin((Math.PI * 2 * i) / 6) * ring
      });
    }

    for (let i = 0; i < 6; i++) {
      centers.push({
        x: Math.cos((Math.PI * 2 * i) / 6) * ring * 2,
        y: Math.sin((Math.PI * 2 * i) / 6) * ring * 2
      });
    }

    for (let i = 0; i < 6; i++) {
      centers.push({
        x: Math.cos((Math.PI * 2 * i) / 6 + Math.PI / 6) * ring * 1.72,
        y: Math.sin((Math.PI * 2 * i) / 6 + Math.PI / 6) * ring * 1.72
      });
    }

    centers.forEach((c) => addCircle(points, c.x, c.y, r, 72));
    addCircle(points, 0, 0, r * 3, 108);
    return makeLineGeometry(points);
  }

  function createMetatronGeometry() {
    const points = [];
    const nodes = [{ x: 0, y: 0 }];
    const r = 0.52;

    for (let i = 0; i < 6; i++) {
      nodes.push({
        x: Math.cos((Math.PI * 2 * i) / 6) * r,
        y: Math.sin((Math.PI * 2 * i) / 6) * r
      });
    }

    for (let i = 0; i < 6; i++) {
      nodes.push({
        x: Math.cos((Math.PI * 2 * i) / 6 + Math.PI / 6) * r * 1.78,
        y: Math.sin((Math.PI * 2 * i) / 6 + Math.PI / 6) * r * 1.78
      });
    }

    for (let i = 0; i < nodes.length; i++) addCircle(points, nodes[i].x, nodes[i].y, 0.16, 42);

    for (let i = 1; i <= 6; i++) {
      addLine(points, 0, 0, nodes[i].x, nodes[i].y);
      const next = i === 6 ? 1 : i + 1;
      addLine(points, nodes[i].x, nodes[i].y, nodes[next].x, nodes[next].y);
    }

    for (let i = 7; i < nodes.length; i++) addLine(points, 0, 0, nodes[i].x, nodes[i].y);

    for (let i = 7; i < nodes.length; i++) {
      const next = i === nodes.length - 1 ? 7 : i + 1;
      addLine(points, nodes[i].x, nodes[i].y, nodes[next].x, nodes[next].y);
    }

    return makeLineGeometry(points);
  }

  function createTorusWireGeometry() {
    const points = [];
    const rings = 18;
    const segments = 80;

    for (let j = 0; j < rings; j++) {
      const phase = (j / rings) * Math.PI * 2;
      let lastX = null;
      let lastY = null;

      for (let i = 0; i <= segments; i++) {
        const t = (i / segments) * Math.PI * 2;
        const warp = Math.sin(t * 2 + phase) * 0.12;
        const rx = 0.84 + warp;
        const ry = 0.48 + Math.cos(phase) * 0.07;
        const x = Math.cos(t + phase * 0.1) * rx;
        const y = Math.sin(t) * ry;

        if (lastX !== null) addLine(points, lastX, lastY, x, y);
        lastX = x;
        lastY = y;
      }
    }

    addCircle(points, 0, 0, 0.9, 96);
    addCircle(points, 0, 0, 0.48, 96);
    return makeLineGeometry(points);
  }

  function createSacredGeometry(kind) {
    if (kind === 0) return createGoldenSpiralGeometry();
    if (kind === 1) return createFlowerOfLifeGeometry();
    if (kind === 2) return createMetatronGeometry();
    return createTorusWireGeometry();
  }

  const SACRED_COUNT = 42;
  const sacred = {
    meshes: [],
    positions: new Float32Array(SACRED_COUNT * 3),
    velocities: new Float32Array(SACRED_COUNT * 3),
    rotations: new Float32Array(SACRED_COUNT * 3),
    rotationSpeeds: new Float32Array(SACRED_COUNT * 3),
    sizes: new Float32Array(SACRED_COUNT),
    life: new Float32Array(SACRED_COUNT),
    maxLife: new Float32Array(SACRED_COUNT),
    dance: new Float32Array(SACRED_COUNT),
    cursor: 0
  };

  for (let i = 0; i < SACRED_COUNT; i++) {
    const geometry = createSacredGeometry(i % 4);
    const material = new THREE.LineBasicMaterial({
      color: 0xCC3565,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      depthTest: false
    });

    const mesh = new THREE.LineSegments(geometry, material);
    mesh.renderOrder = 3;
    mesh.visible = false;
    sacred.meshes.push(mesh);
    scene.add(mesh);
    sacred.life[i] = 0;
  }

  const grainMat = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uIntensity: { value: 0.045 }
    },
    vertexShader: `
      void main() {
        gl_Position = vec4(position.xy, 0.999, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform float uIntensity;
      float hash(vec2 p) {
        return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
      }
      void main() {
        vec2 p = gl_FragCoord.xy + fract(uTime * 1.7) * 1000.0;
        float n = hash(p);
        float v = (n - 0.5) * uIntensity;
        gl_FragColor = vec4(v, v, v, 1.0);
      }
    `,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    depthTest: false
  });

  const grainMesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), grainMat);
  grainMesh.frustumCulled = false;
  grainMesh.renderOrder = 1000;
  scene.add(grainMesh);

  function spawnFlat(idx, ox, oy) {
    const angle = Math.random() * Math.PI * 2;
    const speed = 0.4 + Math.random() * 2.5;
    const jr = Math.pow(Math.random(), 1.4) * 0.07;
    const ja = Math.random() * Math.PI * 2;

    flat.positions[idx * 3] = ox + Math.cos(ja) * jr;
    flat.positions[idx * 3 + 1] = oy + Math.sin(ja) * jr;
    flat.positions[idx * 3 + 2] = 0;

    flat.velocities[idx * 3] = Math.cos(angle) * speed;
    flat.velocities[idx * 3 + 1] = Math.sin(angle) * speed;
    flat.velocities[idx * 3 + 2] = 0;

    const c = pickDigitalColor();
    const cj = 0.025;

    flat.colors[idx * 3] = Math.max(0, Math.min(1, c[0] + (Math.random() - 0.5) * cj));
    flat.colors[idx * 3 + 1] = Math.max(0, Math.min(1, c[1] + (Math.random() - 0.5) * cj));
    flat.colors[idx * 3 + 2] = Math.max(0, Math.min(1, c[2] + (Math.random() - 0.5) * cj));

    const sr = Math.random();
    let isChunky = false;

    if (sr < 0.5) flat.sizes[idx] = 0.3 + Math.random() * 0.5;
    else if (sr < 0.85) flat.sizes[idx] = 1.0 + Math.random() * 1.0;
    else {
      flat.sizes[idx] = 2.4 + Math.random() * 2.0;
      isChunky = true;
    }

    flat.rotations[idx] = Math.random() * Math.PI * 2;
    flat.rotationSpeeds[idx] = (Math.random() - 0.5) * 6;
    flat.dissolves[idx] = isChunky && Math.random() < 0.55 ? 1 : 0;
    flat.maxLife[idx] = 1.6 + Math.random() * 2.4;
    flat.life[idx] = flat.maxLife[idx];
    flat.lifeRatios[idx] = 1;
    flat.alphas[idx] = 0;
    flat.seeds[idx] = Math.random() * 100;
  }

  function spawnCube(idx, ox, oy) {
    const angle = Math.random() * Math.PI * 2;
    const speed = 0.4 + Math.random() * 2.2;

    cube.positions[idx * 3] = ox + (Math.random() - 0.5) * 0.06;
    cube.positions[idx * 3 + 1] = oy + (Math.random() - 0.5) * 0.06;
    cube.positions[idx * 3 + 2] = (Math.random() - 0.5) * 0.4;

    cube.velocities[idx * 3] = Math.cos(angle) * speed;
    cube.velocities[idx * 3 + 1] = Math.sin(angle) * speed;
    cube.velocities[idx * 3 + 2] = (Math.random() - 0.5) * 1.2;

    cube.rotations[idx * 3] = Math.random() * Math.PI * 2;
    cube.rotations[idx * 3 + 1] = Math.random() * Math.PI * 2;
    cube.rotations[idx * 3 + 2] = Math.random() * Math.PI * 2;

    cube.rotationSpeeds[idx * 3] = (Math.random() - 0.5) * 3;
    cube.rotationSpeeds[idx * 3 + 1] = (Math.random() - 0.5) * 3;
    cube.rotationSpeeds[idx * 3 + 2] = (Math.random() - 0.5) * 3;

    const isStriped = Math.random() < 0.35;
    cubeModes[idx] = isStriped ? 1 : 0;

    if (isStriped) cube.sizes[idx] = 0.14 + Math.random() * 0.16;
    else {
      const sr = Math.random();
      if (sr < 0.55) cube.sizes[idx] = 0.06 + Math.random() * 0.07;
      else cube.sizes[idx] = 0.14 + Math.random() * 0.12;
    }

    let c;
    if (isStriped) {
      const sr = Math.random();
      if (sr < 0.35) c = [0.80, 0.21, 0.40];
      else if (sr < 0.58) c = [0.90, 0.68, 0.22];
      else if (sr < 0.78) c = [0.22, 0.56, 0.78];
      else c = pickDigitalColor();
    } else {
      c = pickDigitalColor();
    }

    cubeColors[idx * 3] = c[0];
    cubeColors[idx * 3 + 1] = c[1];
    cubeColors[idx * 3 + 2] = c[2];

    cubeAlphas[idx] = 0;
    cube.maxLife[idx] = 2.6 + Math.random() * 2.4;
    cube.life[idx] = cube.maxLife[idx];
  }

  function spawnLemonIcon(idx) {
    const jr = Math.random() * leafRadiusWorld;
    const ja = Math.random() * Math.PI * 2;
    const sx = leafCenterX + Math.cos(ja) * jr;
    const sy = leafCenterY + Math.sin(ja) * jr;

    lemonIcon.positions[idx * 3] = sx;
    lemonIcon.positions[idx * 3 + 1] = sy;
    lemonIcon.positions[idx * 3 + 2] = (Math.random() - 0.5) * 0.3;

    const baseAngle = Math.atan2(sy, sx);
    const angle = baseAngle + (Math.random() - 0.5) * Math.PI * 0.7;
    const speed = 0.5 + Math.random() * 1.5;

    lemonIcon.velocities[idx * 3] = Math.cos(angle) * speed;
    lemonIcon.velocities[idx * 3 + 1] = Math.sin(angle) * speed;
    lemonIcon.velocities[idx * 3 + 2] = (Math.random() - 0.5) * 0.6;

    lemonIcon.rotations[idx * 3] = Math.random() * Math.PI * 2;
    lemonIcon.rotations[idx * 3 + 1] = Math.random() * Math.PI * 2;
    lemonIcon.rotations[idx * 3 + 2] = Math.random() * Math.PI * 2;

    lemonIcon.rotationSpeeds[idx * 3] = (Math.random() - 0.5) * 2.2;
    lemonIcon.rotationSpeeds[idx * 3 + 1] = (Math.random() - 0.5) * 2.2;
    lemonIcon.rotationSpeeds[idx * 3 + 2] = (Math.random() - 0.5) * 2.2;
    lemonIcon.sizes[idx] = 0.32 + Math.random() * 0.24;

    const c = Math.random() < 0.55 ? [0.80, 0.21, 0.40] : pickDigitalColor();

    lemonIconColors[idx * 3] = c[0];
    lemonIconColors[idx * 3 + 1] = c[1];
    lemonIconColors[idx * 3 + 2] = c[2];

    lemonIconAlphas[idx] = 0;
    lemonIcon.maxLife[idx] = 3.5 + Math.random() * 2.5;
    lemonIcon.life[idx] = lemonIcon.maxLife[idx];
  }

  function pickSacredAnchor(ox, oy, leftStrength) {
    const anchors = [
      { x: -halfWidthWorld * 0.92, y: 0.72 },
      { x: -halfWidthWorld * 0.74, y: 0.42 },
      { x: -halfWidthWorld * 0.86, y: 0.08 },
      { x: -halfWidthWorld * 0.66, y: -0.32 },
      { x: -halfWidthWorld * 0.96, y: -0.68 },
      { x: -halfWidthWorld * 0.44, y: 0.68 },
      { x: -halfWidthWorld * 0.36, y: -0.58 }
    ];

    if (Math.random() < 0.82) {
      const anchor = anchors[Math.floor(Math.random() * anchors.length)];
      return {
        x: anchor.x + (Math.random() - 0.5) * 0.18,
        y: anchor.y + (Math.random() - 0.5) * 0.18
      };
    }

    return {
      x: ox - Math.random() * halfWidthWorld * (0.35 + leftStrength * 0.35),
      y: oy + (Math.random() - 0.5) * 0.45
    };
  }

  function spawnSacred(idx, ox, oy, leftStrength) {
    const anchor = pickSacredAnchor(ox, oy, leftStrength);
    const angle = Math.PI + (Math.random() - 0.5) * Math.PI * 1.45;
    const speed = 0.1 + Math.random() * 0.5;
    const c = pickSacredColor();
    const mesh = sacred.meshes[idx];

    sacred.positions[idx * 3] = anchor.x;
    sacred.positions[idx * 3 + 1] = anchor.y;
    sacred.positions[idx * 3 + 2] = 0.22 + Math.random() * 0.16;

    sacred.velocities[idx * 3] = Math.cos(angle) * speed * (0.5 + leftStrength);
    sacred.velocities[idx * 3 + 1] = Math.sin(angle) * speed;
    sacred.velocities[idx * 3 + 2] = 0;

    sacred.rotations[idx * 3] = (Math.random() - 0.5) * 0.28;
    sacred.rotations[idx * 3 + 1] = (Math.random() - 0.5) * 0.28;
    sacred.rotations[idx * 3 + 2] = Math.random() * Math.PI * 2;

    // More visible movement: slow 3D tilt plus a stronger spinning drift.
    sacred.rotationSpeeds[idx * 3] = (Math.random() - 0.5) * 0.58;
    sacred.rotationSpeeds[idx * 3 + 1] = (Math.random() - 0.5) * 0.58;
    sacred.rotationSpeeds[idx * 3 + 2] = (Math.random() - 0.5) * 1.55;

    sacred.sizes[idx] = 0.24 + Math.random() * 0.42;
    sacred.maxLife[idx] = 3.6 + Math.random() * 3.1;
    sacred.life[idx] = sacred.maxLife[idx];
    sacred.dance[idx] = Math.random() * 100;

    mesh.material.color.setRGB(c[0], c[1], c[2]);
    mesh.material.opacity = 0;
    mesh.visible = true;
  }

  function emitOneLemonIcon() {
    let scanned = 0;
    while (scanned < LEMON_ICON_COUNT) {
      const i = lemonIcon.cursor;
      lemonIcon.cursor = (lemonIcon.cursor + 1) % LEMON_ICON_COUNT;
      scanned++;
      if (lemonIcon.life[i] <= 0.05) {
        spawnLemonIcon(i);
        return true;
      }
    }
    return false;
  }

  function emitSacred(ox, oy, count, leftStrength) {
    let made = 0;
    let scanned = 0;
    while (made < count && scanned < SACRED_COUNT) {
      const i = sacred.cursor;
      sacred.cursor = (sacred.cursor + 1) % SACRED_COUNT;
      scanned++;
      if (sacred.life[i] <= 0.05) {
        spawnSacred(i, ox, oy, leftStrength);
        made++;
      }
    }
  }

  function spawnOrganic(idx, ox, oy) {
    const tier = Math.random();
    let speed;
    let lifeMul;
    let sizeMul;
    let opacityBoost = 1;

    // The right side is the paint / atmosphere side.
    // It now has more splatter variety: soft clouds, mid flecks, fast paint specks, and occasional larger drops.
    if (tier < 0.18) {
      speed = 0.05 + Math.random() * 0.28;
      lifeMul = 1.85;
      sizeMul = 2.2;
      opacityBoost = 1.05;
    } else if (tier < 0.42) {
      speed = 0.16 + Math.random() * 0.55;
      lifeMul = 1.55;
      sizeMul = 1.45;
    } else if (tier < 0.83) {
      speed = 0.75 + Math.random() * 1.95;
      lifeMul = 1.0;
      sizeMul = 1.0;
    } else {
      speed = 2.8 + Math.random() * 2.8;
      lifeMul = 0.58;
      sizeMul = 0.62;
      opacityBoost = 1.15;
    }

    const angle = Math.random() * Math.PI * 2;
    const jr = Math.pow(Math.random(), 1.6) * 0.1;
    const ja = Math.random() * Math.PI * 2;

    org.positions[idx * 3] = ox + Math.cos(ja) * jr;
    org.positions[idx * 3 + 1] = oy + Math.sin(ja) * jr;
    org.positions[idx * 3 + 2] = (Math.random() - 0.5) * 0.34;

    org.velocities[idx * 3] = Math.cos(angle) * speed;
    org.velocities[idx * 3 + 1] = Math.sin(angle) * speed;
    org.velocities[idx * 3 + 2] = (Math.random() - 0.5) * 0.38;

    const c = organicPalette[Math.floor(Math.random() * organicPalette.length)];
    const cj = 0.045;

    org.colors[idx * 3] = Math.max(0, Math.min(1, c[0] + (Math.random() - 0.5) * cj));
    org.colors[idx * 3 + 1] = Math.max(0, Math.min(1, c[1] + (Math.random() - 0.5) * cj));
    org.colors[idx * 3 + 2] = Math.max(0, Math.min(1, c[2] + (Math.random() - 0.5) * cj));

    const sr = Math.pow(Math.random(), 1.55);
    org.sizes[idx] = (3.0 + sr * 15.5) * sizeMul;
    org.maxLife[idx] = (2.5 + Math.random() * 3.4) * lifeMul;
    org.life[idx] = org.maxLife[idx];
    org.alphas[idx] = 0;
    org.seeds[idx] = Math.random() * 100 * opacityBoost;
  }

  function emitInto(state, spawnFn, count, ox, oy) {
    let made = 0;
    let scanned = 0;
    const total = state.life.length;

    while (made < count && scanned < total) {
      const i = state.cursor;
      state.cursor = (state.cursor + 1) % total;
      scanned++;

      if (state.life[i] <= 0.05) {
        spawnFn(i, ox, oy);
        made++;
      }
    }
  }

  function emit(ox, oy, count, probOrganic) {
    let organicN = 0;
    for (let n = 0; n < count; n++) {
      if (Math.random() < probOrganic) organicN++;
    }

    const rightStrength = probOrganic;
    const digitalTotal = count - organicN;
    let cubeN = 0;

    for (let n = 0; n < digitalTotal; n++) {
      if (Math.random() < 0.12) cubeN++;
    }

    const flatN = digitalTotal - cubeN;
    if (flatN > 0) emitInto(flat, spawnFlat, flatN, ox, oy);
    if (cubeN > 0) emitInto(cube, spawnCube, cubeN, ox, oy);
    if (organicN > 0) emitInto(org, spawnOrganic, organicN, ox, oy);

    // Give the right paint side extra life so it can compete with the left pixel side.
    // These are additional splattery atmosphere particles, not a color reset.
    if (rightStrength > 0.48 && count > 70) {
      const extraSplatter = Math.floor(count * rightStrength * (0.22 + Math.random() * 0.34));
      if (extraSplatter > 0) emitInto(org, spawnOrganic, extraSplatter, ox, oy);
    }

    const leftStrength = 1 - probOrganic;
    if (leftStrength > 0.34 && count > 80 && Math.random() < 0.82) {
      emitSacred(ox, oy, 1 + Math.floor(Math.random() * 2), leftStrength);
    }
  }

  function isInsideLemon(worldX, worldY) {
    const [sx, sy] = toSVG(worldX, worldY);
    const pt = svgEl.createSVGPoint();
    pt.x = sx;
    pt.y = sy;

    try {
      if (outerPathEl.isPointInFill(pt)) return true;
      if (leafPathEl.isPointInFill(pt)) return true;
    } catch (e) {
      return (
        sx >= outerBBox.x &&
        sx <= outerBBox.x + outerBBox.width &&
        sy >= outerBBox.y &&
        sy <= outerBBox.y + outerBBox.height
      );
    }

    return false;
  }

  function screenToWorld(clientX, clientY) {
    const rect = renderer.domElement.getBoundingClientRect();
    const mx = ((clientX - rect.left) / rect.width) * 2 - 1;
    const my = -((clientY - rect.top) / rect.height) * 2 + 1;
    const vec = new THREE.Vector3(mx, my, 0.5);

    vec.unproject(camera);

    const dir = vec.sub(camera.position).normalize();
    const dist = -camera.position.z / dir.z;

    return camera.position.clone().add(dir.multiplyScalar(dist));
  }

  function computeProbOrganic(worldX) {
    const relX = worldX / Math.max(halfWidthWorld, 0.001);
    return smoothstep(-0.3, 0.3, relX);
  }

  let isPressing = false;
  let pointerX = 0;
  let pointerY = 0;
  let pressOnLemon = false;
  let pressVisual = 0;
  let lemonSpawnTimer = 0;
  let sacredDragTimer = 0;

  const onPointerDown = (e) => {
    if (e.pointerType === "mouse" && e.button !== 0) return;

    pointerX = e.clientX;
    pointerY = e.clientY;

    const world = screenToWorld(pointerX, pointerY);
    if (!isInsideLemon(world.x, world.y)) return;

    isPressing = true;
    pressOnLemon = true;

    const probOrganic = computeProbOrganic(world.x);
    emit(world.x, world.y, 280, probOrganic);

    if (Math.random() < 0.35) emitOneLemonIcon();
    if (1 - probOrganic > 0.3) {
      emitSacred(world.x, world.y, 2 + Math.floor(Math.random() * 2), 1 - probOrganic);
    }

    lemonSpawnTimer = 0;
    sacredDragTimer = 0;

    try {
      renderer.domElement.setPointerCapture(e.pointerId);
    } catch (err) {}
  };

  const onPointerMove = (e) => {
    pointerX = e.clientX;
    pointerY = e.clientY;

    const world = screenToWorld(pointerX, pointerY);
    const onLemon = isInsideLemon(world.x, world.y);

    renderer.domElement.style.cursor = onLemon ? "pointer" : "default";

    if (isPressing) pressOnLemon = onLemon;
  };

  const onPointerUp = () => {
    isPressing = false;
    pressOnLemon = false;
  };

  renderer.domElement.addEventListener("pointerdown", onPointerDown);
  renderer.domElement.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", onPointerUp);

  function updateFlat(dt, t) {
    for (let i = 0; i < FLAT_COUNT; i++) {
      if (flat.life[i] <= 0) {
        flat.alphas[i] = 0;
        flat.lifeRatios[i] = 0;
        continue;
      }

      flat.life[i] -= dt;

      if (flat.life[i] <= 0) {
        flat.alphas[i] = 0;
        flat.lifeRatios[i] = 0;
        continue;
      }

      let vx = flat.velocities[i * 3];
      let vy = flat.velocities[i * 3 + 1];

      vx *= 0.978;
      vy *= 0.978;

      const s = flat.seeds[i];

      vx += Math.sin(t * 1.2 + s * 1.7) * 0.4 * dt;
      vy += Math.cos(t * 1.5 + s * 2.1) * 0.4 * dt;

      flat.velocities[i * 3] = vx;
      flat.velocities[i * 3 + 1] = vy;

      flat.positions[i * 3] += vx * dt;
      flat.positions[i * 3 + 1] += vy * dt;

      const r = flat.life[i] / flat.maxLife[i];
      flat.lifeRatios[i] = r;

      const fadeIn = Math.min(1, (1 - r) * 8);

      if (flat.dissolves[i] > 0.5) {
        flat.alphas[i] = fadeIn * 0.98;
      } else {
        const fadeOut = r * r;
        flat.alphas[i] = Math.min(fadeIn, fadeOut) * 0.98;
      }
    }

    flatGeom.attributes.position.needsUpdate = true;
    flatGeom.attributes.alpha.needsUpdate = true;
    flatGeom.attributes.customColor.needsUpdate = true;
    flatGeom.attributes.size.needsUpdate = true;
    flatGeom.attributes.seed.needsUpdate = true;
    flatGeom.attributes.rotation.needsUpdate = true;
    flatGeom.attributes.rotationSpeed.needsUpdate = true;
    flatGeom.attributes.dissolve.needsUpdate = true;
    flatGeom.attributes.lifeRatio.needsUpdate = true;
    flatMat.uniforms.uTime.value = t;
  }

  function updateCubes(dt) {
    for (let i = 0; i < CUBE_COUNT; i++) {
      if (cube.life[i] <= 0) {
        if (cubeAlphas[i] !== 0) {
          cubeAlphas[i] = 0;
          tempMatrix.makeScale(0, 0, 0);
          cubeMesh.setMatrixAt(i, tempMatrix);
        }
        continue;
      }

      cube.life[i] -= dt;

      if (cube.life[i] <= 0) {
        cubeAlphas[i] = 0;
        tempMatrix.makeScale(0, 0, 0);
        cubeMesh.setMatrixAt(i, tempMatrix);
        continue;
      }

      cube.velocities[i * 3] *= 0.975;
      cube.velocities[i * 3 + 1] *= 0.975;
      cube.velocities[i * 3 + 2] *= 0.975;

      cube.positions[i * 3] += cube.velocities[i * 3] * dt;
      cube.positions[i * 3 + 1] += cube.velocities[i * 3 + 1] * dt;
      cube.positions[i * 3 + 2] += cube.velocities[i * 3 + 2] * dt;

      cube.rotations[i * 3] += cube.rotationSpeeds[i * 3] * dt;
      cube.rotations[i * 3 + 1] += cube.rotationSpeeds[i * 3 + 1] * dt;
      cube.rotations[i * 3 + 2] += cube.rotationSpeeds[i * 3 + 2] * dt;

      const s = cube.sizes[i];

      tempEuler.set(
        cube.rotations[i * 3],
        cube.rotations[i * 3 + 1],
        cube.rotations[i * 3 + 2]
      );

      tempMatrix.makeRotationFromEuler(tempEuler);
      tempMatrix.scale(tempScaleVec.set(s, s, s));

      tempMatrix.setPosition(
        cube.positions[i * 3],
        cube.positions[i * 3 + 1],
        cube.positions[i * 3 + 2]
      );

      cubeMesh.setMatrixAt(i, tempMatrix);

      const r = cube.life[i] / cube.maxLife[i];
      const fadeIn = Math.min(1, (1 - r) * 8);
      const fadeOut = Math.min(1, r * 2);

      cubeAlphas[i] = Math.min(fadeIn, fadeOut) * 0.98;
    }

    cubeMesh.instanceMatrix.needsUpdate = true;
    cubeGeom.attributes.aColor.needsUpdate = true;
    cubeGeom.attributes.aAlpha.needsUpdate = true;
    cubeGeom.attributes.aMode.needsUpdate = true;
  }

  function updateLemonIcons(dt) {
    for (let i = 0; i < LEMON_ICON_COUNT; i++) {
      if (lemonIcon.life[i] <= 0) {
        if (lemonIconAlphas[i] !== 0) {
          lemonIconAlphas[i] = 0;
          tempMatrix.makeScale(0, 0, 0);
          lemonIconMesh.setMatrixAt(i, tempMatrix);
        }
        continue;
      }

      lemonIcon.life[i] -= dt;

      if (lemonIcon.life[i] <= 0) {
        lemonIconAlphas[i] = 0;
        tempMatrix.makeScale(0, 0, 0);
        lemonIconMesh.setMatrixAt(i, tempMatrix);
        continue;
      }

      lemonIcon.velocities[i * 3] *= 0.98;
      lemonIcon.velocities[i * 3 + 1] *= 0.98;
      lemonIcon.velocities[i * 3 + 2] *= 0.98;

      lemonIcon.positions[i * 3] += lemonIcon.velocities[i * 3] * dt;
      lemonIcon.positions[i * 3 + 1] += lemonIcon.velocities[i * 3 + 1] * dt;
      lemonIcon.positions[i * 3 + 2] += lemonIcon.velocities[i * 3 + 2] * dt;

      lemonIcon.rotations[i * 3] += lemonIcon.rotationSpeeds[i * 3] * dt;
      lemonIcon.rotations[i * 3 + 1] += lemonIcon.rotationSpeeds[i * 3 + 1] * dt;
      lemonIcon.rotations[i * 3 + 2] += lemonIcon.rotationSpeeds[i * 3 + 2] * dt;

      const s = lemonIcon.sizes[i];

      tempEuler.set(
        lemonIcon.rotations[i * 3],
        lemonIcon.rotations[i * 3 + 1],
        lemonIcon.rotations[i * 3 + 2]
      );

      tempMatrix.makeRotationFromEuler(tempEuler);
      tempMatrix.scale(tempScaleVec.set(s, s, s));

      tempMatrix.setPosition(
        lemonIcon.positions[i * 3],
        lemonIcon.positions[i * 3 + 1],
        lemonIcon.positions[i * 3 + 2]
      );

      lemonIconMesh.setMatrixAt(i, tempMatrix);

      const r = lemonIcon.life[i] / lemonIcon.maxLife[i];
      const fadeIn = Math.min(1, (1 - r) * 6);
      const fadeOut = Math.min(1, r * 2);

      lemonIconAlphas[i] = Math.min(fadeIn, fadeOut) * 0.98;
    }

    lemonIconMesh.instanceMatrix.needsUpdate = true;
    lemonIconGeom.attributes.aColor.needsUpdate = true;
    lemonIconGeom.attributes.aAlpha.needsUpdate = true;
  }

  function updateOrganic(dt, t) {
    for (let i = 0; i < ORG_COUNT; i++) {
      if (org.life[i] <= 0) {
        org.alphas[i] = 0;
        continue;
      }

      org.life[i] -= dt;

      if (org.life[i] <= 0) {
        org.alphas[i] = 0;
        continue;
      }

      let vx = org.velocities[i * 3];
      let vy = org.velocities[i * 3 + 1];
      let vz = org.velocities[i * 3 + 2];

      const s = org.seeds[i];

      const turbX =
        Math.sin(t * 0.6 + s * 1.3) * 0.6 +
        Math.sin(t * 1.7 + s * 2.7) * 0.35 +
        Math.sin(t * 3.4 + s * 4.1) * 0.18;

      const turbY =
        Math.cos(t * 0.8 + s * 1.7) * 0.6 +
        Math.cos(t * 1.9 + s * 2.9) * 0.35 +
        Math.cos(t * 3.7 + s * 4.7) * 0.18;

      vx += turbX * 0.5 * dt;
      vy += turbY * 0.5 * dt;
      vy -= dt * 0.28;

      vx *= 0.97;
      vy *= 0.97;
      vz *= 0.97;

      org.velocities[i * 3] = vx;
      org.velocities[i * 3 + 1] = vy;
      org.velocities[i * 3 + 2] = vz;

      org.positions[i * 3] += vx * dt;
      org.positions[i * 3 + 1] += vy * dt;
      org.positions[i * 3 + 2] += vz * dt;

      const r = org.life[i] / org.maxLife[i];
      const fadeIn = Math.min(1, (1 - r) * 6);
      const fadeOut = r * r;

      org.alphas[i] = Math.min(fadeIn, fadeOut) * 0.96;
    }

    orgGeom.attributes.position.needsUpdate = true;
    orgGeom.attributes.alpha.needsUpdate = true;
    orgGeom.attributes.customColor.needsUpdate = true;
    orgGeom.attributes.size.needsUpdate = true;
    orgGeom.attributes.seed.needsUpdate = true;
    orgMat.uniforms.uTime.value = t;
  }

  function updateSacred(dt, t) {
    for (let i = 0; i < SACRED_COUNT; i++) {
      const mesh = sacred.meshes[i];

      if (sacred.life[i] <= 0) {
        mesh.visible = false;
        mesh.material.opacity = 0;
        continue;
      }

      sacred.life[i] -= dt;

      if (sacred.life[i] <= 0) {
        mesh.visible = false;
        mesh.material.opacity = 0;
        continue;
      }

      sacred.velocities[i * 3] *= 0.988;
      sacred.velocities[i * 3 + 1] *= 0.988;
      sacred.velocities[i * 3 + 2] *= 0.988;

      sacred.positions[i * 3] += sacred.velocities[i * 3] * dt;
      sacred.positions[i * 3 + 1] += sacred.velocities[i * 3 + 1] * dt;
      sacred.positions[i * 3 + 2] += sacred.velocities[i * 3 + 2] * dt;

      sacred.rotations[i * 3] += sacred.rotationSpeeds[i * 3] * dt;
      sacred.rotations[i * 3 + 1] += sacred.rotationSpeeds[i * 3 + 1] * dt;
      sacred.rotations[i * 3 + 2] += sacred.rotationSpeeds[i * 3 + 2] * dt;

      const r = sacred.life[i] / sacred.maxLife[i];
      const fadeIn = Math.min(1, (1 - r) * 4.8);
      const fadeOut = Math.min(1, r * 2.1);
      const dance = sacred.dance[i];

      const driftX = Math.sin(t * 1.05 + dance) * 0.045 + Math.sin(t * 2.4 + dance * 0.7) * 0.018;
      const driftY = Math.cos(t * 0.9 + dance) * 0.045 + Math.cos(t * 2.1 + dance * 0.9) * 0.018;
      const pulse = 1 + Math.sin(t * 2.2 + dance) * 0.075 + Math.sin(t * 5.3 + dance) * 0.028;

      mesh.position.set(
        sacred.positions[i * 3] + driftX,
        sacred.positions[i * 3 + 1] + driftY,
        sacred.positions[i * 3 + 2]
      );

      mesh.rotation.set(
        sacred.rotations[i * 3] + Math.sin(t * 0.95 + dance) * 0.16,
        sacred.rotations[i * 3 + 1] + Math.cos(t * 0.82 + dance) * 0.16,
        sacred.rotations[i * 3 + 2] + Math.sin(t * 0.65 + dance) * 0.12
      );

      mesh.scale.setScalar(sacred.sizes[i] * pulse);
      mesh.material.opacity = Math.min(fadeIn, fadeOut) * 0.66;
      mesh.visible = true;
    }
  }

  const clock = new THREE.Clock();

  let dragEmitAccumulator = 0;
  let autoBurstTimer = 0;
  let nextAutoBurst = 24 + Math.random() * 14;
  let raf;

  function emitAmbientBurst() {
    // Small autonomous activation every so often, so the mark feels alive without user input.
    const side = Math.random();
    let x;
    let probOrganic;

    if (side < 0.34) {
      x = -halfWidthWorld * (0.42 + Math.random() * 0.42);
      probOrganic = 0.1 + Math.random() * 0.22;
    } else if (side < 0.68) {
      x = halfWidthWorld * (0.28 + Math.random() * 0.58);
      probOrganic = 0.72 + Math.random() * 0.24;
    } else {
      x = (Math.random() - 0.5) * halfWidthWorld * 0.7;
      probOrganic = 0.35 + Math.random() * 0.35;
    }

    const y = (Math.random() - 0.5) * 0.86;
    const count = 120 + Math.floor(Math.random() * 120);
    emit(x, y, count, probOrganic);

    if (probOrganic < 0.45 && Math.random() < 0.75) {
      emitSacred(x, y, 1 + Math.floor(Math.random() * 2), 1 - probOrganic);
    }

    if (probOrganic > 0.6) {
      emitInto(org, spawnOrganic, 90 + Math.floor(Math.random() * 130), x, y);
    }
  }

  function tick() {
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.getElapsedTime();

    if (isPressing && pressOnLemon) {
      const world = screenToWorld(pointerX, pointerY);

      if (isInsideLemon(world.x, world.y)) {
        const probOrganic = computeProbOrganic(world.x);

        dragEmitAccumulator += dt * 14 * 60;

        const toEmit = Math.floor(dragEmitAccumulator);
        dragEmitAccumulator -= toEmit;

        if (toEmit > 0) emit(world.x, world.y, toEmit, probOrganic);

        lemonSpawnTimer += dt;
        sacredDragTimer += dt;

        if (lemonSpawnTimer >= 0.8) {
          lemonSpawnTimer = 0;
          if (Math.random() < 0.6) emitOneLemonIcon();
        }

        if (sacredDragTimer >= 0.38 && 1 - probOrganic > 0.44) {
          sacredDragTimer = 0;
          if (Math.random() < 0.7) emitSacred(world.x, world.y, 1, 1 - probOrganic);
        }
      } else {
        dragEmitAccumulator = 0;
        sacredDragTimer = 0;
      }
    } else {
      dragEmitAccumulator = 0;
      sacredDragTimer = 0;
    }

    if (!isPressing) {
      autoBurstTimer += dt;
      if (autoBurstTimer >= nextAutoBurst) {
        autoBurstTimer = 0;
        nextAutoBurst = 24 + Math.random() * 16;
        emitAmbientBurst();
      }
    }

    updateOrganic(dt, t);
    updateFlat(dt, t);
    updateCubes(dt);
    updateLemonIcons(dt);
    updateSacred(dt, t);

    grainMat.uniforms.uTime.value = t;

    const target = isPressing && pressOnLemon ? 1 : 0;
    pressVisual += (target - pressVisual) * Math.min(1, dt * 14);
    lemonGroup.scale.setScalar(1 - pressVisual * 0.012);

    renderer.render(scene, camera);
    raf = requestAnimationFrame(tick);
  }

  tick();

  const onResize = () => {
    width = mount.clientWidth;
    height = mount.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  };

  window.addEventListener("resize", onResize);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLemoineExplosion);
} else {
  initLemoineExplosion();
}
