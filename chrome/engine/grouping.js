/** Group resolved verses onto slides without changing the wording. */

import { ATTRIBUTION_BOTH, ATTRIBUTION_ENGLISH, MAX_COMBINED_CHARS } from "./config.js";

function visible(verse, language) {
  if (language === "english") return Boolean(verse.english);
  if (language === "urdu") return Boolean(verse.urdu);
  return Boolean(verse.english || verse.urdu);
}

function lengthOf(verse, language) {
  const parts = [];
  if (language !== "urdu" && verse.english) parts.push(verse.english);
  if (language !== "english" && verse.urdu) parts.push(verse.urdu);
  return parts.join(" ").length;
}

function joinField(verses, field) {
  const lines = [];
  for (const verse of verses) {
    const text = verse[field];
    if (!text) continue;
    lines.push(verses.length === 1 ? text : `${verse.verse}  ${text}`);
  }
  return lines.length ? lines.join("\n") : null;
}

function cite(verses, language) {
  const name = language === "urdu" ? verses[0].bookNameUrdu : verses[0].bookName;
  const first = verses[0].verse;
  const last = verses[verses.length - 1].verse;
  const chapter = verses[0].chapter;
  if (verses.length === 1 || first === last) return `${name} ${chapter}:${first}`;
  return `${name} ${chapter}:${first}-${last}`;
}

function toSlide(verses, language) {
  const english = language === "urdu" ? null : joinField(verses, "english");
  const urdu = language === "english" ? null : joinField(verses, "urdu");
  let attribution = null;
  if (urdu) attribution = ATTRIBUTION_BOTH;
  else if (english) attribution = ATTRIBUTION_ENGLISH;
  return { reference: cite(verses, language), english, urdu, attribution };
}

export function groupIntoSlides(verses, language, keepTogether) {
  const usable = verses.filter((verse) => visible(verse, language));
  if (!keepTogether) return usable.map((verse) => toSlide([verse], language));

  const groups = [];
  for (const verse of usable) {
    const current = groups.length ? groups[groups.length - 1] : null;
    const previous = current && current.length ? current[current.length - 1] : null;
    const contiguous = Boolean(
      previous
      && previous.bookId === verse.bookId
      && previous.chapter === verse.chapter
      && verse.verse === previous.verse + 1,
    );
    if (!current || !contiguous) groups.push([verse]);
    else current.push(verse);
  }

  const slides = [];
  for (const group of groups) {
    let chunk = [];
    let chars = 0;
    const flush = () => {
      if (chunk.length) slides.push(toSlide(chunk, language));
      chunk = [];
      chars = 0;
    };
    for (const verse of group) {
      const length = lengthOf(verse, language);
      if (chunk.length && chars + length > MAX_COMBINED_CHARS) flush();
      chunk.push(verse);
      chars += length;
    }
    flush();
  }
  return slides;
}
