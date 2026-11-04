# Publish WordOnAir Slides on the Microsoft Store

Publisher: **WordOnAir Labs**  
Homepage: https://wordonair.com  
Privacy policy URL for Partner Center:

https://sgeorge83.github.io/ppt-app/

Package identity name: `WordOnAirLabs.WordOnAirSlides`  
Publisher: `CN=5144E98A-1B05-48A3-97EA-086D7DF840DF`  
Publisher display name: WordOnAir Labs

This is a new product. Partner Center assigns the Store ID when the submission is created. Do not reuse the Bible Widget Store ID.

## Listing

Copy from `store/listing/en-US/`.

- Name: WordOnAir Slides
- Category: Books & reference
- Price: Free
- Age rating: suitable for all ages. Religious text. No user interaction that collects data. No ads.
- Privacy policy: the GitHub Pages URL above
- Support: sharoong27@gmail.com
- Screenshots: `store/listing/en-US/about.png` from the GitHub build, plus a window capture from a PC that can open the app
- Logos: `StoreListing300x300.png`, `StoreListing150x150.png`, `StoreListing71x71.png`

## Package

GitHub Actions builds `dist/WordOnAirSlides_<version>_x64.msix` and uploads it as an artifact. Download that file and upload it under Partner Center → Packages.

Microsoft signs Store packages. A paid code-signing certificate is not required for the submission.

The installed app includes the World English Bible and the Urdu Geo Version. Urdu text is marked right to left. The package does not install a system font, because this Store account cannot use the shared-font extension. PowerPoint uses Noto Nastaliq Urdu when that font is already on the PC.
