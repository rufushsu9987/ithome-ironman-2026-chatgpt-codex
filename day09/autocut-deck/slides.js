const slides = [...document.querySelectorAll('.slide')];
const progressBar = document.querySelector('#progressBar');
const pageCounter = document.querySelector('#pageCounter');
const notesPanel = document.querySelector('#notesPanel');
const notesContent = document.querySelector('#notesContent');
const videoMode = new URLSearchParams(location.search).get('render') === 'video';
if (videoMode) document.documentElement.classList.add('render-video');

let current = clamp(Number.parseInt(location.hash.slice(1), 10) - 1 || 0, 0, slides.length - 1);
function clamp(value, min, max) { return Math.min(Math.max(value, min), max); }
function scaleDeck() {
  const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
  document.documentElement.style.setProperty('--deck-scale', String(scale));
}
function render({ updateHash = true } = {}) {
  slides.forEach((slide, index) => {
    const active = index === current;
    slide.classList.toggle('is-active', active);
    slide.setAttribute('aria-hidden', active ? 'false' : 'true');
  });
  const page = current + 1;
  progressBar.style.width = `${(page / slides.length) * 100}%`;
  pageCounter.textContent = `${page} / ${slides.length}`;
  document.title = `${slides[current].dataset.title || `Slide ${page}`} — Day 9｜Learning Pack 與證據回流`;
  const notes = slides[current].querySelector('.notes')?.textContent.trim() || 'No speaker notes.';
  notesContent.textContent = notes;
  if (updateHash) history.replaceState(null, '', `#${page}`);
}
function goTo(index) { current = clamp(index, 0, slides.length - 1); render(); }
function toggleNotes(force) { notesPanel.hidden = !(force ?? notesPanel.hidden); }
window.addEventListener('resize', scaleDeck);
window.addEventListener('hashchange', () => {
  const requested = Number.parseInt(location.hash.slice(1), 10) - 1;
  if (Number.isFinite(requested)) { current = clamp(requested, 0, slides.length - 1); render({ updateHash: false }); }
});
document.addEventListener('keydown', (event) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
  if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(event.key)) { event.preventDefault(); goTo(current + 1); }
  else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(event.key)) { event.preventDefault(); goTo(current - 1); }
  else if (event.key === 'Home') { event.preventDefault(); goTo(0); }
  else if (event.key === 'End') { event.preventDefault(); goTo(slides.length - 1); }
  else if (event.key.toLowerCase() === 'n') { event.preventDefault(); toggleNotes(); }
  else if (event.key === 'Escape') toggleNotes(false);
});
document.querySelector('#prevButton').addEventListener('click', () => goTo(current - 1));
document.querySelector('#nextButton').addEventListener('click', () => goTo(current + 1));
document.querySelector('#notesButton').addEventListener('click', () => toggleNotes());
document.querySelector('#closeNotes').addEventListener('click', () => toggleNotes(false));
scaleDeck();
render();
