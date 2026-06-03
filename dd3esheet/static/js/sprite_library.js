(function () {
  const root = document.querySelector('[data-screen-label="sprite-library"]');
  if (!root) return;

  const search = root.querySelector('#sl-search');
  const gallery = root.querySelector('#sl-gallery');
  const count = root.querySelector('#sl-count');
  const crumb = root.querySelector('#sl-crumb');
  const empty = root.querySelector('#sl-empty');
  const sidebar = root.querySelector('#sl-sidebar');
  const menuButton = root.querySelector('#sl-menu-btn');
  const scrim = root.querySelector('#sl-scrim');
  const drawer = root.querySelector('#sl-drawer');
  const drawerClose = root.querySelector('#sl-drawer-close');
  const cards = Array.from(root.querySelectorAll('.sl-card'));
  const groups = Array.from(root.querySelectorAll('.sl-group'));
  const groupButtons = Array.from(root.querySelectorAll('[data-group].sl-nav-item'));
  const typeChips = Array.from(root.querySelectorAll('[data-type].sl-chip'));
  const footprintChips = Array.from(root.querySelectorAll('[data-footprint].sl-chip'));
  const densityButtons = Array.from(root.querySelectorAll('[data-density]'));
  const manifestTotal = Number(count.textContent.match(/\d+\s+no manifesto/)?.[0].match(/\d+/)?.[0] || cards.length);

  const state = {
    search: '',
    group: 'all',
    types: new Set(),
    footprints: new Set(),
  };

  function matches(card) {
    if (state.group !== 'all' && card.dataset.group !== state.group) return false;
    if (state.types.size && !state.types.has(card.dataset.type)) return false;
    if (state.footprints.size && !state.footprints.has(card.dataset.footprint)) return false;
    if (state.search) {
      return (card.dataset.search || '').toLowerCase().includes(state.search);
    }
    return true;
  }

  function selectedGroupLabel() {
    if (state.group === 'all') return 'Todos os Sprites';
    const button = groupButtons.find(item => item.dataset.group === state.group);
    return button ? button.querySelector('.sl-nav-label').textContent : 'Sprites';
  }

  function renderFilters() {
    let shown = 0;

    groups.forEach(group => {
      let groupShown = 0;
      group.querySelectorAll('.sl-card').forEach(card => {
        const visible = matches(card);
        card.hidden = !visible;
        if (visible) groupShown += 1;
      });
      group.hidden = groupShown === 0;
      const visibleCount = group.querySelector('.sl-group-visible-count');
      if (visibleCount) visibleCount.textContent = String(groupShown);
      shown += groupShown;
    });

    groupButtons.forEach(button => {
      button.classList.toggle('is-active', button.dataset.group === state.group);
    });
    typeChips.forEach(chip => {
      chip.classList.toggle('is-active', state.types.has(chip.dataset.type));
    });
    footprintChips.forEach(chip => {
      chip.classList.toggle('is-active', state.footprints.has(chip.dataset.footprint));
    });

    crumb.textContent = selectedGroupLabel();
    count.textContent = `${shown} visiveis - ${manifestTotal} no manifesto`;
    empty.hidden = shown !== 0;
  }

  function closeSidebar() {
    sidebar.classList.remove('is-visible');
    if (!drawer.classList.contains('is-visible')) {
      scrim.classList.remove('is-visible');
      scrim.hidden = true;
    }
  }

  function closeDrawer() {
    drawer.classList.remove('is-visible');
    drawer.setAttribute('aria-hidden', 'true');
    if (!sidebar.classList.contains('is-visible')) {
      scrim.classList.remove('is-visible');
      scrim.hidden = true;
    }
  }

  function showScrim() {
    scrim.hidden = false;
    requestAnimationFrame(() => scrim.classList.add('is-visible'));
  }

  function detailPrompt(card) {
    const parts = [
      'Warm parchment storybook style, hand-inked classic fantasy tabletop RPG sourcebook art.',
      '',
      `SUBJECT: ${card.dataset.desc}.`,
      '',
      `FORMAT (${card.dataset.typeLabel}): ${card.dataset.canvas} px, ${card.dataset.alpha}.`,
    ];
    if (card.dataset.footprint) {
      parts.push(`Footprint metadata: ${card.dataset.footprint} cells.`);
    }
    parts.push('');
    parts.push('Palette: dark ink, parchment, ochre, leather, forest green, iron, deep red, steel blue, muted gold, arcane teal, royal blue, dull violet.');
    parts.push('');
    parts.push('No text, labels, UI, frame, watermark, grid lines, token ring, base disc, health bar, or selection mark.');
    return parts.join('\n');
  }

  function setText(selector, value) {
    const node = root.querySelector(selector);
    if (node) node.textContent = value || '';
  }

  function openDrawer(card) {
    const slot = card.querySelector('.sl-slot').cloneNode(true);
    const preview = root.querySelector('#sl-drawer-preview');
    preview.innerHTML = '';
    const holder = document.createElement('div');
    holder.className = 'sl-card';
    holder.appendChild(slot);
    preview.appendChild(holder);

    drawer.style.setProperty('--accent', getComputedStyle(card).getPropertyValue('--accent'));
    drawer.dataset.id = card.dataset.id;
    drawer.dataset.prompt = detailPrompt(card);

    setText('#sl-drawer-type', card.dataset.typeLabel);
    setText('#sl-drawer-title', card.dataset.id);
    setText('#sl-spec-type', card.dataset.typeLabel);
    setText('#sl-spec-canvas', card.dataset.canvas);
    setText('#sl-spec-alpha', card.dataset.alpha || card.dataset.format);
    setText('#sl-spec-footprint', card.dataset.footprint || card.dataset.grid);
    setText('#sl-spec-group', card.dataset.groupLabel);
    setText('#sl-drawer-desc', card.dataset.desc);
    setText('#sl-drawer-prompt', drawer.dataset.prompt);

    const sizeRow = root.querySelector('#sl-spec-size-row');
    if (card.dataset.size) {
      setText('#sl-spec-size', card.dataset.size);
      sizeRow.hidden = false;
    } else {
      sizeRow.hidden = true;
    }

    showScrim();
    drawer.classList.add('is-visible');
    drawer.setAttribute('aria-hidden', 'false');
  }

  function copyText(text, button, label) {
    function done() {
      button.classList.add('is-copied');
      button.textContent = 'Copiado';
      setTimeout(() => {
        button.classList.remove('is-copied');
        button.textContent = label;
      }, 1300);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(fallback);
    } else {
      fallback();
    }
    function fallback() {
      const input = document.createElement('textarea');
      input.value = text;
      document.body.appendChild(input);
      input.select();
      try {
        document.execCommand('copy');
      } catch (error) {
        /* Clipboard fallback can fail silently in older browsers. */
      }
      input.remove();
      done();
    }
  }

  search.addEventListener('input', event => {
    state.search = event.target.value.trim().toLowerCase();
    renderFilters();
  });

  groupButtons.forEach(button => {
    button.addEventListener('click', () => {
      state.group = button.dataset.group;
      renderFilters();
      gallery.scrollTop = 0;
      closeSidebar();
    });
  });

  typeChips.forEach(chip => {
    chip.addEventListener('click', () => {
      state.types.has(chip.dataset.type) ? state.types.delete(chip.dataset.type) : state.types.add(chip.dataset.type);
      renderFilters();
    });
  });

  footprintChips.forEach(chip => {
    chip.addEventListener('click', () => {
      state.footprints.has(chip.dataset.footprint) ? state.footprints.delete(chip.dataset.footprint) : state.footprints.add(chip.dataset.footprint);
      renderFilters();
    });
  });

  densityButtons.forEach(button => {
    button.addEventListener('click', () => {
      const dense = button.dataset.density === 'dense';
      root.classList.toggle('is-dense', dense);
      densityButtons.forEach(item => item.classList.toggle('is-active', item === button));
    });
  });

  cards.forEach(card => card.addEventListener('click', () => openDrawer(card)));

  menuButton.addEventListener('click', () => {
    sidebar.classList.add('is-visible');
    showScrim();
  });

  scrim.addEventListener('click', () => {
    closeDrawer();
    closeSidebar();
  });
  drawerClose.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      closeDrawer();
      closeSidebar();
    }
  });

  root.querySelector('#sl-copy-id').addEventListener('click', event => {
    copyText(drawer.dataset.id || '', event.currentTarget, 'Copiar id');
  });
  root.querySelector('#sl-copy-prompt').addEventListener('click', event => {
    copyText(drawer.dataset.prompt || '', event.currentTarget, 'Copiar prompt');
  });

  renderFilters();
})();
