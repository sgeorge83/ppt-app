import { openBible } from "./engine/bible.js";
import { ENGLISH_BOOK_NAMES, getTheme, PUBLISHER, THEMES } from "./engine/config.js";
import { groupIntoSlides } from "./engine/grouping.js";
import { parseReference } from "./engine/parser.js";
import { TOPICS } from "./engine/topics.js";
import { buildPptx } from "./pptx.js";

const ABOUT = `WordOnAir Slides helps pastors place Scripture on the PowerPoint slides they already use in church.

Type a reference such as John 3:16, search a word, or choose a topic. Each slide can show the World English Bible, the Urdu Geo Version, or both. The wording is copied from those Bibles and is not rewritten.

This is a free Chrome extension from ${PUBLISHER}. There is no account, no advertising, and no collection of personal information. The church name and logo stay in this browser.

How to use it
1. Choose Both, English, or Urdu. Both is the usual choice for a bilingual service.
2. Enter a reference, search a word in either language, or pick a sermon topic.
3. Add the church name, a logo, and one of the four themes if you want them on the slide.
4. Download a PowerPoint file and open it in PowerPoint. To use a presentation you already have, copy these slides into that file.

Scripture
World English Bible is a free public-domain resource.
Urdu Geo Version is a free resource under CC BY-NC-ND 4.0. A slide that includes Urdu credits “Urdu Geo Version · World English Bible”. An English-only slide credits “World English Bible”.
PowerPoint uses Noto Nastaliq Urdu for the Urdu lines when that font is installed.

${PUBLISHER} builds free Scripture tools for phones, desktops, and church slides.
wordonair.com`;

const SETTINGS_KEY = "wordonair-slides";
const DEFAULTS = {
  language: "both",
  keepTogether: false,
  churchName: "",
  theme: "air",
  logoData: "",
};

const status = document.querySelector("#status");
const preview = document.querySelector("#preview");
const referenceInput = document.querySelector("#reference");
const searchInput = document.querySelector("#search");
const searchResults = document.querySelector("#search-results");
const topicList = document.querySelector("#topic-list");
const topicRefs = document.querySelector("#topic-refs");
const churchName = document.querySelector("#church-name");
const keepTogether = document.querySelector("#keep-together");
const logoInput = document.querySelector("#logo");
const logoPreview = document.querySelector("#logo-preview");
const languageButtons = [...document.querySelectorAll("[data-language]")];
const themeRow = document.querySelector(".themes");

let bible = null;
let templateBytes = null;
let activeTab = "reference";
let searchHits = [];
let settings = { ...DEFAULTS };
let saveTimer = 0;

function asset(path) {
  if (globalThis.chrome?.runtime?.getURL) return chrome.runtime.getURL(path);
  return new URL(path, import.meta.url).href;
}

function setStatus(text, kind = "info") {
  status.textContent = text;
  status.className = kind === "info" ? "" : kind;
}

function selectedLanguage() {
  return settings.language === "english" || settings.language === "urdu" ? settings.language : "both";
}

function paintChoices() {
  for (const button of languageButtons) {
    button.setAttribute("aria-pressed", button.dataset.language === selectedLanguage() ? "true" : "false");
  }
  for (const button of themeRow.querySelectorAll("button")) {
    button.setAttribute("aria-pressed", button.dataset.theme === getTheme(settings.theme).id ? "true" : "false");
  }
}

async function loadSettings() {
  try {
    if (globalThis.chrome?.storage?.local) {
      const stored = await chrome.storage.local.get(DEFAULTS);
      return { ...DEFAULTS, ...stored };
    }
    const raw = localStorage.getItem(SETTINGS_KEY);
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
  } catch {
    return { ...DEFAULTS };
  }
}

async function saveSettings() {
  settings = {
    ...settings,
    language: selectedLanguage(),
    keepTogether: keepTogether.checked,
    churchName: churchName.value,
    theme: getTheme(settings.theme).id,
  };
  try {
    if (globalThis.chrome?.storage?.local) await chrome.storage.local.set(settings);
    else localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    const withoutLogo = { ...settings, logoData: "" };
    try {
      if (globalThis.chrome?.storage?.local) await chrome.storage.local.set(withoutLogo);
      else localStorage.setItem(SETTINGS_KEY, JSON.stringify(withoutLogo));
      setStatus("The logo will be used for this download. It is too large to remember next time.", "error");
    } catch {
      setStatus("The church settings could not be remembered in this browser.", "error");
    }
  }
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => { saveSettings(); }, 250);
}

