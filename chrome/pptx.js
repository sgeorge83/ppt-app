/** Build a widescreen PowerPoint file from the packaged blank presentation. */

import { getTheme } from "./engine/config.js";
import { readStoredZip, writeStoredZip } from "./zip.js";

const SLIDE_WIDTH = 12192000;
const SLIDE_HEIGHT = 6858000;
const encoder = new TextEncoder();
const decoder = new TextDecoder();

function inches(value) {
  return Math.trunc(value * 914400);
}

function points(value) {
  return Math.trunc(value * 12700);
}

function xmlEscape(value) {
  return value
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function textBox(id, left, top, width, height, text, fontName, size, color, { bold = false, rtl = false } = {}) {
  const paragraphs = (text || "").split("\n");
  const align = rtl ? ' algn="r" rtl="1"' : ' algn="l"';
  const weight = bold ? ' b="1"' : "";
  const body = paragraphs.map((line) => {
    const run = line
      ? `<a:r><a:rPr sz="${size * 100}"${weight}><a:solidFill><a:srgbClr val="${color}"/></a:solidFill><a:latin typeface="${xmlEscape(fontName)}"/><a:cs typeface="${xmlEscape(fontName)}"/><a:ea typeface="${xmlEscape(fontName)}"/></a:rPr><a:t>${xmlEscape(line)}</a:t></a:r>`
      : `<a:endParaRPr sz="${size * 100}"/>`;
    return `<a:p><a:pPr${align}><a:spcAft><a:spcPts val="600"/></a:spcAft></a:pPr>${run}</a:p>`;
  }).join("");
  return `<p:sp><p:nvSpPr><p:cNvPr id="${id}" name="TextBox ${id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="${left}" y="${top}"/><a:ext cx="${width}" cy="${height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>${body}</p:txBody></p:sp>`;
}

function rule(id, left, top, color) {
  return `<p:sp><p:nvSpPr><p:cNvPr id="${id}" name="Rectangle ${id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="${left}" y="${top}"/><a:ext cx="${inches(1.8)}" cy="${points(4)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="${color}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="ctr"/></a:p></p:txBody></p:sp>`;
}

function picture(id, left, top, width, height) {
  return `<p:pic><p:nvPicPr><p:cNvPr id="${id}" name="Logo"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="${left}" y="${top}"/><a:ext cx="${width}" cy="${height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>`;
}

function slideXml(shapes, background) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="${background}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>${shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>`;
}

function paintSlide(content, theme, churchName, logo) {
  const margin = inches(0.55);
  const contentWidth = SLIDE_WIDTH - inches(1.1) - (logo ? inches(1.15) : 0);
  const parts = [];
  let shapeId = 2;
  if (logo) {
    const logoHeight = inches(0.82);
    const logoWidth = Math.max(1, Math.round(logoHeight * (logo.width / logo.height)));
    parts.push(picture(shapeId, SLIDE_WIDTH - inches(1.45), inches(0.32), logoWidth, logoHeight));
    shapeId += 1;
  }
  let cursor = inches(0.38);
  if (churchName.trim()) {
    parts.push(textBox(shapeId, margin, cursor, contentWidth, inches(0.38), churchName.trim(), theme.font, 16, theme.muted, { bold: true }));
    shapeId += 1;
    cursor += inches(0.36);
  }
  parts.push(textBox(shapeId, margin, cursor, contentWidth, inches(0.55), content.reference, theme.font, 28, theme.accent, { bold: true }));
  shapeId += 1;
  parts.push(rule(shapeId, margin, cursor + inches(0.58), theme.accent));
  shapeId += 1;
  cursor += inches(0.78);
  const bottom = SLIDE_HEIGHT - inches(0.62);
  const bodyHeight = bottom - cursor - inches(0.08);
  if (content.urdu && content.english) {
    const urduHeight = Math.trunc(bodyHeight * 0.46);
    parts.push(textBox(shapeId, margin, cursor, contentWidth, urduHeight, content.urdu, theme.urduFont, 24, theme.text, { rtl: true }));
    shapeId += 1;
    parts.push(textBox(shapeId, margin, cursor + urduHeight, contentWidth, bodyHeight - urduHeight, content.english, theme.font, 20, theme.text));
    shapeId += 1;
  } else if (content.urdu) {
    parts.push(textBox(shapeId, margin, cursor, contentWidth, bodyHeight, content.urdu, theme.urduFont, 28, theme.text, { rtl: true }));
    shapeId += 1;
  } else {
    parts.push(textBox(shapeId, margin, cursor, contentWidth, bodyHeight, content.english || "", theme.font, 24, theme.text));
    shapeId += 1;
  }
  if (content.attribution) {
    parts.push(textBox(shapeId, margin, SLIDE_HEIGHT - inches(0.48), SLIDE_WIDTH - inches(1.1), inches(0.32), content.attribution, theme.font, 12, theme.muted));
  }
  return slideXml(parts.join(""), theme.background);
}

