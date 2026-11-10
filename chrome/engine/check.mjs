/** Checks the Chrome verse engine, and John 3:16 when a Bible file is passed. */

import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";

import { openBible } from "./bible.js";
import { englishKeys } from "./normalize.js";
import { parseReference } from "./parser.js";
import { groupIntoSlides } from "./grouping.js";
import { buildPptx } from "../pptx.js";
import { readStoredZip } from "../zip.js";

assert.ok(englishKeys("loved").includes("love"));

const john = parseReference("John 3:16");
assert.equal(john[0].bookId, 43);
assert.equal(john[0].chapter, 3);
assert.equal(john[0].verseStart, 16);
assert.equal(john[0].verseEnd, 16);

const short = parseReference("Jn 3:16");
assert.equal(short[0].bookId, 43);

const psalm = parseReference("Psalm 23");
assert.equal(psalm[0].bookId, 19);
assert.equal(psalm[0].chapter, 23);
assert.equal(psalm[0].verseEnd, null);

const passage = parseReference("1 Cor 13:4-7");
assert.equal(passage[0].bookId, 46);
assert.equal(passage[0].verseStart, 4);
assert.equal(passage[0].verseEnd, 7);

const jude = parseReference("Jude 3");
assert.equal(jude[0].bookId, 65);
assert.equal(jude[0].chapter, 1);
assert.equal(jude[0].verseStart, 3);

const sample = [
  { bookId: 43, bookName: "John", bookNameUrdu: "یوحنا", chapter: 3, verse: 16, english: "For God so loved the world.", urdu: "محبت", reference: "John 3:16" },
  { bookId: 43, bookName: "John", bookNameUrdu: "یوحنا", chapter: 3, verse: 17, english: "For God didn't send his Son.", urdu: "بیٹا", reference: "John 3:17" },
];

const separate = groupIntoSlides(sample, "english", false);
assert.equal(separate.length, 2);
assert.equal(separate[0].english, "For God so loved the world.");
assert.equal(separate[0].urdu, null);
assert.equal(separate[0].attribution, "World English Bible");

const together = groupIntoSlides(sample, "both", true);
assert.equal(together.length, 1);
assert.equal(together[0].english, "16  For God so loved the world.\n17  For God didn't send his Son.");
assert.ok(together[0].urdu.includes("محبت"));
assert.equal(together[0].reference, "John 3:16-17");
assert.equal(together[0].attribution, "Urdu Geo Version · World English Bible");

const urduOnly = groupIntoSlides(sample, "urdu", false)[0];
assert.equal(urduOnly.reference, "یوحنا 3:16");
assert.equal(urduOnly.english, null);

const skipped = [sample[0], { ...sample[1], verse: 19, reference: "John 3:19" }];
assert.equal(groupIntoSlides(skipped, "english", true).length, 2);

const template = readFileSync(new URL("../blank.pptx", import.meta.url));
const pptx = buildPptx(template, together, { themeId: "air", churchName: "Grace Chapel" });
const packed = readStoredZip(pptx);
const xml = new TextDecoder().decode(packed.get("ppt/slides/slide1.xml"));
assert.match(xml, /For God so loved the world\./);
assert.match(xml, /محبت/);
assert.match(xml, /Urdu Geo Version · World English Bible/);
assert.match(xml, /Grace Chapel/);
assert.match(xml, /rtl="1"/);
if (process.env.CHROME_CHECK_PPTX) writeFileSync(process.env.CHROME_CHECK_PPTX, pptx);

const biblePath = process.argv[2];
if (biblePath) {
  const web = "For God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.";
  const urdu = "کیونکہ اللہ نے دنیا سے اِتنی محبت رکھی کہ اُس نے اپنے اکلوتے فرزند کو بخش دیا، تاکہ جو بھی اُس پر ایمان لائے ہلاک نہ ہو بلکہ ابدی زندگی پائے۔";
  const bible = openBible(JSON.parse(readFileSync(biblePath, "utf8")));
  const verses = bible.resolve(parseReference("John 3:16"));
  assert.equal(verses.length, 1);
  assert.equal(verses[0].english, web);
  assert.equal(verses[0].urdu, urdu);
  assert.equal(verses[0].bookNameUrdu, "یوحنا");
  const named = parseReference("یوحنا 3:16");
  assert.equal(named[0].bookId, 43);
  assert.equal(named[0].verseStart, 16);
  const found = bible.search("love", 2000);
  assert.equal(found.empty, false);
  assert.ok(found.hits.some((hit) => hit.bookId === 43 && hit.chapter === 3 && hit.verse === 16));
  const slides = groupIntoSlides(verses, "both", false);
  const full = buildPptx(template, slides, { churchName: "Grace Chapel" });
  const fullXml = new TextDecoder().decode(readStoredZip(full).get("ppt/slides/slide1.xml"));
  assert.match(fullXml, /For God so loved the world, that he gave his one and only Son/);
  assert.match(fullXml, /rtl="1"/);
}

console.log(biblePath ? "Chrome engine and John 3:16 checks passed" : "Chrome engine checks passed");
