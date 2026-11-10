/** Token rules shared by English and Urdu search. Kept in step with slides/normalize.py. */

const ENGLISH_STOP = new Set([
  "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for", "with", "as", "at", "by",
  "from", "that", "this", "these", "those", "is", "are", "was", "were", "be", "been", "am", "it",
  "its", "he", "she", "they", "them", "his", "her", "their", "you", "your", "we", "our", "do",
  "did", "does", "have", "has", "had", "will", "shall", "into", "over", "after", "before", "about",
  "than", "then", "so", "if", "when", "who", "whom", "which", "what", "there", "here", "all",
  "also", "just", "unto", "ye", "thou", "thee", "thy", "thine", "hath", "shalt", "him", "me", "my",
  "i", "o",
]);

const URDU_STOP_RAW = [
  "کے", "کی", "کا", "کو", "نے", "میں", "سے", "پر", "ہے", "ہیں", "ہوں", "تھا", "تھی", "تھے",
  "اور", "یا", "یہ", "وہ", "ان", "اس", "کہ", "جو", "بھی", "ہی", "تو", "نہ", "نہیں", "گیا",
  "گئی", "گئے", "ایک", "کیا", "کر", "لیے", "لئے", "ہو", "ہوا", "ہوئی", "اپنے", "اپنی", "اپنا",
  "جس", "جن", "اگر", "تاکہ", "بلکہ", "بعد", "پہلے",
];

export function stripArabicMarks(text) {
  return text.replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u200C\u200D]/g, "");
}

export function normalizeUrduToken(text) {
  let cleaned = stripArabicMarks(text);
  cleaned = cleaned.replace(/[يى]/g, "ی");
  cleaned = cleaned.replaceAll("ك", "ک");
  cleaned = cleaned.replace(/[ۀہة]/g, "ہ");
  cleaned = cleaned.replace(/[أإآ]/g, "ا");
  cleaned = cleaned.replaceAll("ؤ", "و");
  return cleaned.replaceAll("ئ", "ی");
}

const URDU_STOP = new Set(URDU_STOP_RAW.map((word) => normalizeUrduToken(word)));

export function tokenizeEnglish(text) {
  let lowered = text.toLowerCase();
  lowered = lowered.replace(/['’]s\b/g, "");
  lowered = lowered.replace(/['’]/g, "");
  lowered = lowered.replace(/[^a-z0-9\s]/g, " ");
  return lowered.split(/\s+/).filter((token) => token.length >= 2 && !ENGLISH_STOP.has(token) && !/^\d+$/.test(token));
}

export function tokenizeUrdu(text) {
  let cleaned = normalizeUrduToken(text);
  cleaned = cleaned.replace(/[^\u0600-\u06FF\s]/g, " ");
  return cleaned.split(/\s+/).filter((token) => token.length >= 2 && !URDU_STOP.has(token));
}

export function englishKeys(token) {
  const keys = new Set([token]);
  if (token.length >= 5 && /[sd]$/.test(token) && !token.endsWith("ss")) {
    const stem = token.slice(0, -1);
    if (stem.length >= 4) keys.add(stem);
  }
  return [...keys];
}

export function previewText(text, limit = 100) {
  const clean = text.replace(/\s+/g, " ").trim();
  const chars = [...clean];
  if (chars.length <= limit) return clean;
  return `${chars.slice(0, limit).join("")}…`;
}
