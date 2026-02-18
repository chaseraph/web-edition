(function() {
  const KEY = [
    ['C','A','M','P','S'],
    ['A','L','E','R','T'],
    ['M','E','D','I','A'],
    ['P','R','I','N','T'],
    ['S','T','A','T','E']
  ];
  const grid = document.getElementById('xword');
  const inputs = grid.querySelectorAll('input');
  const clues = document.querySelectorAll('.clue');

  let direction = 'across';

  function getNeighbor(el, dr, dc) {
    const r = +el.dataset.r + dr, c = +el.dataset.c + dc;
    return grid.querySelector('input[data-r="' + r + '"][data-c="' + c + '"]');
  }
  function getNext(el) {
    if (direction === 'across') return getNeighbor(el, 0, 1);
    return getNeighbor(el, 1, 0);
  }
  function getPrev(el) {
    if (direction === 'across') return getNeighbor(el, 0, -1);
    return getNeighbor(el, -1, 0);
  }
  function highlightWord(el) {
    const r = +el.dataset.r, c = +el.dataset.c;
    if (direction === 'across') {
      for (var i = 0; i < 5; i++) {
        var cell = grid.querySelector('input[data-r="' + r + '"][data-c="' + i + '"]');
        if (cell) cell.parentElement.classList.add('highlight');
      }
    } else {
      for (var i = 0; i < 5; i++) {
        var cell = grid.querySelector('input[data-r="' + i + '"][data-c="' + c + '"]');
        if (cell) cell.parentElement.classList.add('highlight');
      }
    }
  }
  function checkWin() {
    var complete = true;
    inputs.forEach(function(inp) {
      var r = +inp.dataset.r, c = +inp.dataset.c;
      if (inp.value.toUpperCase() !== KEY[r][c]) complete = false;
    });
    if (complete) {
      inputs.forEach(function(inp) { inp.parentElement.classList.add('correct'); });
      grid.classList.add('solved');
    }
  }

  inputs.forEach(function(inp) {
    inp.addEventListener('input', function() {
      this.value = this.value.toUpperCase();
      if (this.value) {
        var next = getNext(this);
        if (next) next.focus();
      }
      checkWin();
    });
    inp.addEventListener('keydown', function(e) {
      if (e.key === 'Backspace' && !this.value) {
        var prev = getPrev(this);
        if (prev) { prev.focus(); prev.value = ''; }
      }
      if (e.key === 'ArrowRight') { var n = getNeighbor(this, 0, 1); if (n) n.focus(); }
      if (e.key === 'ArrowLeft') { var n = getNeighbor(this, 0, -1); if (n) n.focus(); }
      if (e.key === 'ArrowDown') { var n = getNeighbor(this, 1, 0); if (n) n.focus(); }
      if (e.key === 'ArrowUp') { var n = getNeighbor(this, -1, 0); if (n) n.focus(); }
    });
    inp.addEventListener('focus', function() {
      inputs.forEach(function(i) { i.parentElement.classList.remove('highlight'); });
      highlightWord(this);
      this.select();
    });
  });

  clues.forEach(function(clue) {
    clue.addEventListener('click', function() {
      clues.forEach(function(c) { c.classList.remove('active'); });
      this.classList.add('active');
      var dir = this.dataset.dir;
      var idx = +this.dataset.idx;
      direction = dir;
      var cell = dir === 'across'
        ? grid.querySelector('input[data-r="' + idx + '"][data-c="0"]')
        : grid.querySelector('input[data-r="0"][data-c="' + idx + '"]');
      if (cell) cell.focus();
    });
  });

  document.getElementById('xword-check').addEventListener('click', function() {
    inputs.forEach(function(inp) {
      var r = +inp.dataset.r, c = +inp.dataset.c;
      if (!inp.value) return;
      if (inp.value.toUpperCase() === KEY[r][c]) {
        inp.parentElement.classList.add('correct');
        inp.parentElement.classList.remove('wrong');
      } else {
        inp.parentElement.classList.add('wrong');
        inp.parentElement.classList.remove('correct');
      }
    });
  });

  document.getElementById('xword-reveal').addEventListener('click', function() {
    inputs.forEach(function(inp) {
      var r = +inp.dataset.r, c = +inp.dataset.c;
      inp.value = KEY[r][c];
      inp.parentElement.classList.add('correct');
      inp.parentElement.classList.remove('wrong');
    });
    checkWin();
  });
})();
