(function () {
  'use strict';

  var OPTIONS_URL = '/api/companies/filter-options/';
  var COUNT_URL = '/api/companies/count/';

  var optionsPromise = null;

  function fetchOptions() {
    if (!optionsPromise) {
      optionsPromise = fetch(OPTIONS_URL)
        .then(function (r) { return r.json(); })
        .catch(function () { return { areas: [], locations: [] }; });
    }
    return optionsPromise;
  }

  function initCombobox(container, options, onChange) {
    var name = container.dataset.name;
    var currentValue = container.dataset.value || '';
    var placeholder = container.dataset.placeholder || 'Selecciona una opción…';

    container.style.position = 'relative';
    container.innerHTML = '';

    var hidden = document.createElement('input');
    hidden.type = name ? 'hidden' : 'hidden';
    if (name) hidden.name = name;
    hidden.value = currentValue;
    container.appendChild(hidden);

    var textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.value = currentValue;
    textInput.placeholder = placeholder;
    textInput.autocomplete = 'off';
    textInput.className = [
      'w-full border border-gray-200 rounded-xl px-3 py-2 text-sm',
      'focus:outline-none focus:ring-2 focus:ring-brand-ring bg-white'
    ].join(' ');
    container.appendChild(textInput);

    var dropdown = document.createElement('ul');
    dropdown.className = [
      'absolute z-20 w-full bg-white border border-gray-200 rounded-xl shadow-lg',
      'mt-1 max-h-48 overflow-y-auto'
    ].join(' ');
    dropdown.style.display = 'none';
    container.appendChild(dropdown);

    function showDropdown(filter) {
      var term = (filter || '').toLowerCase();
      var filtered = options.filter(function (o) {
        return !term || o.toLowerCase().includes(term);
      });

      dropdown.innerHTML = '';

      if (hidden.value) {
        var clearLi = document.createElement('li');
        clearLi.textContent = '— Sin filtro —';
        clearLi.className = 'px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 cursor-pointer italic';
        clearLi.addEventListener('mousedown', function (e) {
          e.preventDefault();
          hidden.value = '';
          textInput.value = '';
          dropdown.style.display = 'none';
          onChange('');
        });
        dropdown.appendChild(clearLi);
      }

      filtered.forEach(function (opt) {
        var li = document.createElement('li');
        li.textContent = opt;
        li.className = 'px-3 py-2 text-sm text-gray-800 hover:bg-brand-soft hover:text-brand-dark cursor-pointer';
        li.addEventListener('mousedown', function (e) {
          e.preventDefault();
          hidden.value = opt;
          textInput.value = opt;
          dropdown.style.display = 'none';
          onChange(opt);
        });
        dropdown.appendChild(li);
      });

      if (!filtered.length) {
        var empty = document.createElement('li');
        empty.textContent = 'Sin resultados';
        empty.className = 'px-3 py-2 text-sm text-gray-400 italic';
        dropdown.appendChild(empty);
      }

      dropdown.style.display = 'block';
    }

    textInput.addEventListener('focus', function () { showDropdown(textInput.value); });
    textInput.addEventListener('input', function () { showDropdown(textInput.value); });

    textInput.addEventListener('blur', function () {
      setTimeout(function () { dropdown.style.display = 'none'; }, 150);
      if (!textInput.value.trim() && hidden.value) {
        hidden.value = '';
        onChange('');
      }
    });

    textInput.addEventListener('keydown', function (e) {
      var items = dropdown.querySelectorAll('li');
      var activeEl = dropdown.querySelector('li.bg-brand-muted');
      var idx = Array.from(items).indexOf(activeEl);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (activeEl) activeEl.classList.remove('bg-brand-muted');
        var next = items[idx + 1] || items[0];
        if (next) next.classList.add('bg-brand-muted');
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (activeEl) activeEl.classList.remove('bg-brand-muted');
        var prev = idx > 0 ? items[idx - 1] : items[items.length - 1];
        if (prev) prev.classList.add('bg-brand-muted');
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (activeEl) activeEl.dispatchEvent(new MouseEvent('mousedown'));
      } else if (e.key === 'Escape') {
        dropdown.style.display = 'none';
      }
    });
  }

  var countTimer = null;

  function scheduleCount(widget) {
    clearTimeout(countTimer);
    countTimer = setTimeout(function () {
      var areaEl = widget.querySelector('[data-combobox="area"] input[type=hidden]');
      var locEl = widget.querySelector('[data-combobox="location"] input[type=hidden]');
      var counterEl = widget.querySelector('[data-company-counter]');
      if (!counterEl) return;

      var params = new URLSearchParams();
      if (areaEl && areaEl.value) params.set('area', areaEl.value);
      if (locEl && locEl.value) params.set('location', locEl.value);

      fetch(COUNT_URL + (params.toString() ? '?' + params : ''))
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (data && typeof data.count === 'number') {
            counterEl.textContent = data.count.toLocaleString('es-ES');
          }
        })
        .catch(function () {});
    }, 250);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var widgets = document.querySelectorAll('[data-filter-widget]');
    if (!widgets.length) return;

    fetchOptions().then(function (opts) {
      widgets.forEach(function (widget) {
        var areaContainer = widget.querySelector('[data-combobox="area"]');
        var locContainer = widget.querySelector('[data-combobox="location"]');

        if (areaContainer) {
          initCombobox(areaContainer, opts.areas, function () { scheduleCount(widget); });
        }
        if (locContainer) {
          initCombobox(locContainer, opts.locations, function () { scheduleCount(widget); });
        }

        scheduleCount(widget);
      });
    });
  });
})();
