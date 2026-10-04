/*
 * motion.js — 시간(t)만 넣으면 화면이 결정되는 초소형 모션그래픽 엔진
 *
 * 핵심 규칙: 모든 장면은 "render(t)" 하나로 그린다. (t = 초 단위 현재 시간)
 *  - 브라우저에서 열면: 실시간 재생 + 하단 재생바(스페이스=재생/정지, ←/→ = 0.5초 이동)
 *  - render.js 로 렌더링하면: 프레임마다 window.__seek(t) 를 호출해 MP4로 저장
 *
 * 사용법 (HTML 안에서):
 *   Motion.start({ width:1920, height:1080, duration:11, render(t, M){ ... } })
 */
(function () {
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, p) => a + (b - a) * p;

  const ease = {
    linear: p => p,
    inQuad: p => p * p,
    outQuad: p => 1 - (1 - p) * (1 - p),
    inOutQuad: p => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2),
    outCubic: p => 1 - Math.pow(1 - p, 3),
    inOutCubic: p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    outExpo: p => (p === 1 ? 1 : 1 - Math.pow(2, -10 * p)),
    inOutExpo: p =>
      p === 0 ? 0 : p === 1 ? 1 : p < 0.5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2,
    outBack: p => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
    outElastic: p =>
      p === 0 ? 0 : p === 1 ? 1 : Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1,
  };

  // 구간 진행률: t가 start~end 사이에서 0→1 (이징 적용)
  const prog = (t, start, end, e = ease.inOutCubic) => e(clamp((t - start) / (end - start)));

  // 키프레임: key(t, [[0, 0], [1, 100, 'outBack'], [2, 50]])  →  해당 시간의 값
  function key(t, frames) {
    if (t <= frames[0][0]) return frames[0][1];
    for (let i = 1; i < frames.length; i++) {
      const [t1, v1, e] = frames[i];
      const [t0, v0] = frames[i - 1];
      if (t <= t1) {
        const p = (ease[e] || ease.inOutCubic)(clamp((t - t0) / (t1 - t0)));
        return Array.isArray(v0) ? v0.map((x, j) => lerp(x, v1[j], p)) : lerp(v0, v1, p);
      }
    }
    return frames[frames.length - 1][1];
  }

  // 결정적 난수 (매 프레임 같은 값 → 렌더링 결과가 흔들리지 않음)
  function rand(seed) {
    let s = seed >>> 0 || 1;
    return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  }

  // 스타일 일괄 지정 헬퍼: set(el, {x, y, s, r, o, ...css})
  function set(el, o) {
    if (!el) return;
    const tf = [];
    if (o.x !== undefined || o.y !== undefined) tf.push(`translate(${o.x || 0}px, ${o.y || 0}px)`);
    if (o.s !== undefined) tf.push(`scale(${o.s})`);
    if (o.sx !== undefined || o.sy !== undefined) tf.push(`scale(${o.sx ?? 1}, ${o.sy ?? 1})`);
    if (o.r !== undefined) tf.push(`rotate(${o.r}deg)`);
    if (tf.length) el.style.transform = tf.join(' ');
    if (o.o !== undefined) el.style.opacity = o.o;
    for (const k in o) if (!['x', 'y', 's', 'sx', 'sy', 'r', 'o'].includes(k)) el.style[k] = o[k];
  }

  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));

  const M = { clamp, lerp, ease, prog, key, rand, set, $, $$ };

  function start(cfg) {
    const params = new URLSearchParams(location.search);
    const W = +params.get('w') || cfg.width || 1920;
    const H = +params.get('h') || cfg.height || 1080;
    const duration = cfg.duration;
    const renderMode = params.has('render');

    const stage = document.getElementById('stage');
    stage.style.width = W + 'px';
    stage.style.height = H + 'px';
    stage.classList.toggle('portrait', H > W);
    document.documentElement.style.setProperty('--W', W);
    document.documentElement.style.setProperty('--H', H);

    M.W = W; M.H = H; M.portrait = H > W;
    if (cfg.setup) cfg.setup(M);

    const draw = t => cfg.render(clamp(t, 0, duration), M);

    window.__DURATION = duration;
    window.__SIZE = { width: W, height: H };
    window.__seek = t => { draw(t); return true; };

    if (renderMode) {
      document.body.classList.add('render');
      draw(0);
      return;
    }

    // ── 미리보기 모드: 화면 맞춤 + 재생바 ──
    const fit = () => {
      const s = Math.min(innerWidth / W, (innerHeight - 56) / H);
      stage.style.transform = `scale(${s})`;
      stage.style.transformOrigin = 'top left';
      stage.style.left = (innerWidth - W * s) / 2 + 'px';
      stage.style.top = (innerHeight - 56 - H * s) / 2 + 'px';
    };
    addEventListener('resize', fit); fit();

    const bar = document.createElement('div');
    bar.id = 'mbar';
    bar.innerHTML = `<button id="mplay">❚❚</button><input id="mseek" type="range" min="0" max="${duration}" step="0.01" value="0"><span id="mtime"></span>`;
    document.body.appendChild(bar);
    const css = document.createElement('style');
    css.textContent = `#stage{position:absolute;overflow:hidden}
      #mbar{position:fixed;left:0;right:0;bottom:0;height:56px;display:flex;align-items:center;gap:12px;padding:0 16px;background:#111;color:#eee;font:14px system-ui;z-index:9}
      #mbar button{width:40px;height:32px;border:0;border-radius:6px;background:#333;color:#fff;cursor:pointer}
      #mbar input{flex:1}`;
    document.head.appendChild(css);

    let t = 0, playing = true, last = performance.now();
    const play = $('#mplay'), seek = $('#mseek'), time = $('#mtime');
    const toggle = () => { playing = !playing; play.textContent = playing ? '❚❚' : '▶'; if (playing && t >= duration) t = 0; };
    play.onclick = toggle;
    seek.oninput = () => { t = +seek.value; draw(t); };
    addEventListener('keydown', e => {
      if (e.code === 'Space') { e.preventDefault(); toggle(); }
      if (e.code === 'ArrowRight') t = Math.min(duration, t + 0.5);
      if (e.code === 'ArrowLeft') t = Math.max(0, t - 0.5);
    });
    (function loop(now) {
      if (playing) { t += (now - last) / 1000; if (t >= duration) { t = duration; toggle(); } }
      last = now;
      draw(t);
      seek.value = t;
      time.textContent = `${t.toFixed(2)}s / ${duration}s`;
      requestAnimationFrame(loop);
    })(last);
  }

  M.start = start;
  window.Motion = M;
})();