function slideRels(layoutTarget, logoName) {
  const image = logoName
    ? `<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/${logoName}"/>`
    : "";
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="${layoutTarget}"/>${image}</Relationships>`;
}

function textOf(bytes) {
  return decoder.decode(bytes);
}

export function buildPptx(templateBytes, slides, { themeId = "air", churchName = "", logo = null } = {}) {
  if (!slides.length) throw new Error("No verse text is available in that language.");
  const theme = getTheme(themeId);
  const files = readStoredZip(templateBytes);
  const layoutMatch = textOf(files.get("ppt/slides/_rels/slide1.xml.rels") || new Uint8Array()).match(/Target="(\.\.\/slideLayouts\/slideLayout\d+\.xml)"/);
  const layoutTarget = layoutMatch ? layoutMatch[1] : "../slideLayouts/slideLayout7.xml";
  const logoName = logo ? `logo.${logo.ext === "png" ? "png" : "jpeg"}` : null;

  let rels = textOf(files.get("ppt/_rels/presentation.xml.rels"));
  rels = rels.replace(/<Relationship\b[^>]*\/relationships\/slide"[^>]*\/>/g, "");
  const usedIds = [...rels.matchAll(/Id="rId(\d+)"/g)].map((match) => Number(match[1]));
  let nextRelationship = Math.max(0, ...usedIds) + 1;
  const relationshipIds = slides.map(() => {
    const id = nextRelationship;
    nextRelationship += 1;
    return id;
  });
  const slideRelsXml = relationshipIds.map((id, index) => (
    `<Relationship Id="rId${id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${index + 1}.xml"/>`
  )).join("");
  rels = rels.replace("</Relationships>", `${slideRelsXml}</Relationships>`);
  files.set("ppt/_rels/presentation.xml.rels", encoder.encode(rels));

  let presentation = textOf(files.get("ppt/presentation.xml"));
  const ids = relationshipIds.map((id, index) => `<p:sldId id="${256 + index}" r:id="rId${id}"/>`).join("");
  if (!/<p:sldIdLst>[\s\S]*?<\/p:sldIdLst>/.test(presentation)) {
    throw new Error("The PowerPoint template is missing its slide list.");
  }
  presentation = presentation.replace(/<p:sldIdLst>[\s\S]*?<\/p:sldIdLst>/, `<p:sldIdLst>${ids}</p:sldIdLst>`);
  presentation = presentation.replace(/<p:sldSz\b[^>]*\/>/, '<p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>');
  files.set("ppt/presentation.xml", encoder.encode(presentation));

  let types = textOf(files.get("[Content_Types].xml"));
  types = types.replace(/<Override PartName="\/ppt\/slides\/slide\d+\.xml"[^>]*\/>/g, "");
  if (logo?.ext === "png" && !/Extension="png"/.test(types)) {
    types = types.replace(/(<Types\b[^>]*>)/, '$1<Default Extension="png" ContentType="image/png"/>');
  }
  const overrides = slides.map((_, index) => (
    `<Override PartName="/ppt/slides/slide${index + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`
  )).join("");
  types = types.replace("</Types>", `${overrides}</Types>`);
  files.set("[Content_Types].xml", encoder.encode(types));

  const app = files.get("docProps/app.xml");
  if (app) {
    files.set("docProps/app.xml", encoder.encode(textOf(app).replace(/<Slides>\d+<\/Slides>/, `<Slides>${slides.length}</Slides>`)));
  }

  for (const name of [...files.keys()]) {
    if (/^ppt\/slides\/slide\d+\.xml/.test(name) || /^ppt\/media\//.test(name)) files.delete(name);
  }
  slides.forEach((content, index) => {
    const number = index + 1;
    files.set(`ppt/slides/slide${number}.xml`, encoder.encode(paintSlide(content, theme, churchName, logo)));
    files.set(`ppt/slides/_rels/slide${number}.xml.rels`, encoder.encode(slideRels(layoutTarget, logoName)));
  });
  if (logo && logoName) files.set(`ppt/media/${logoName}`, logo.bytes);

  const preferred = ["[Content_Types].xml", "_rels/.rels", "docProps/core.xml", "docProps/app.xml", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels"];
  const names = [...files.keys()].sort((left, right) => {
    const leftRank = preferred.indexOf(left);
    const rightRank = preferred.indexOf(right);
    if (leftRank !== -1 || rightRank !== -1) return (leftRank === -1 ? 99 : leftRank) - (rightRank === -1 ? 99 : rightRank);
    return left < right ? -1 : left > right ? 1 : 0;
  });
  return writeStoredZip(names.map((name) => ({ name, data: files.get(name) })));
}
