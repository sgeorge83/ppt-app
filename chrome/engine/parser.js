/** Bible reference parser. Kept in step with slides/parser.py. */

import { ENGLISH_BOOK_NAMES, EXTRA_ALIASES, SINGLE_CHAPTER_BOOK_IDS } from "./config.js";

let dynamicAliases = [];
let lookup = [];

function rebuildLookup() {
  const seen = new Set();
  const entries = [];

  function add(bookId, pattern) {
    const trimmed = pattern.trim();
    const key = trimmed.toLowerCase();
    if (!trimmed || seen.has(key)) return;
    seen.add(key);
    entries.push({ bookId, pattern: trimmed });
  }

  for (const [bookId, name] of Object.entries(ENGLISH_BOOK_NAMES)) add(Number(bookId), name);
  for (const [bookId, patterns] of Object.entries(EXTRA_ALIASES)) {
    for (const pattern of patterns) add(Number(bookId), pattern);
  }
  for (const [bookId, pattern] of dynamicAliases) add(bookId, pattern);

  entries.sort((left, right) => right.pattern.length - left.pattern.length || left.bookId - right.bookId);
  lookup = entries;
}

export function registerBookAliases(entries) {
  dynamicAliases = entries.map(([bookId, pattern]) => [bookId, pattern]);
  rebuildLookup();
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function normalizeReferenceInput(value) {
  let text = value.replaceAll("–", "-").replaceAll("—", "-");
  text = text.replace(/\b1st\b/gi, "1");
  text = text.replace(/\b2nd\b/gi, "2");
  text = text.replace(/\b3rd\b/gi, "3");
  text = text.replace(/\bfirst\b/gi, "1");
  text = text.replace(/\bsecond\b/gi, "2");
  text = text.replace(/\bthird\b/gi, "3");
  text = text.replace(/(^|;|\band\b)\s*III\b/gi, "$1 3");
  text = text.replace(/(^|;|\band\b)\s*II\b/gi, "$1 2");
  text = text.replace(/(^|;|\band\b)\s*I\b/gi, "$1 1");
  text = text.replace(/([^\W\d_])\./gu, "$1");
  return text.replace(/\s+/g, " ").trim();
}

function matchBook(segment) {
  const trimmed = segment.trim();
  for (const entry of lookup) {
    const matcher = new RegExp(`^${escapeRegExp(entry.pattern)}(?:\\s+|$)(.*)$`, "i");
    const match = matcher.exec(trimmed);
    if (!match) continue;
    const bookName = ENGLISH_BOOK_NAMES[entry.bookId] || entry.pattern;
    return { bookId: entry.bookId, bookName, rest: (match[1] || "").trim() };
  }
  return null;
}

function wholeChapter(bookId, bookName, chapter) {
  return { bookId, bookName, chapter, verseStart: 1, verseEnd: null, label: `${bookName} ${chapter}` };
}

function verseSpec(bookId, bookName, chapter, start, end) {
  const label = start === end ? `${bookName} ${chapter}:${start}` : `${bookName} ${chapter}:${start}-${end}`;
  return { bookId, bookName, chapter, verseStart: start, verseEnd: end, label };
}

function parseVerseList(bookId, bookName, chapter, verseList) {
  const parts = verseList.split(",").map((part) => part.trim()).filter(Boolean);
  if (!parts.length) throw new Error(`Could not read ${bookName} ${chapter}.`);
  const specs = [];
  for (const part of parts) {
    const range = /^(\d+)\s*-\s*(\d+)$/.exec(part);
    const single = range ? null : /^(\d+)$/.exec(part);
    if (!range && !single) throw new Error(`Could not read ${bookName} ${chapter}:${verseList}.`);
    const start = Number((range || single)[1]);
    const end = range ? Number(range[2]) : start;
    if (start < 1 || end < start) throw new Error(`The verse range ${part} is not valid.`);
    specs.push(verseSpec(bookId, bookName, chapter, start, end));
  }
  return specs;
}

function parseRest(bookId, bookName, rest) {
  const single = SINGLE_CHAPTER_BOOK_IDS.has(bookId);
  if (!rest) {
    if (!single) throw new Error(`Add a chapter, for example ${bookName} 1.`);
    return [{ bookId, bookName, chapter: 1, verseStart: 1, verseEnd: null, label: bookName }];
  }

  let match = /^(\d+):(\d+)\s*-\s*(\d+):(\d+)$/.exec(rest);
  if (match) {
    const startChapter = Number(match[1]);
    const startVerse = Number(match[2]);
    const endChapter = Number(match[3]);
    const endVerse = Number(match[4]);
    if (endChapter < startChapter || startVerse < 1 || endVerse < 1) {
      throw new Error("That reference range is not valid.");
    }
    if (startChapter === endChapter) return [verseSpec(bookId, bookName, startChapter, startVerse, endVerse)];
    const specs = [{
      bookId,
      bookName,
      chapter: startChapter,
      verseStart: startVerse,
      verseEnd: null,
      label: `${bookName} ${startChapter}:${startVerse}-`,
    }];
    for (let chapter = startChapter + 1; chapter < endChapter; chapter += 1) {
      specs.push(wholeChapter(bookId, bookName, chapter));
    }
    specs.push(verseSpec(bookId, bookName, endChapter, 1, endVerse));
    return specs;
  }

  match = /^(\d+)\s*-\s*(\d+):(\d+)$/.exec(rest);
  if (match && !single) {
    const startChapter = Number(match[1]);
    const endChapter = Number(match[2]);
    const endVerse = Number(match[3]);
    if (endChapter < startChapter) throw new Error("That chapter range is reversed.");
    const specs = [];
    for (let chapter = startChapter; chapter < endChapter; chapter += 1) {
      specs.push(wholeChapter(bookId, bookName, chapter));
    }
    specs.push(verseSpec(bookId, bookName, endChapter, 1, endVerse));
    return specs;
  }

  match = /^(\d+):(.+)$/.exec(rest);
  if (match) return parseVerseList(bookId, bookName, Number(match[1]), match[2]);

  match = /^(\d+)\s*-\s*(\d+)$/.exec(rest);
  if (match) {
    const start = Number(match[1]);
    const end = Number(match[2]);
    if (end < start) throw new Error("That range is reversed.");
    if (single) return [verseSpec(bookId, bookName, 1, start, end)];
    const specs = [];
    for (let chapter = start; chapter <= end; chapter += 1) specs.push(wholeChapter(bookId, bookName, chapter));
    return specs;
  }

  match = /^(\d+)$/.exec(rest);
  if (match) {
    const number = Number(match[1]);
    if (number < 1) throw new Error("Chapter and verse numbers start at 1.");
    if (single) return [verseSpec(bookId, bookName, 1, number, number)];
    return [wholeChapter(bookId, bookName, number)];
  }

  throw new Error(`Could not read ${bookName} ${rest}.`);
}

export function parseReference(reference) {
  if (!reference || !reference.trim()) throw new Error("Enter a reference such as John 3:16.");
  const segments = normalizeReferenceInput(reference)
    .split(/\s*;\s*|\s+\band\b\s+/i)
    .map((part) => part.trim())
    .filter(Boolean);
  if (!segments.length) throw new Error("Enter a reference such as John 3:16.");
  const specs = [];
  for (const segment of segments) {
    const matched = matchBook(segment);
    if (!matched) {
      if (/[\u0600-\u06FF]/.test(segment)) {
        throw new Error("No Urdu book name matched. Install the bundled Bible text, then try the reference again.");
      }
      throw new Error(`No Bible book found in "${segment}".`);
    }
    specs.push(...parseRest(matched.bookId, matched.bookName, matched.rest));
  }
  return specs;
}

rebuildLookup();
