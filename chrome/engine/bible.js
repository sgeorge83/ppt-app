/** Load both Bibles and search them. The wording is copied, not rewritten. */

import { ENGLISH_BOOK_NAMES } from "./config.js";
import { englishKeys, previewText, stripArabicMarks, tokenizeEnglish, tokenizeUrdu } from "./normalize.js";
import { registerBookAliases } from "./parser.js";

function packVerseId(bookId, chapter, verse) {
  return bookId * 1_000_000 + chapter * 1_000 + verse;
}

function unpackVerseId(verseId) {
  const bookId = Math.floor(verseId / 1_000_000);
  const remainder = verseId % 1_000_000;
  return [bookId, Math.floor(remainder / 1_000), remainder % 1_000];
}

function addPosting(postings, keys, verseId) {
  for (const key of keys) {
    const bucket = postings.get(key);
    if (!bucket) postings.set(key, [verseId]);
    else if (bucket[bucket.length - 1] !== verseId) bucket.push(verseId);
  }
}

export function openBible(data) {
  const aliases = [];
  const books = new Map();
  for (const book of data.books) {
    const plainUrdu = stripArabicMarks(book.ur);
    const patterns = [book.en, book.ur];
    if (plainUrdu !== book.ur) patterns.push(plainUrdu);
    for (const pattern of patterns) aliases.push([book.id, pattern]);
    const chapters = book.chapters.map((chapter) => {
      const english = new Map();
      const urdu = new Map();
      for (const [verse, en, ur] of chapter.v) {
        if (en) english.set(verse, en);
        if (ur) urdu.set(verse, ur);
      }
      return { n: chapter.n, english, urdu };
    });
    books.set(book.id, { id: book.id, en: book.en, ur: book.ur, chapters });
  }
  registerBookAliases(aliases);

  let index = null;

  function ensureIndex() {
    if (index) return index;
    const english = new Map();
    const urdu = new Map();
    const previewEn = new Map();
    const previewUr = new Map();
    const names = new Map();
    for (const book of books.values()) {
      names.set(book.id, [book.en, book.ur]);
      book.chapters.forEach((chapter, chapterIndex) => {
        const chapterNumber = chapterIndex + 1;
        const seenUrdu = new Set();
        for (const [number, text] of chapter.english) {
          const verseId = packVerseId(book.id, chapterNumber, number);
          addPosting(english, [...new Set(tokenizeEnglish(text))].flatMap((token) => englishKeys(token)), verseId);
          previewEn.set(verseId, previewText(text));
          const urduText = chapter.urdu.get(number);
          if (!urduText) continue;
          seenUrdu.add(number);
          addPosting(urdu, [...new Set(tokenizeUrdu(urduText))], verseId);
          previewUr.set(verseId, previewText(urduText));
        }
        for (const [number, text] of chapter.urdu) {
          if (seenUrdu.has(number)) continue;
          const verseId = packVerseId(book.id, chapterNumber, number);
          addPosting(urdu, [...new Set(tokenizeUrdu(text))], verseId);
          previewUr.set(verseId, previewText(text));
        }
      });
    }
    index = { english, urdu, previewEn, previewUr, names };
    return index;
  }

  function chapterText(language, bookId, chapterNumber) {
    const book = books.get(bookId);
    const name = language === "en" ? "English" : "Urdu";
    if (!book || chapterNumber < 1 || chapterNumber > book.chapters.length) {
      throw new Error(`Could not load the ${name} text for book ${bookId}, chapter ${chapterNumber}.`);
    }
    return book.chapters[chapterNumber - 1];
  }

  return {
    resolve(specs) {
      if (!specs.length) throw new Error("Enter a reference such as John 3:16.");
      const verses = [];
      for (const spec of specs) {
        const englishChapter = chapterText("en", spec.bookId, spec.chapter);
        const urduChapter = chapterText("ur", spec.bookId, spec.chapter);
        const book = books.get(spec.bookId);
        const englishName = book ? book.en : spec.bookName;
        const urduName = book ? book.ur : spec.bookName;
        const last = Math.max(englishChapter.n, urduChapter.n);
        const end = spec.verseEnd == null ? last : spec.verseEnd;
        if (spec.verseStart > last) throw new Error(`${englishName} ${spec.chapter} only has ${last} verses.`);
        for (let number = spec.verseStart; number <= Math.min(end, last); number += 1) {
          const english = englishChapter.english.get(number) || null;
          const urdu = urduChapter.urdu.get(number) || null;
          if (!english && !urdu) continue;
          verses.push({
            bookId: spec.bookId,
            bookName: englishName,
            bookNameUrdu: urduName,
            chapter: spec.chapter,
            verse: number,
            english,
            urdu,
            reference: `${englishName} ${spec.chapter}:${number}`,
          });
        }
      }
      if (!verses.length) throw new Error("Those verses were not found.");
      return verses;
    },

    search(raw, limit = 50) {
      const urduQuery = /[\u0600-\u06FF]/.test(raw);
      const tokens = urduQuery ? tokenizeUrdu(raw) : tokenizeEnglish(raw);
      if (!tokens.length) return { hits: [], total: 0, empty: true };
      const built = ensureIndex();
      const postings = urduQuery ? built.urdu : built.english;
      const previews = urduQuery ? built.previewUr : built.previewEn;
      let ids = null;
      for (const token of tokens) {
        const union = new Set();
        const keys = urduQuery ? [token] : englishKeys(token);
        for (const key of keys) {
          for (const verseId of postings.get(key) || []) union.add(verseId);
        }
        ids = ids === null ? union : new Set([...ids].filter((verseId) => union.has(verseId)));
      }
      const ordered = [...(ids || [])].sort((left, right) => left - right);
      const hits = ordered.slice(0, limit).map((verseId) => {
        const [bookId, chapter, verse] = unpackVerseId(verseId);
        const [englishName, urduName] = built.names.get(bookId) || ["Verse", "Verse"];
        const name = urduQuery ? urduName : englishName;
        return {
          bookId,
          chapter,
          verse,
          reference: `${name} ${chapter}:${verse}`,
          preview: previews.get(verseId) || "",
          language: urduQuery ? "urdu" : "english",
        };
      });
      return { hits, total: ordered.length, empty: false };
    },

    bookName(bookId) {
      return books.get(bookId)?.en || ENGLISH_BOOK_NAMES[bookId] || "Verse";
    },
  };
}
