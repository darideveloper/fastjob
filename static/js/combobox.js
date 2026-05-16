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
    // data-value is expected to be a comma-separated list of selected names
    var initialValues = container.dataset.value ? container.dataset.value.split(',') : [];
    var selected = initialValues.filter(function(v) { return v.trim().length > 0; });
    var placeholder = container.dataset.placeholder || 'Selecciona opciones…';

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
      'mt-1 max-h-48 overflow-y-auto'
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

      if (selected.length > 0) {
        var clearLi = document.createElement('li');
        clearLi.textContent = '— Limpiar todos —';
        clearLi.className = 'px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 cursor-pointer italic';
        clearLi.addEventListener('mousedown', function (e) {
          e.preventDefault();
          selected = [];
          updatePills();
          dropdown.style.display = 'none';
        });
        dropdown.appendChild(clearLi);
      }

      filtered.forEach(function (opt) {
        var li = document.createElement('li');
        li.textContent = opt;
        li.className = 'px-3 py-2 text-sm text-gray-800 hover:bg-brand-soft hover:text-brand-dark cursor-pointer';
        li.style.textTransform = 'uppercase';
        li.addEventListener('mousedown', function (e) {
          e.preventDefault();
          addValue(opt);
          dropdown.style.display = 'none';
        });
        dropdown.appendChild(li);
      });

      if (!filtered.length && term) {
        var empty = document.createElement('li');
        empty.textContent = 'Sin resultados';
        empty.className = 'px-3 py-2 text-sm text-gray-400 italic';
        dropdown.appendChild(empty);
      } else if (!filtered.length && !term && selected.length === options.length) {
        var allSelected = document.createElement('li');
        allSelected.textContent = 'Todos seleccionados';
        allSelected.className = 'px-3 py-2 text-sm text-gray-400 italic';
        dropdown.appendChild(allSelected);
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

    // Initial render
    updatePills();
  }

  var countTimer = null;

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

      var url = COUNT_URL;
      var queryString = params.toString();
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
