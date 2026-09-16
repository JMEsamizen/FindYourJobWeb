document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-password-toggle]').forEach((toggle) => {
    const field = toggle.closest('.password-field')?.querySelector('input');
    if (!field) return;
    toggle.addEventListener('click', () => {
      const show = field.type === 'password';
      field.type = show ? 'text' : 'password';
      toggle.textContent = show ? 'Hide' : 'Show';
      toggle.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  });
  document.querySelectorAll('form[data-loading]').forEach((form) => form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.dataset.original = button.textContent; button.textContent = 'Loading...'; }
  }));
  document.querySelectorAll('[data-chips-target]').forEach((group) => {
    const target = document.querySelector(group.dataset.chipsTarget);
    const values = new Set((target.value || '').split(',').map((item) => item.trim()).filter(Boolean));
    group.querySelectorAll('[data-chip]').forEach((chip) => {
      chip.classList.toggle('active', values.has(chip.dataset.chip));
      chip.addEventListener('click', () => {
        values.has(chip.dataset.chip) ? values.delete(chip.dataset.chip) : values.add(chip.dataset.chip);
        target.value = [...values].join(', '); chip.classList.toggle('active');
      });
    });
  });
  const filterPanel = document.querySelector('[data-filter-panel]');
  const filterToggle = document.querySelector('[data-filter-toggle]');
  const filterClose = document.querySelector('[data-filter-close]');
  const setFiltersOpen = (open) => {
    if (!filterPanel || !filterToggle) return;
    filterPanel.classList.toggle('is-open', open);
    filterPanel.setAttribute('aria-hidden', String(!open));
    filterToggle.setAttribute('aria-expanded', String(open));
    filterToggle.classList.toggle('is-active', open);
  };
  filterToggle?.addEventListener('click', () => setFiltersOpen(!filterPanel.classList.contains('is-open')));
  filterClose?.addEventListener('click', () => setFiltersOpen(false));
  filterPanel?.addEventListener('click', (event) => { if (event.target === filterPanel) setFiltersOpen(false); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') setFiltersOpen(false); });
});
