const search=document.querySelector('#search'),kind=document.querySelector('#kind'),cards=[...document.querySelectorAll('[data-search]')],count=document.querySelector('#matches'),empty=document.querySelector('#empty');function filter(){let n=0;for(const card of cards){const show=(!kind.value||card.dataset.kind===kind.value)&&card.dataset.search.toLocaleLowerCase().includes(search.value.trim().toLocaleLowerCase());card.hidden=!show;n+=show}count.textContent=n+' 项';empty.hidden=n!==0}if(search&&kind){search.addEventListener('input',filter);kind.addEventListener('change',filter);filter()}

// Native buttons keep the curated index usable with keyboard and touch.
const collectionButtons = [...document.querySelectorAll('[data-collection-filter]')];
const collectionNotes = [...document.querySelectorAll('[data-collection]')];
const collectionCount = document.querySelector('.collection-count');
for (const button of collectionButtons) {
  button.addEventListener('click', () => {
    const selection = button.dataset.collectionFilter;
    for (const item of collectionButtons) item.setAttribute('aria-pressed', String(item === button));
    let visible = 0;
    for (const note of collectionNotes) {
      note.hidden = selection !== 'all' && note.dataset.collection !== selection;
      if (!note.hidden) visible++;
    }
    if (collectionCount) collectionCount.textContent = `精选 ${visible} 页`;
  });
}
