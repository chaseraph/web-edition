(function() {
  var canvas = document.getElementById('snake-canvas');
  var ctx = canvas.getContext('2d');
  var scoreEl = document.getElementById('snake-score');
  var bestEl = document.getElementById('snake-best');

  var COLS = 20, ROWS = 20, CELL;
  var snake, dir, nextDir, food, score, best, alive, started, speed, loop;

  // Solarized palette
  var COL_BG = '#073642';
  var COL_GRID = '#0a3d4a';
  var COL_SNAKE = '#859900';
  var COL_HEAD = '#b8db00';
  var COL_FOOD = '#cb4b16';
  var COL_DEAD = '#dc322f';

  best = +(localStorage.getItem('snakeBest') || 0);
  bestEl.textContent = 'Best: ' + best;

  function resize() {
    var maxW = canvas.parentElement.clientWidth;
    var size = Math.min(400, maxW);
    canvas.width = size;
    canvas.height = size;
    CELL = size / COLS;
  }

  function init() {
    resize();
    var mid = Math.floor(COLS / 2);
    snake = [{x: mid, y: mid}, {x: mid - 1, y: mid}, {x: mid - 2, y: mid}];
    dir = {x: 1, y: 0};
    nextDir = {x: 1, y: 0};
    score = 0;
    alive = true;
    started = false;
    speed = 200;
    scoreEl.textContent = '0';
    placeFood();
    draw();
  }

  function placeFood() {
    var free = [];
    for (var r = 0; r < ROWS; r++) {
      for (var c = 0; c < COLS; c++) {
        var occupied = false;
        for (var i = 0; i < snake.length; i++) {
          if (snake[i].x === c && snake[i].y === r) { occupied = true; break; }
        }
        if (!occupied) free.push({x: c, y: r});
      }
    }
    food = free[Math.floor(Math.random() * free.length)];
  }

  function draw() {
    ctx.fillStyle = COL_BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid lines
    ctx.strokeStyle = COL_GRID;
    ctx.lineWidth = 0.5;
    for (var i = 0; i <= COLS; i++) {
      ctx.beginPath();
      ctx.moveTo(i * CELL, 0);
      ctx.lineTo(i * CELL, canvas.height);
      ctx.stroke();
    }
    for (var j = 0; j <= ROWS; j++) {
      ctx.beginPath();
      ctx.moveTo(0, j * CELL);
      ctx.lineTo(canvas.width, j * CELL);
      ctx.stroke();
    }

    // Food
    if (food) {
      ctx.fillStyle = COL_FOOD;
      ctx.beginPath();
      ctx.arc(food.x * CELL + CELL / 2, food.y * CELL + CELL / 2, CELL / 2.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // Snake
    for (var i = 0; i < snake.length; i++) {
      var s = snake[i];
      if (!alive) {
        ctx.fillStyle = COL_DEAD;
      } else if (i === 0) {
        ctx.fillStyle = COL_HEAD;
      } else {
        ctx.fillStyle = COL_SNAKE;
      }
      var pad = 1;
      ctx.fillRect(s.x * CELL + pad, s.y * CELL + pad, CELL - pad * 2, CELL - pad * 2);
    }

    // Overlay text
    if (!started && alive) {
      overlay('SNAKE', 'Press any key or tap to start');
    } else if (!alive) {
      overlay('GAME OVER', 'Score: ' + score + '  \u2022  Tap or press to restart');
    }
  }

  function overlay(title, sub) {
    ctx.fillStyle = 'rgba(0,43,54,0.8)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#fdf6e3';
    ctx.textAlign = 'center';
    ctx.font = 'bold ' + (CELL * 1.8) + 'px Newsreader, Georgia, serif';
    ctx.fillText(title, canvas.width / 2, canvas.height / 2 - CELL * 0.5);
    ctx.font = (CELL * 0.7) + 'px Newsreader, Georgia, serif';
    ctx.fillText(sub, canvas.width / 2, canvas.height / 2 + CELL * 1.2);
  }

  function step() {
    dir = nextDir;
    var head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};

    // Wall wrap
    if (head.x < 0) head.x = COLS - 1;
    if (head.x >= COLS) head.x = 0;
    if (head.y < 0) head.y = ROWS - 1;
    if (head.y >= ROWS) head.y = 0;

    // Self collision
    for (var i = 0; i < snake.length; i++) {
      if (snake[i].x === head.x && snake[i].y === head.y) {
        alive = false;
        clearInterval(loop);
        if (score > best) {
          best = score;
          localStorage.setItem('snakeBest', best);
          bestEl.textContent = 'Best: ' + best;
        }
        draw();
        return;
      }
    }

    snake.unshift(head);

    // Eat food
    if (food && head.x === food.x && head.y === food.y) {
      score++;
      scoreEl.textContent = score;
      placeFood();
      // Speed up slightly
      if (speed > 80) {
        speed -= 3;
        clearInterval(loop);
        loop = setInterval(step, speed);
      }
    } else {
      snake.pop();
    }

    draw();
  }

  function setDir(dx, dy) {
    // Prevent 180-degree reversal
    if (dir.x === -dx && dir.y === -dy) return;
    if (dx !== 0 || dy !== 0) {
      nextDir = {x: dx, y: dy};
    }
    if (!started && alive) {
      started = true;
      loop = setInterval(step, speed);
    }
    if (!alive) {
      init();
    }
  }

  // Keyboard
  document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowUp' || e.key === 'w') { e.preventDefault(); setDir(0, -1); }
    else if (e.key === 'ArrowDown' || e.key === 's') { e.preventDefault(); setDir(0, 1); }
    else if (e.key === 'ArrowLeft' || e.key === 'a') { e.preventDefault(); setDir(-1, 0); }
    else if (e.key === 'ArrowRight' || e.key === 'd') { e.preventDefault(); setDir(1, 0); }
    else if (!started || !alive) { setDir(dir.x, dir.y); }
  });

  // Touch swipe
  var touchX, touchY;
  canvas.addEventListener('touchstart', function(e) {
    e.preventDefault();
    touchX = e.touches[0].clientX;
    touchY = e.touches[0].clientY;
    if (!started || !alive) setDir(dir.x, dir.y);
  });
  canvas.addEventListener('touchmove', function(e) {
    e.preventDefault();
  });
  canvas.addEventListener('touchend', function(e) {
    e.preventDefault();
    if (!e.changedTouches.length) return;
    var dx = e.changedTouches[0].clientX - touchX;
    var dy = e.changedTouches[0].clientY - touchY;
    if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return; // tap, not swipe
    if (Math.abs(dx) > Math.abs(dy)) {
      setDir(dx > 0 ? 1 : -1, 0);
    } else {
      setDir(0, dy > 0 ? 1 : -1);
    }
  });

  // Click to start/restart on desktop
  canvas.addEventListener('click', function() {
    if (!started || !alive) setDir(dir.x, dir.y);
  });

  // D-pad buttons
  var btnUp = document.getElementById('snake-up');
  var btnDown = document.getElementById('snake-down');
  var btnLeft = document.getElementById('snake-left');
  var btnRight = document.getElementById('snake-right');
  if (btnUp) btnUp.addEventListener('click', function() { setDir(0, -1); });
  if (btnDown) btnDown.addEventListener('click', function() { setDir(0, 1); });
  if (btnLeft) btnLeft.addEventListener('click', function() { setDir(-1, 0); });
  if (btnRight) btnRight.addEventListener('click', function() { setDir(1, 0); });

  window.addEventListener('resize', function() {
    resize();
    draw();
  });

  init();
})();
