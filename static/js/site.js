document.addEventListener('DOMContentLoaded', () => {
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
});
