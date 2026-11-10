# Publish WordOnAir Slides on the Chrome Web Store

The Chrome package is an extension. It is not the Windows `.msix`. A pastor opens it from the Chrome toolbar, looks up a verse, and downloads a PowerPoint file. The World English Bible and the Urdu Geo Version are inside the package, so a lookup does not contact WordOnAir Labs.

## Package

The Chrome Web Store workflow uploads `WordOnAirSlides_<version>_chrome.zip` as the artifact `WordOnAirSlides-chrome`. It does not build or replace the Windows `.msix`. Download that zip and upload it in the [Chrome Web Store developer dashboard](https://chrome.google.com/webstore/devconsole). Do not unzip it first.

To build the same zip on this PC:

```powershell
python packaging/build_chrome.py
```

The file is `dist/WordOnAirSlides_1.0.2_chrome.zip`. Load `dist/chrome` as an unpacked extension when you want to try it before the upload.

## Listing

- Item: Extension
- Name: WordOnAir Slides
- Summary: the description already in `chrome/manifest.json`
- Detailed description: `store/chrome/description.txt`
- Category: Productivity
- Language: English
- Icon: `store/chrome/icon-128.png` (the build writes this 128×128 PNG)
- Screenshot: one 1280×800 capture of the extension page, with a reference such as John 3:16 in the preview
- Homepage: https://wordonair.com
- Privacy policy: https://sgeorge83.github.io/ppt-app/

Publish the privacy page before you submit. The Chrome section is in `docs/index.html`, which GitHub Pages serves at that URL.

## Privacy form

Single purpose: Place Bible verses on PowerPoint slides.

Permission justification for `storage`: Remembers the church name, theme, language, and an optional logo in Chrome on this computer. Nothing is sent to WordOnAir Labs.

The extension has no host permission and no remote code. In the data-use questions, it does not collect or transmit personal information. The church name and logo stay in Chrome’s local storage and in the PowerPoint file the pastor downloads.

## What is different from the Windows app

The extension downloads a new PowerPoint file. It does not insert slides into a presentation that is already open. The pastor copies the downloaded slides into that file in PowerPoint. Urdu is marked right to left. PowerPoint uses Noto Nastaliq Urdu when that font is already installed.