function showTab(name) {
  activeTab = name;
  for (const button of document.querySelectorAll(".tab")) {
    const selected = button.dataset.tab === name;
    button.setAttribute("aria-selected", selected ? "true" : "false");
  }
  for (const panel of document.querySelectorAll(".panel")) {
    panel.hidden = panel.dataset.panel !== name;
  }
}

function selectedValues(list) {
  return [...list.selectedOptions].map((option) => Number(option.value));
}

function specsFromUi() {
  if (activeTab === "reference") return parseReference(referenceInput.value);
  if (activeTab === "search") {
    const chosen = selectedValues(searchResults);
    if (!chosen.length) throw new Error("Select one or more search results.");
    return chosen.map((index) => {
      const hit = searchHits[index];
      return {
        bookId: hit.bookId,
        bookName: ENGLISH_BOOK_NAMES[hit.bookId] || "Verse",
        chapter: hit.chapter,
        verseStart: hit.verse,
        verseEnd: hit.verse,
        label: hit.reference,
      };
    });
  }
  if (activeTab === "topics") {
    const topicIndex = topicList.selectedIndex;
    if (topicIndex < 0) throw new Error("Choose a topic.");
    const references = TOPICS[topicIndex].references;
    const chosen = selectedValues(topicRefs);
    const picked = chosen.length ? chosen.map((index) => references[index]) : references;
    return parseReference(picked.join("; "));
  }
  throw new Error("Open Reference, Search, or Topics, then create the slides.");
}

function showPreview(slides) {
  preview.replaceChildren();
  if (!slides.length) {
    preview.textContent = "No verse text is available in that language.";
    return;
  }
  for (const slide of slides) {
    const article = document.createElement("article");
    const heading = document.createElement("h3");
    heading.textContent = slide.reference;
    article.append(heading);
    if (slide.urdu) {
      const urdu = document.createElement("p");
      urdu.className = "urdu";
      urdu.dir = "rtl";
      urdu.lang = "ur";
      urdu.textContent = slide.urdu;
      article.append(urdu);
    }
    if (slide.english) {
      const english = document.createElement("p");
      english.textContent = slide.english;
      article.append(english);
    }
    if (slide.attribution) {
      const credit = document.createElement("p");
      credit.className = "credit";
      credit.textContent = slide.attribution;
      article.append(credit);
    }
    preview.append(article);
  }
}

function currentSlides() {
  const verses = bible.resolve(specsFromUi());
  const slides = groupIntoSlides(verses, selectedLanguage(), keepTogether.checked);
  if (!slides.length) throw new Error("No verse text is available in that language.");
  return { verses, slides };
}

function dataUrlParts(dataUrl) {
  const match = /^data:([^;,]+);base64,([\s\S]+)$/.exec(dataUrl || "");
  if (!match) return null;
  const binary = atob(match[2]);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  const mime = match[1].toLowerCase();
  const ext = mime.includes("png") ? "png" : "jpeg";
  return { bytes, ext, mime };
}

async function logoForSlide() {
  const parts = dataUrlParts(settings.logoData);
  if (!parts) return null;
  const blob = new Blob([parts.bytes], { type: parts.mime });
  const bitmap = await createImageBitmap(blob);
  const logo = { ...parts, width: bitmap.width, height: bitmap.height };
  bitmap.close();
  if (!logo.width || !logo.height) return null;
  return logo;
}

function download(bytes) {
  const blob = new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "WordOnAir-Slides.pptx";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function fillTopics(index) {
  topicRefs.replaceChildren();
  const topic = TOPICS[index];
  if (!topic) return;
  topic.references.forEach((reference, referenceIndex) => {
    const option = document.createElement("option");
    option.value = String(referenceIndex);
    option.textContent = reference;
    topicRefs.append(option);
  });
}

async function onSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    setStatus("Enter a word to search.", "error");
    return;
  }
  if (!bible) return;
  setStatus("Searching the Bible text…");
  await new Promise((resolve) => setTimeout(resolve, 0));
  try {
    const { hits, total, empty } = bible.search(query);
    searchHits = hits;
    searchResults.replaceChildren();
    if (empty) {
      setStatus("Enter a word with letters. Small words such as “the” are skipped.", "error");
      return;
    }
    hits.forEach((hit, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = `${hit.reference}  —  ${hit.preview}`;
      searchResults.append(option);
    });
    const extra = total > hits.length ? ` Showing ${hits.length}.` : "";
    setStatus(`${total} verses contain that word.${extra}`, "ok");
  } catch (error) {
    setStatus(error.message || "The search could not be finished.", "error");
  }
}

