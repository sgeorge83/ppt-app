# WordOnAir Slides

WordOnAir Slides is a free Windows app from WordOnAir Labs. Pastors type a reference, search a word, or pick a topic, and the app writes World English Bible and Urdu Geo verses onto PowerPoint slides. The wording is copied from those Bibles and is not rewritten.

Both languages stay in one app. **Both** is the usual choice. English-only and Urdu-only are choices for that slide.

## What a pastor does

1. Choose Both, English, or Urdu.
2. Enter a reference such as `John 3:16`, search, or choose a topic.
3. Add a church name, logo, and theme if wanted.
4. Create a PowerPoint file, or add the slides to a presentation that already exists.

Open the About tab in the app for the same explanation, the Bible credits, and how the app treats the church name and logo.

## Scripture

- World English Bible, public domain, from [english-bible-data](https://github.com/sgeorge83/english-bible-data)
- Urdu Geo Version, CC BY-NC-ND 4.0, from [urdu-bible-data](https://github.com/sgeorge83/urdu-bible-data)

The app stays free. A slide that includes Urdu credits `Urdu Geo Version · World English Bible`.

## Proof on GitHub

This PC is not the place the product is tested. GitHub Actions clones both Bible repositories, checks John 3:16 in both languages, checks search, and checks that the PowerPoint file contains both wordings and right-to-left Urdu. The same run builds the Microsoft Store package.

Store listing copy, the privacy policy, and upload steps are in [store/README.md](store/README.md).

## Local notes

```powershell
python packaging/prepare_data.py
python packaging/fetch_font.py
pip install -r requirements.txt
python -m pytest
python app.py
```

`python packaging/build_msix.ps1` builds the package when the Windows SDK is installed. The GitHub artifact is the file to upload.
