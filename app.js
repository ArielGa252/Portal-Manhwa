let currentManhwa = null;
let currentChapterIndex = 0;

const homePage = document.getElementById("homePage");
const detailsPage = document.getElementById("detailsPage");
const readerPage = document.getElementById("readerPage");

const manhwaGrid = document.getElementById("manhwaGrid");
const searchInput = document.getElementById("searchInput");
const detailsBox = document.getElementById("detailsBox");

const readerTitle = document.getElementById("readerTitle");
const readerImages = document.getElementById("readerImages");
const chapterSelect = document.getElementById("chapterSelect");
const prevChapter = document.getElementById("prevChapter");
const nextChapter = document.getElementById("nextChapter");

const totalCount = document.getElementById("totalCount");
const readCount = document.getElementById("readCount");
const doneCount = document.getElementById("doneCount");

function cleanName(name) {
  return String(name || "")
    .replace("| Blackout Comics", "")
    .replace("Blackout Comics", "")
    .trim();
}

function storageKey(id, field) {
  return `portal_manhwa_${id}_${field}`;
}

function getProgress(id) {
  return {
    read: localStorage.getItem(storageKey(id, "read")) === "1",
    done: localStorage.getItem(storageKey(id, "done")) === "1",
    chapter: localStorage.getItem(storageKey(id, "chapter")) || ""
  };
}

function setProgress(id, field, value) {
  if (field === "read" || field === "done") {
    localStorage.setItem(storageKey(id, field), value ? "1" : "0");
  } else {
    localStorage.setItem(storageKey(id, field), value);
  }
  updateStats();
}

function showPage(page) {
  [homePage, detailsPage, readerPage].forEach(p => p.classList.remove("active"));
  page.classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateStats() {
  const total = MANHWAS.length;
  let read = 0;
  let done = 0;

  MANHWAS.forEach(m => {
    const p = getProgress(m.id);
    if (p.read) read++;
    if (p.done) done++;
  });

  totalCount.textContent = total;
  readCount.textContent = read;
  doneCount.textContent = done;
}

function renderCards(list) {
  manhwaGrid.innerHTML = "";

  if (!list.length) {
    manhwaGrid.innerHTML = `<div class="empty">Nenhum manhwa encontrado.</div>`;
    return;
  }

  list.forEach(manhwa => {
    const progress = getProgress(manhwa.id);
    const card = document.createElement("article");
    card.className = "card";

    card.innerHTML = `
      <div class="cover" data-open="${manhwa.id}">
        ${manhwa.imagem ? `<img src="${manhwa.imagem}" alt="${cleanName(manhwa.nome)}" loading="lazy">` : "Sem capa"}
      </div>

      <div class="cardBody">
        <h3 data-open="${manhwa.id}">${cleanName(manhwa.nome)}</h3>
        <span class="badge">${manhwa.status || "Sem status"}</span>

        <div class="progressBox" onclick="event.stopPropagation()">
          <label>
            <input type="checkbox" ${progress.read ? "checked" : ""} data-progress="read" data-id="${manhwa.id}">
            Lido
          </label>

          <label>
            Capítulo atual:
            <input type="number" min="0" value="${progress.chapter}" placeholder="0" data-progress="chapter" data-id="${manhwa.id}">
          </label>

          <label>
            <input type="checkbox" ${progress.done ? "checked" : ""} data-progress="done" data-id="${manhwa.id}">
            Finalizado
          </label>
        </div>
      </div>
    `;

    card.addEventListener("click", (event) => {
      const openId = event.target?.dataset?.open;
      if (openId) openDetails(Number(openId));
    });

    manhwaGrid.appendChild(card);
  });

  document.querySelectorAll("[data-progress]").forEach(el => {
    el.addEventListener("change", event => {
      const id = event.target.dataset.id;
      const field = event.target.dataset.progress;

      if (field === "chapter") {
        setProgress(id, field, event.target.value);
      } else {
        setProgress(id, field, event.target.checked);
      }
    });
  });
}

function openDetails(id) {
  currentManhwa = MANHWAS.find(item => Number(item.id) === Number(id));
  if (!currentManhwa) return;

  const chapters = currentManhwa.capitulos || [];

  detailsBox.innerHTML = `
    <div class="detailsHeader">
      <div class="detailsCover">
        ${currentManhwa.imagem ? `<img src="${currentManhwa.imagem}" alt="${cleanName(currentManhwa.nome)}">` : `<div class="cover">Sem capa</div>`}
      </div>

      <div class="detailsText">
        <h2>${cleanName(currentManhwa.nome)}</h2>
        <span class="badge">${currentManhwa.status || "Sem status"}</span>
        <p>${currentManhwa.descricao || "Sem descrição cadastrada."}</p>
        <p><strong>${chapters.length}</strong> capítulo(s) disponível(is)</p>
      </div>
    </div>

    <div class="chapters">
      ${chapters.length ? chapters.map((cap, index) => `
        <button class="chapterBtn" onclick="openReader(${index})">
          ${cap.titulo || `Capítulo ${cap.numero}`}
        </button>
      `).join("") : `<div class="empty">Nenhum capítulo cadastrado ainda.</div>`}
    </div>
  `;

  showPage(detailsPage);
}

function openReader(index) {
  currentChapterIndex = index;
  renderReader();
  showPage(readerPage);
}

function renderReader() {
  if (!currentManhwa) return;

  const chapters = currentManhwa.capitulos || [];
  const chapter = chapters[currentChapterIndex];

  if (!chapter) return;

  readerTitle.textContent = `${cleanName(currentManhwa.nome)} - ${chapter.titulo || `Capítulo ${chapter.numero}`}`;

  chapterSelect.innerHTML = chapters.map((cap, index) => `
    <option value="${index}" ${index === currentChapterIndex ? "selected" : ""}>
      ${cap.titulo || `Capítulo ${cap.numero}`}
    </option>
  `).join("");

  const validImages = (chapter.imagens || []).filter(Boolean);

  readerImages.innerHTML = validImages.length
    ? validImages.map((src, i) => `<img src="${src}" alt="Página ${i + 1}" loading="lazy">`).join("")
    : `<div class="empty">Este capítulo ainda não possui imagens cadastradas.</div>`;

  prevChapter.disabled = currentChapterIndex <= 0;
  nextChapter.disabled = currentChapterIndex >= chapters.length - 1;
}

function goHome() {
  currentManhwa = null;
  showPage(homePage);
  renderCards(filterManhwas());
}

function backToDetails() {
  showPage(detailsPage);
}

function filterManhwas() {
  const term = searchInput.value.toLowerCase().trim();

  return MANHWAS.filter(m => {
    return cleanName(m.nome).toLowerCase().includes(term) ||
      String(m.status || "").toLowerCase().includes(term);
  });
}

searchInput.addEventListener("input", () => {
  renderCards(filterManhwas());
});

chapterSelect.addEventListener("change", event => {
  currentChapterIndex = Number(event.target.value);
  renderReader();
});

prevChapter.addEventListener("click", () => {
  if (currentChapterIndex > 0) {
    currentChapterIndex--;
    renderReader();
  }
});

nextChapter.addEventListener("click", () => {
  if (currentManhwa && currentChapterIndex < currentManhwa.capitulos.length - 1) {
    currentChapterIndex++;
    renderReader();
  }
});

updateStats();
renderCards(MANHWAS);