async function onPreview() {
  try {
    const { verses, slides } = currentSlides();
    showPreview(slides);
    const count = verses.length;
    setStatus(`Preview ready. ${count} verse${count === 1 ? "" : "s"}.`, "ok");
  } catch (error) {
    setStatus(error.message || "The preview could not be made.", "error");
  }
}

async function onDownload() {
  try {
    if (!templateBytes) throw new Error("The PowerPoint template is not in this copy.");
    const { verses, slides } = currentSlides();
    const logo = await logoForSlide();
    const bytes = buildPptx(templateBytes, slides, {
      themeId: settings.theme,
      churchName: churchName.value,
      logo,
    });
    showPreview(slides);
    download(bytes);
    await saveSettings();
    const count = verses.length;
    setStatus(`Downloaded WordOnAir-Slides.pptx. ${count} verse${count === 1 ? "" : "s"}.`, "ok");
  } catch (error) {
    setStatus(error.message || "The PowerPoint file could not be made.", "error");
  }
}

function readLogo(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    settings.logoData = String(reader.result || "");
    logoPreview.src = settings.logoData;
    logoPreview.hidden = !settings.logoData;
    saveSettings();
  };
  reader.readAsDataURL(file);
}

document.querySelector("#about").textContent = ABOUT;
TOPICS.forEach((topic, index) => {
  const option = document.createElement("option");
  option.value = String(index);
  option.textContent = topic.label;
  topicList.append(option);
});
topicList.selectedIndex = 0;
fillTopics(0);

for (const theme of THEMES) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.theme = theme.id;
  button.textContent = theme.name;
  button.addEventListener("click", () => {
    settings.theme = theme.id;
    paintChoices();
    scheduleSave();
  });
  themeRow.append(button);
}

for (const button of document.querySelectorAll(".tab")) {
  button.addEventListener("click", () => showTab(button.dataset.tab));
}
for (const button of languageButtons) {
  button.addEventListener("click", () => {
    settings.language = button.dataset.language;
    paintChoices();
    scheduleSave();
  });
}

topicList.addEventListener("change", () => fillTopics(topicList.selectedIndex));
keepTogether.addEventListener("change", scheduleSave);
churchName.addEventListener("input", scheduleSave);
searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") onSearch();
});
referenceInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") onPreview();
});
document.querySelector("#search-button").addEventListener("click", onSearch);
document.querySelector("#preview-button").addEventListener("click", onPreview);
document.querySelector("#download-button").addEventListener("click", onDownload);
document.querySelector("#clear-logo").addEventListener("click", () => {
  settings.logoData = "";
  logoInput.value = "";
  logoPreview.hidden = true;
  logoPreview.removeAttribute("src");
  saveSettings();
});
logoInput.addEventListener("change", () => readLogo(logoInput.files?.[0]));

const loaded = await loadSettings();
settings = loaded;
churchName.value = settings.churchName || "";
keepTogether.checked = Boolean(settings.keepTogether);
if (settings.logoData) {
  logoPreview.src = settings.logoData;
  logoPreview.hidden = false;
}
paintChoices();

try {
  const [bibleResponse, templateResponse] = await Promise.all([
    fetch(asset("data/bible.json")),
    fetch(asset("blank.pptx")),
  ]);
  if (!bibleResponse.ok || !templateResponse.ok) {
    throw new Error("Bible text is not in this copy yet. The Chrome package is built with python packaging/build_chrome.py.");
  }
  bible = openBible(await bibleResponse.json());
  templateBytes = new Uint8Array(await templateResponse.arrayBuffer());
  setStatus("Choose Both, English, or Urdu, then enter a reference.");
} catch (error) {
  setStatus(error.message || "The Bible text could not be loaded.", "error");
}
