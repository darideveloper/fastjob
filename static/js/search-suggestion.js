(function () {
  'use strict';

  var NS = window.FastJobFilter;
  if (!NS) return;

  var typedInstances = [];
  var currentOpts = null;

  function buildSuggestions(opts) {
    if (!opts || !opts.areas || !opts.locations || opts.areas.length < 2 || opts.locations.length < 2) {
      return null;
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

    return { displayStrings: displayStrings, stringMeta: stringMeta };
  }

  function initTyped(el, displayStrings) {
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reducedMotion) {
      el.textContent = displayStrings[0];
      return null;
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

    return typed;
  }

  function initSuggestionElements() {
    var suggestionEls = document.querySelectorAll('[data-search-suggestion]');
    if (!suggestionEls.length) return;

    if (!currentOpts || !currentOpts.areas || !currentOpts.locations || currentOpts.areas.length < 2 || currentOpts.locations.length < 2) {
      [].forEach.call(suggestionEls, function (el) {
        el.textContent = 'Busca por sector y ubicación';
      });
      return;
    }

    var sug = buildSuggestions(currentOpts);
    if (!sug) {
      [].forEach.call(suggestionEls, function (el) {
        el.textContent = 'Busca por sector y ubicación';
      });
      return;
    }

    typedInstances = [];

    [].forEach.call(suggestionEls, function (el) {
      var parent = el.parentElement;
      var widget = parent
        ? (parent.matches && parent.matches('[data-filter-widget]')
            ? parent
            : parent.querySelector('[data-filter-widget]'))
        : null;

      var typed = initTyped(el, sug.displayStrings);
      if (typed) {
        typedInstances.push(typed);
      }

      var widgetInputs = widget ? widget.querySelectorAll('[data-combobox] input[type="text"]') : [];
      [].forEach.call(widgetInputs, function (input) {
        input.addEventListener('focus', hideSuggestions);
      });

      var clickHandler = function () {
        hideSuggestions();
        if (!typed) return;
        var seq = typed.sequence;
        var pos = typed.arrayPos;
        var currentDisplay = typed.strings[seq[pos]];
        if (!currentDisplay) return;

        var meta = null;
        for (var m = 0; m < sug.displayStrings.length; m++) {
          if (sug.displayStrings[m] === currentDisplay) {
            meta = sug.stringMeta[m];
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
      };

      el.addEventListener('click', clickHandler);
    });
  }

  var userInteracted = false;

  function hideSuggestions() {
    if (userInteracted) return;
    userInteracted = true;

    typedInstances.forEach(function (instance) {
      try { instance.stop(); } catch (e) {}
    });

    var suggestionEls = document.querySelectorAll('[data-search-suggestion]');
    [].forEach.call(suggestionEls, function (el) {
      el.style.transition = 'opacity 0.3s ease';
      el.style.opacity = '0';
    });

    setTimeout(function () {
      typedInstances.forEach(function (instance) {
        try { instance.destroy(); } catch (e) {}
      });
      typedInstances = [];

      [].forEach.call(suggestionEls, function (el) {
        el.innerHTML = '';
      });
    }, 350);
  }

  NS.readyPromise.then(function () {
    currentOpts = NS.optionsData;
    initSuggestionElements();
  });
})();
