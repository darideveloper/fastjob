(function () {
  'use strict';

  var NS = window.FastJobFilter;
  if (!NS) return;

  NS.readyPromise.then(function () {
    var suggestionEls = document.querySelectorAll('[data-search-suggestion]');
    if (!suggestionEls.length) return;

    var opts = NS.optionsData;

    if (!opts || !opts.areas || !opts.locations || opts.areas.length < 2 || opts.locations.length < 2) {
      [].forEach.call(suggestionEls, function (el) {
        el.textContent = 'Busca por sector y ubicación';
      });
      return;
    }

    var displayStrings = [];
    var stringMeta = [];
    var shuffledAreas = opts.areas.slice().sort(function () { return Math.random() - 0.5; });
    var shuffledLocations = opts.locations.slice().sort(function () { return Math.random() - 0.5; });
    for (var i = 0; i < 10; i++) {
      var area = shuffledAreas[i % shuffledAreas.length];
      var loc = shuffledLocations[(i + 3) % shuffledLocations.length];
      var capArea = area.charAt(0).toUpperCase() + area.slice(1);
      var capLoc = loc.charAt(0).toUpperCase() + loc.slice(1);
      displayStrings.push(capArea + ' en ' + capLoc + '...');
      stringMeta.push({ area: area, location: loc });
    }

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    [].forEach.call(suggestionEls, function (el) {
      var parent = el.parentElement;
      var widget = parent
        ? (parent.matches && parent.matches('[data-filter-widget]')
            ? parent
            : parent.querySelector('[data-filter-widget]'))
        : null;

      if (reducedMotion) {
        el.textContent = displayStrings[0];
        return;
      }

      var typed = new Typed(el, {
        strings: displayStrings,
        typeSpeed: 50,
        backSpeed: 30,
        backDelay: 2000,
        loop: true,
        shuffle: true,
        showCursor: true,
        cursorChar: '|'
      });

      if (widget) {
        var inputs = widget.querySelectorAll('[data-combobox] input[type="text"]');
        [].forEach.call(inputs, function (input) {
          input.addEventListener('focus', function () { typed.stop(); });
          input.addEventListener('blur', function () {
            setTimeout(function () {
              var anyFocused = false;
              [].forEach.call(inputs, function (inp) {
                if (inp === document.activeElement) anyFocused = true;
              });
              if (!anyFocused) typed.start();
            }, 100);
          });
        });
      }

      el.addEventListener('click', function () {
        var seq = typed.sequence;
        var pos = typed.arrayPos;
        var currentDisplay = typed.strings[seq[pos]];
        if (!currentDisplay) return;

        var meta = null;
        for (var m = 0; m < displayStrings.length; m++) {
          if (displayStrings[m] === currentDisplay) {
            meta = stringMeta[m];
            break;
          }
        }
        if (!meta) return;

        if (widget) {
          NS.clearWidget(widget);
        }

        if (meta.area && widget) {
          NS.addValue(widget, 'area', meta.area);
        }
        if (meta.location && widget) {
          NS.addValue(widget, 'location', meta.location);
        }
      });
    });
  });
})();
