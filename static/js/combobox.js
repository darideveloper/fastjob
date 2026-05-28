(function () {
  'use strict';

  var OPTIONS_URL = '/api/companies/filter-options/';
  var COUNT_URL = '/api/companies/count/';
  var AVAILABLE_URL = '/api/companies/available-filters/';

  var optionsPromise = null;

  function fetchOptions() {
    if (!optionsPromise) {
      optionsPromise = fetch(OPTIONS_URL)
        .then(function (r) {
          // A throttled (429) or errored response is NOT valid options data.
          // Treat it as a failure instead of feeding empty lists to the UI.
          if (!r.ok) { throw new Error('filter-options HTTP ' + r.status); }
          return r.json();
        })
        .catch(function (err) {
          // Never memoise a failure: clearing the singleton lets a later
          // call (e.g. the retry button) re-request the options.
          optionsPromise = null;
          throw err;
        });
    }
    return optionsPromise;
  }

  function initCombobox(container, initialOptions, onChange) {
    var options = initialOptions;
    var name = container.dataset.name;
    // data-value is expected to be a comma-separated list of selected names
    var initialValues = container.dataset.value ? container.dataset.value.split(',') : [];
    var selected = initialValues.filter(function(v) { return v.trim().length > 0; });
    var placeholder = container.dataset.placeholder || 'Selecciona opciones…';
    var comboboxType = container.dataset.combobox;
    var noFilterLabel = comboboxType === 'area' ? '— TODOS LOS SECTORES —' : comboboxType === 'location' ? '— TODAS LAS UBICACIONES —' : '— Todos —';

    container.style.position = 'relative';
    container.innerHTML = '';

    // Wrapper for the pills + input
    var controlWrapper = document.createElement('div');
    controlWrapper.className = [
      'w-full border border-gray-200 rounded-xl px-2 py-1.5 text-sm flex flex-wrap gap-1.5 items-center',
      'focus-within:ring-2 focus-within:ring-brand-ring bg-white cursor-text'
    ].join(' ');
    container.appendChild(controlWrapper);

    var pillsWrapper = document.createElement('div');
    pillsWrapper.className = 'flex flex-wrap gap-1.5';
    controlWrapper.appendChild(pillsWrapper);

    var textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.placeholder = selected.length === 0 ? placeholder : '';
    textInput.autocomplete = 'off';
    textInput.className = 'flex-1 min-w-[120px] outline-none bg-transparent py-0.5 px-1';
    controlWrapper.appendChild(textInput);

    // Container for hidden inputs (to be submitted in the form)
    var hiddenContainer = document.createElement('div');
    container.appendChild(hiddenContainer);

    var dropdown = document.createElement('ul');
    dropdown.className = [
      'absolute left-0 right-0 z-20 bg-white border border-gray-200 rounded-xl shadow-lg',
      'mt-1 max-h-[480px] overflow-y-auto'
    ].join(' ');
    dropdown.style.display = 'none';
    container.appendChild(dropdown);

    function updatePills() {
      pillsWrapper.innerHTML = '';
      hiddenContainer.innerHTML = '';
      
      selected.forEach(function(val) {
        // Create pill
        var pill = document.createElement('div');
        pill.className = 'bg-brand-soft text-brand-dark px-2 py-0.5 rounded-lg flex items-center gap-1 text-xs font-medium border border-brand/10';
        pill.style.textTransform = 'uppercase';
        pill.textContent = val;
        
        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.innerHTML = '&times;';
        removeBtn.className = 'hover:text-red-500 font-bold ml-0.5';
        removeBtn.addEventListener('click', function(e) {
          e.stopPropagation();
          removeValue(val);
        });
        pill.appendChild(removeBtn);
        pillsWrapper.appendChild(pill);

        // Create hidden input for state tracking (and form submission if name is present)
        var input = document.createElement('input');
        input.type = 'hidden';
        if (name) {
          input.name = name;
        }
        input.value = val;
        hiddenContainer.appendChild(input);
      });

      textInput.placeholder = selected.length === 0 ? placeholder : '';
      onChange(selected);
    }

    function addValue(val) {
      if (selected.indexOf(val) === -1) {
        selected.push(val);
        textInput.value = '';
        updatePills();
      }
    }
    container._addValue = addValue;

    function removeValue(val) {
      selected = selected.filter(function(v) { return v !== val; });
      updatePills();
    }

    function showDropdown(filter) {
      var term = (filter || '').toLowerCase();
      // Exclude already selected options
      var filtered = options.filter(function (o) {
        return (selected.indexOf(o) === -1) && (!term || o.toLowerCase().includes(term));
      });

      dropdown.innerHTML = '';

      var clearLi = document.createElement('li');
      clearLi.textContent = noFilterLabel;
      clearLi.className = 'px-3 py-2 text-sm text-brand-dark font-semibold border-b border-gray-100 hover:bg-gray-50 cursor-pointer italic';
      clearLi.style.textTransform = 'uppercase';
      clearLi.addEventListener('mousedown', function (e) {
        e.preventDefault();
        selected = [];
        textInput.value = '';
        updatePills();
        dropdown.style.display = 'none';
        setTimeout(function() { textInput.blur(); }, 0);
      });
      dropdown.appendChild(clearLi);

      filtered.forEach(function (opt) {
        var li = document.createElement('li');
        li.textContent = opt;
        li.className = 'px-3 py-2 text-sm text-gray-800 hover:bg-brand-soft hover:text-brand-dark cursor-pointer';
        li.style.textTransform = 'uppercase';
        li.addEventListener('mousedown', function (e) {
          e.preventDefault();
          addValue(opt);
          dropdown.style.display = 'none';
          setTimeout(function() { textInput.blur(); }, 0);
        });
        dropdown.appendChild(li);
      });

      if (!filtered.length && term) {
        var empty = document.createElement('li');
        empty.textContent = 'Sin resultados';
        empty.className = 'px-3 py-2 text-sm text-gray-400 italic';
        dropdown.appendChild(empty);
      }

      if (dropdown.children.length > 0) {
        dropdown.style.display = 'block';
      } else {
        dropdown.style.display = 'none';
      }
    }

    controlWrapper.addEventListener('click', function() {
      textInput.focus();
    });

    textInput.addEventListener('focus', function () { showDropdown(textInput.value); });
    textInput.addEventListener('input', function () { showDropdown(textInput.value); });

    textInput.addEventListener('blur', function () {
      setTimeout(function () { dropdown.style.display = 'none'; }, 150);
    });

    textInput.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && textInput.value === '' && selected.length > 0) {
        removeValue(selected[selected.length - 1]);
        return;
      }

      var items = dropdown.querySelectorAll('li:not(.italic)');
      var activeEl = dropdown.querySelector('li.bg-brand-soft');
      var idx = Array.from(items).indexOf(activeEl);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (activeEl) activeEl.classList.remove('bg-brand-soft');
        var next = items[idx + 1] || items[0];
        if (next) next.classList.add('bg-brand-soft');
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (activeEl) activeEl.classList.remove('bg-brand-soft');
        var prev = idx > 0 ? items[idx - 1] : items[items.length - 1];
        if (prev) prev.classList.add('bg-brand-soft');
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (activeEl) activeEl.dispatchEvent(new MouseEvent('mousedown'));
      } else if (e.key === 'Escape') {
        dropdown.style.display = 'none';
      }
    });

    function removeAll() {
      selected = [];
      updatePills();
    }
    container._removeAll = removeAll;

    // Initial render
    updatePills();

    container._updateOptions = function(newOptions) {
      options = newOptions;
    };
  }

  var countTimer = null;
  var availableTimer = null;

  function scheduleCount(widget) {
    clearTimeout(countTimer);
    countTimer = setTimeout(function () {
      var areaInputs = widget.querySelectorAll('[data-combobox="area"] input[type=hidden]');
      var locInputs = widget.querySelectorAll('[data-combobox="location"] input[type=hidden]');
      
      var counterEl = widget.querySelector('[data-company-counter]');
      if (!counterEl) return;

      var params = new URLSearchParams();
      areaInputs.forEach(function(input) {
        params.append('area', input.value);
      });
      locInputs.forEach(function(input) {
        params.append('location', input.value);
      });

      var queryString = params.toString();
      var url = COUNT_URL;
      if (queryString) url += '?' + queryString;

      fetch(url)
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (data && typeof data.count === 'number') {
            counterEl.textContent = data.count.toLocaleString('es-ES');
          }
        })
        .catch(function () {});
    }, 250);
  }

  function scheduleAvailableFilters(widget) {
    clearTimeout(availableTimer);
    availableTimer = setTimeout(function () {
      var areaInputs = widget.querySelectorAll('[data-combobox="area"] input[type=hidden]');
      var locInputs = widget.querySelectorAll('[data-combobox="location"] input[type=hidden]');

      var params = new URLSearchParams();
      areaInputs.forEach(function(input) {
        params.append('area', input.value);
      });
      locInputs.forEach(function(input) {
        params.append('location', input.value);
      });

      var queryString = params.toString();
      var url = AVAILABLE_URL;
      if (queryString) url += '?' + queryString;

      fetch(url)
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data || !data.areas || !data.locations) return;

          var areaContainer = widget.querySelector('[data-combobox="area"]');
          var locContainer = widget.querySelector('[data-combobox="location"]');
          if (areaContainer && typeof areaContainer._updateOptions === 'function') {
            areaContainer._updateOptions(data.areas);
          }
          if (locContainer && typeof locContainer._updateOptions === 'function') {
            locContainer._updateOptions(data.locations);
          }

          window.FastJobFilter.optionsData = data;
        })
        .catch(function () {});
    }, 250);
  }

  function initWidgets(widgets, opts) {
    widgets.forEach(function (widget) {
      var areaContainer = widget.querySelector('[data-combobox="area"]');
      var locContainer = widget.querySelector('[data-combobox="location"]');

      function onChange() {
        scheduleCount(widget);
        scheduleAvailableFilters(widget);
      }

      if (areaContainer) {
        initCombobox(areaContainer, opts.areas, onChange);
      }
      if (locContainer) {
        initCombobox(locContainer, opts.locations, onChange);
      }

      scheduleCount(widget);
      scheduleAvailableFilters(widget);
    });
  }

  function renderOptionsError(widgets, onRetry) {
    // On an options-load failure, replace each combobox's contents with a
    // visible, recoverable error instead of leaving silently empty, dead
    // dropdowns. Only innerHTML is cleared — the container's data-* attributes
    // (data-value, data-name, …) are preserved so a retry can re-initialise.
    widgets.forEach(function (widget) {
      widget.querySelectorAll('[data-combobox]').forEach(function (container) {
        container.innerHTML = '';

        var box = document.createElement('div');
        box.className = [
          'w-full border border-red-200 bg-red-50 text-red-700 rounded-xl',
          'px-3 py-2 text-sm flex items-center justify-between gap-2'
        ].join(' ');

        var msg = document.createElement('span');
        msg.textContent = 'No se pudieron cargar las opciones.';
        box.appendChild(msg);

        var retry = document.createElement('button');
        retry.type = 'button';
        retry.textContent = 'Reintentar';
        retry.className = 'font-semibold underline hover:no-underline shrink-0';
        retry.addEventListener('click', onRetry);
        box.appendChild(retry);

        container.appendChild(box);
      });
    });
  }

  // --- Expose public API for search-suggestion.js ---
  var resolveReady = null;
  var _readyResolved = false;

  window.FastJobFilter = {
    get optionsPromise() { return optionsPromise; },
    readyPromise: new Promise(function (resolve) { resolveReady = resolve; }),
    addValue: function (widgetElement, comboboxType, value) {
      var container = widgetElement.querySelector('[data-combobox="' + comboboxType + '"]');
      if (container && typeof container._addValue === 'function') {
        container._addValue(value);
      }
    },
    clearWidget: function (widgetElement) {
      [].forEach.call(widgetElement.querySelectorAll('[data-combobox]'), function (container) {
        if (typeof container._removeAll === 'function') {
          container._removeAll();
        }
      });
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    var widgets = document.querySelectorAll('[data-filter-widget]');
    if (!widgets.length) {
      if (resolveReady) resolveReady();
      return;
    }

    function loadWidgets() {
      fetchOptions()
        .then(function (opts) {
          window.FastJobFilter.optionsData = opts;
          initWidgets(widgets, opts);
          if (!_readyResolved) { _readyResolved = true; resolveReady(); }
        })
        .catch(function () {
          renderOptionsError(widgets, loadWidgets);
          if (!_readyResolved) { _readyResolved = true; resolveReady(); }
        });
    }

    loadWidgets();
  });
})();
