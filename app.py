"""WordOnAir Slides — desktop window for pastors."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

try:
    from pythonnet import load as load_runtime

    load_runtime("netfx")
except Exception:
    pass

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System import Action
from System.Drawing import Bitmap, Color, Font, FontStyle, Point, Rectangle, Size
from System.Drawing.Imaging import ImageFormat
from System.Windows.Forms import (
    Application,
    BorderStyle,
    Button,
    CheckBox,
    Cursors,
    DialogResult,
    DockStyle,
    FlatStyle,
    Form,
    FormBorderStyle,
    FormStartPosition,
    Label,
    ListBox,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    OpenFileDialog,
    Padding,
    Panel,
    SaveFileDialog,
    ScrollBars,
    SelectionMode,
    TabControl,
    TabPage,
    TextBox,
)

from slides.about import APP_NAME, PURPOSE, PUBLISHER
from slides.config import ENGLISH_BOOK_NAMES, GOLD, MIST, MUTED, NAVY, TEAL, WHITE
from slides.export_pptx import export_pptx
from slides.lookup import resolve_passages
from slides.models import PassageSpec
from slides.parser import parse_reference_string
from slides.paths import bible_text_ready
from slides.search import query_index
from slides.settings import load_settings, save_settings
from slides.themes import THEMES
from slides.topics import TOPICS


def windows_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\n", "\r\n")


def color_of(hex_color: str) -> Color:
    value = hex_color.removeprefix("#")
    return Color.FromArgb(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


NAVY_C = color_of(NAVY)
GOLD_C = color_of(GOLD)
MIST_C = color_of(MIST)
MUTED_C = color_of(MUTED)
TEAL_C = color_of(TEAL)
WHITE_C = color_of(WHITE)
BROWN_C = color_of("#8A6430")
LINE_C = color_of("#D5DEEA")
ERROR_BACK = color_of("#F8E8E4")
ERROR_FORE = color_of("#6D2A22")
OK_BACK = color_of("#E5F2EA")
OK_FORE = color_of("#1D5A38")


def ui_font(size: float, bold: bool = False) -> Font:
    style = FontStyle.Bold if bold else FontStyle.Regular
    return Font("Segoe UI", size, style)


class MainForm(Form):
    def __init__(self):
        super().__init__()
        self.Text = APP_NAME
        self.ClientSize = Size(980, 700)
        self.MinimumSize = Size(860, 620)
        self.StartPosition = FormStartPosition.CenterScreen
        self.BackColor = MIST_C
        self.Font = ui_font(10)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.language = "both"
        self.theme_id = "air"
        self.search_hits = []
        self._settings = load_settings()
        self.language = self._settings.get("language", "both")
        if self.language not in ("both", "english", "urdu"):
            self.language = "both"
        self.theme_id = self._settings.get("theme", "air")
        self._build()
        self._apply_settings()
        if not bible_text_ready():
            self._set_status(
                "Bible text is not beside the app yet. The Store package includes the World English Bible and the Urdu Geo Version.",
                "error",
            )

    def _build(self) -> None:
        header = Panel()
        header.Dock = DockStyle.Top
        header.Height = 104
        header.BackColor = WHITE_C
        gold_line = Panel()
        gold_line.Dock = DockStyle.Bottom
        gold_line.Height = 3
        gold_line.BackColor = GOLD_C
        teal = Panel()
        teal.Dock = DockStyle.Bottom
        teal.Height = 2
        teal.BackColor = TEAL_C
        kicker = Label()
        kicker.Text = PUBLISHER
        kicker.ForeColor = BROWN_C
        kicker.Font = ui_font(9, True)
        kicker.Location = Point(22, 12)
        kicker.AutoSize = True
        title = Label()
        title.Text = APP_NAME
        title.ForeColor = NAVY_C
        title.Font = ui_font(20, True)
        title.Location = Point(20, 32)
        title.AutoSize = True
        subtitle = Label()
        subtitle.Text = "English and Urdu verses for PowerPoint"
        subtitle.ForeColor = MUTED_C
        subtitle.Font = ui_font(9)
        subtitle.Location = Point(22, 70)
        subtitle.AutoSize = True
        header.Controls.Add(subtitle)
        header.Controls.Add(title)
        header.Controls.Add(kicker)
        header.Controls.Add(teal)
        header.Controls.Add(gold_line)

        tools = Panel()
        tools.Dock = DockStyle.Top
        tools.Height = 48
        tools.BackColor = MIST_C
        tools.Padding = Padding(16, 8, 16, 8)
        self.language_buttons = {}
        x = 18
        for key, label in (("both", "Both"), ("english", "English"), ("urdu", "Urdu")):
            button = Button()
            button.Text = label
            button.Size = Size(88, 30)
            button.Location = Point(x, 9)
            button.FlatStyle = FlatStyle.Flat
            button.Cursor = Cursors.Hand
            button.Click += lambda _sender, _args, chosen=key: self._choose_language(chosen)
            tools.Controls.Add(button)
            self.language_buttons[key] = button
            x += 94
        self.keep_together = CheckBox()
        self.keep_together.Text = "Keep a passage together"
        self.keep_together.AutoSize = True
        self.keep_together.Location = Point(320, 14)
        self.keep_together.ForeColor = NAVY_C
        self.keep_together.Checked = bool(self._settings.get("keepTogether", False))
        tools.Controls.Add(self.keep_together)

        self.status = Label()
        self.status.Dock = DockStyle.Bottom
        self.status.Height = 36
        self.status.Padding = Padding(16, 8, 16, 0)
        self.status.BackColor = color_of("#E7EEF6")
        self.status.ForeColor = NAVY_C
        self.status.Text = "Connected. Choose Both, English, or Urdu, then enter a reference."

        footer = Panel()
        footer.Dock = DockStyle.Bottom
        footer.Height = 58
        footer.BackColor = WHITE_C
        preview = self._button("Preview", False)
        preview.Location = Point(18, 12)
        preview.Click += self._on_preview
        create = self._button("Create PowerPoint", True)
        create.Location = Point(150, 12)
        create.Size = Size(180, 34)
        create.Click += self._on_create
        add = self._button("Add to existing", False)
        add.Location = Point(342, 12)
        add.Size = Size(160, 34)
        add.Click += self._on_add
        footer.Controls.Add(preview)
        footer.Controls.Add(create)
        footer.Controls.Add(add)

        self.tabs = TabControl()
        self.tabs.Dock = DockStyle.Fill
        self.tabs.Font = ui_font(10)
        self.tabs.TabPages.Add(self._reference_page())
        self.tabs.TabPages.Add(self._search_page())
        self.tabs.TabPages.Add(self._topics_page())
        self.tabs.TabPages.Add(self._church_page())
        self.tabs.TabPages.Add(self._about_page())

        self.Controls.Add(self.tabs)
        self.Controls.Add(footer)
        self.Controls.Add(self.status)
        self.Controls.Add(tools)
        self.Controls.Add(header)
        self._choose_language(self.language)

    def _button(self, text: str, primary: bool) -> Button:
        button = Button()
        button.Text = text
        button.Size = Size(120, 34)
        button.FlatStyle = FlatStyle.Flat
        button.Cursor = Cursors.Hand
        button.Font = ui_font(10, True)
        if primary:
            button.BackColor = NAVY_C
            button.ForeColor = MIST_C
            button.FlatAppearance.BorderSize = 0
        else:
            button.BackColor = WHITE_C
            button.ForeColor = NAVY_C
            button.FlatAppearance.BorderColor = LINE_C
            button.FlatAppearance.BorderSize = 1
        return button

    def _field(self) -> TextBox:
        box = TextBox()
        box.BorderStyle = BorderStyle.FixedSingle
        box.Font = ui_font(11)
        box.BackColor = WHITE_C
        box.ForeColor = NAVY_C
        return box

    def _reference_page(self) -> TabPage:
        page = TabPage()
        page.Text = "Reference"
        page.BackColor = MIST_C
        page.Padding = Padding(16)
        hint = Label()
        hint.Text = "Example: John 3:16, Jn 3:16, Psalm 23, 1 Cor 13:4-7, or یوحنا 3:16"
        hint.ForeColor = MUTED_C
        hint.Location = Point(16, 16)
        hint.AutoSize = True
        self.reference_box = self._field()
        self.reference_box.Location = Point(16, 44)
        self.reference_box.Size = Size(900, 28)
        self.preview_box = self._multiline(Point(16, 88), Size(900, 360))
        page.Controls.Add(hint)
        page.Controls.Add(self.reference_box)
        page.Controls.Add(self.preview_box)
        return page

    def _search_page(self) -> TabPage:
        page = TabPage()
        page.Text = "Search"
        page.BackColor = MIST_C
        hint = Label()
        hint.Text = "Search English or Urdu. The verse on the slide still follows Both, English, or Urdu."
        hint.ForeColor = MUTED_C
        hint.Location = Point(16, 16)
        hint.AutoSize = True
        self.search_box = self._field()
        self.search_box.Location = Point(16, 44)
        self.search_box.Size = Size(760, 28)
        find = self._button("Search", True)
        find.Location = Point(788, 42)
        find.Click += self._on_search
        self.search_list = ListBox()
        self.search_list.Location = Point(16, 86)
        self.search_list.Size = Size(900, 360)
        self.search_list.Font = ui_font(10)
        self.search_list.SelectionMode = SelectionMode.MultiExtended
        self.search_list.BorderStyle = BorderStyle.FixedSingle
        page.Controls.Add(hint)
        page.Controls.Add(self.search_box)
        page.Controls.Add(find)
        page.Controls.Add(self.search_list)
        return page

    def _topics_page(self) -> TabPage:
        page = TabPage()
        page.Text = "Topics"
        page.BackColor = MIST_C
        hint = Label()
        hint.Text = "A short list for the sermon, not every verse that contains the word."
        hint.ForeColor = MUTED_C
        hint.Location = Point(16, 16)
        hint.AutoSize = True
        self.topic_list = ListBox()
        self.topic_list.Location = Point(16, 48)
        self.topic_list.Size = Size(220, 400)
        self.topic_list.Font = ui_font(11)
        self.topic_list.BorderStyle = BorderStyle.FixedSingle
        for topic in TOPICS:
            self.topic_list.Items.Add(topic.label)
        self.topic_list.SelectedIndexChanged += self._on_topic
        self.topic_refs = ListBox()
        self.topic_refs.Location = Point(252, 48)
        self.topic_refs.Size = Size(664, 400)
        self.topic_refs.Font = ui_font(11)
        self.topic_refs.SelectionMode = SelectionMode.MultiExtended
        self.topic_refs.BorderStyle = BorderStyle.FixedSingle
        page.Controls.Add(hint)
        page.Controls.Add(self.topic_list)
        page.Controls.Add(self.topic_refs)
        if TOPICS:
            self.topic_list.SelectedIndex = 0
        return page

    def _church_page(self) -> TabPage:
        page = TabPage()
        page.Text = "Church"
        page.BackColor = MIST_C
        name_label = Label()
        name_label.Text = "Church name"
        name_label.ForeColor = NAVY_C
        name_label.Location = Point(16, 18)
        name_label.AutoSize = True
        self.church_box = self._field()
        self.church_box.Location = Point(16, 44)
        self.church_box.Size = Size(640, 28)
        logo_label = Label()
        logo_label.Text = "Logo"
        logo_label.ForeColor = NAVY_C
        logo_label.Location = Point(16, 88)
        logo_label.AutoSize = True
        self.logo_box = self._field()
        self.logo_box.Location = Point(16, 114)
        self.logo_box.Size = Size(640, 28)
        self.logo_box.ReadOnly = True
        browse = self._button("Browse", False)
        browse.Location = Point(668, 112)
        browse.Click += self._on_browse_logo
        clear = self._button("Clear", False)
        clear.Location = Point(800, 112)
        clear.Click += lambda *_args: self._set_logo("")
        theme_label = Label()
        theme_label.Text = "Theme"
        theme_label.ForeColor = NAVY_C
        theme_label.Location = Point(16, 162)
        theme_label.AutoSize = True
        self.theme_buttons = {}
        x = 16
        for theme in THEMES:
            button = self._button(theme.name, False)
            button.Location = Point(x, 190)
            button.Size = Size(150, 40)
            button.Click += lambda _sender, _args, chosen=theme.id: self._choose_theme(chosen)
            page.Controls.Add(button)
            self.theme_buttons[theme.id] = button
            x += 162
        note = Label()
        note.Text = "Morning Air is the WordOnAir navy and gold. The verse wording stays the same in every theme."
        note.ForeColor = MUTED_C
        note.Location = Point(16, 248)
        note.AutoSize = True
        for control in (name_label, self.church_box, logo_label, self.logo_box, browse, clear, theme_label, note):
            page.Controls.Add(control)
        return page

    def _about_page(self) -> TabPage:
        page = TabPage()
        page.Text = "About"
        page.BackColor = MIST_C
        self.about_box = self._multiline(Point(16, 16), Size(900, 470))
        self.about_box.Text = windows_text(PURPOSE.strip())
        self.about_box.BackColor = WHITE_C
        page.Controls.Add(self.about_box)
        return page

    def _multiline(self, location: Point, size: Size) -> TextBox:
        box = TextBox()
        box.Multiline = True
        box.ReadOnly = True
        box.ScrollBars = ScrollBars.Vertical
        box.Location = location
        box.Size = size
        box.Font = ui_font(11)
        box.BackColor = WHITE_C
        box.ForeColor = NAVY_C
        box.BorderStyle = BorderStyle.FixedSingle
        return box

    def _apply_settings(self) -> None:
        self.church_box.Text = str(self._settings.get("churchName", ""))
        self._set_logo(str(self._settings.get("logoPath", "")))
        self._choose_theme(self.theme_id)

    def _persist(self) -> None:
        save_settings(
            {
                "language": self.language,
                "keepTogether": bool(self.keep_together.Checked),
                "churchName": self.church_box.Text,
                "logoPath": self.logo_box.Text,
                "theme": self.theme_id,
            }
        )

    def _choose_language(self, language: str) -> None:
        self.language = language
        for key, button in self.language_buttons.items():
            selected = key == language
            button.BackColor = WHITE_C if selected else color_of("#E6EDF5")
            button.ForeColor = NAVY_C
            button.FlatAppearance.BorderSize = 1 if selected else 0
            button.FlatAppearance.BorderColor = GOLD_C

    def _choose_theme(self, theme_id: str) -> None:
        self.theme_id = theme_id if theme_id in self.theme_buttons else "air"
        for key, button in self.theme_buttons.items():
            selected = key == self.theme_id
            button.BackColor = NAVY_C if selected else WHITE_C
            button.ForeColor = MIST_C if selected else NAVY_C
            button.FlatAppearance.BorderColor = GOLD_C

    def _set_logo(self, path: str) -> None:
        self.logo_box.Text = path

    def _on_browse_logo(self, _sender, _args) -> None:
        dialog = OpenFileDialog()
        dialog.Filter = "Images (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg"
        dialog.Title = "Church logo"
        if dialog.ShowDialog() == DialogResult.OK:
            self._set_logo(dialog.FileName)

    def _on_topic(self, _sender, _args) -> None:
        self.topic_refs.Items.Clear()
        index = self.topic_list.SelectedIndex
        if index < 0:
            return
        for reference in TOPICS[index].references:
            self.topic_refs.Items.Add(reference)

    def _on_search(self, _sender, _args) -> None:
        query = self.search_box.Text.strip()
        if not query:
            self._set_status("Enter a word to search.", "error")
            return
        self._set_status("Searching the Bible text…")

        def work() -> None:
            try:
                hits, total, empty = query_index(query)
            except Exception as exc:
                message = str(exc)
                self.BeginInvoke(Action(lambda: self._set_status(message, "error")))
                return

            def apply() -> None:
                self.search_hits = hits
                self.search_list.Items.Clear()
                if empty:
                    self._set_status("Enter a word with letters. Small words such as “the” are skipped.", "error")
                    return
                for hit in hits:
                    self.search_list.Items.Add(f"{hit.reference}  —  {hit.preview}")
                shown = len(hits)
                extra = f" Showing {shown}." if total > shown else ""
                self._set_status(f"{total} verses contain that word.{extra}", "ok")

            self.BeginInvoke(Action(apply))

        threading.Thread(target=work, daemon=True).start()

    def _specs_from_ui(self) -> list[PassageSpec]:
        index = self.tabs.SelectedIndex
        if index == 0:
            return parse_reference_string(self.reference_box.Text)
        if index == 1:
            chosen = list(self.search_list.SelectedIndices)
            if not chosen:
                raise ValueError("Select one or more search results.")
            specs = []
            for item in chosen:
                hit = self.search_hits[int(item)]
                specs.append(
                    PassageSpec(
                        hit.book_id,
                        ENGLISH_BOOK_NAMES.get(hit.book_id, "Verse"),
                        hit.chapter,
                        hit.verse,
                        hit.verse,
                        hit.reference,
                    )
                )
            return specs
        if index == 2:
            topic_index = self.topic_list.SelectedIndex
            if topic_index < 0:
                raise ValueError("Choose a topic.")
            selected = list(self.topic_refs.SelectedIndices)
            references = TOPICS[topic_index].references
            if selected:
                references = tuple(references[int(item)] for item in selected)
            return parse_reference_string("; ".join(references))
        raise ValueError("Open Reference, Search, or Topics, then create the slides.")

    def _preview_text(self, verses) -> str:
        from slides.grouping import group_into_slides

        slides = group_into_slides(verses, self.language, bool(self.keep_together.Checked))
        blocks = []
        for slide in slides:
            parts = [slide.reference, ""]
            if slide.urdu:
                parts.append(slide.urdu)
                parts.append("")
            if slide.english:
                parts.append(slide.english)
                parts.append("")
            if slide.attribution:
                parts.append(slide.attribution)
            blocks.append("\n".join(parts).strip())
        return "\n\n".join(blocks)

    def _on_preview(self, _sender, _args) -> None:
        try:
            verses = resolve_passages(self._specs_from_ui())
            self.preview_box.Text = windows_text(self._preview_text(verses))
            self.tabs.SelectedIndex = 0
            self._set_status(f"Preview ready. {len(verses)} verse{'s' if len(verses) != 1 else ''}.", "ok")
        except Exception as exc:
            self._set_status(str(exc), "error")

    def _on_create(self, _sender, _args) -> None:
        dialog = SaveFileDialog()
        dialog.Filter = "PowerPoint (*.pptx)|*.pptx"
        dialog.FileName = "WordOnAir-Slides.pptx"
        dialog.Title = "Create PowerPoint slides"
        if dialog.ShowDialog() != DialogResult.OK:
            return
        self._write(dialog.FileName, None)

    def _on_add(self, _sender, _args) -> None:
        dialog = OpenFileDialog()
        dialog.Filter = "PowerPoint (*.pptx)|*.pptx"
        dialog.Title = "Add slides to an existing presentation"
        if dialog.ShowDialog() != DialogResult.OK:
            return
        self._write(dialog.FileName, dialog.FileName)

    def _write(self, destination: str, existing: str | None) -> None:
        try:
            verses = resolve_passages(self._specs_from_ui())
            logo = self.logo_box.Text.strip() or None
            export_pptx(
                verses,
                destination,
                language=self.language,
                keep_together=bool(self.keep_together.Checked),
                theme_id=self.theme_id,
                church_name=self.church_box.Text,
                logo_path=logo,
                existing=existing,
            )
            self._persist()
            self.preview_box.Text = windows_text(self._preview_text(verses))
            self._set_status(f"Saved {destination}", "ok")
            os.startfile(destination)
        except Exception as exc:
            self._set_status(str(exc), "error")
            MessageBox.Show(str(exc), APP_NAME, MessageBoxButtons.OK, MessageBoxIcon.Warning)

    def _set_status(self, text: str, kind: str = "info") -> None:
        self.status.Text = text
        if kind == "error":
            self.status.BackColor = ERROR_BACK
            self.status.ForeColor = ERROR_FORE
        elif kind == "ok":
            self.status.BackColor = OK_BACK
            self.status.ForeColor = OK_FORE
        else:
            self.status.BackColor = color_of("#E7EEF6")
            self.status.ForeColor = NAVY_C


def save_about_snapshot(destination: Path) -> None:
    """Draw the About window onto a Store-sized PNG."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        Application.EnableVisualStyles()
        form = MainForm()
        form.tabs.SelectedIndex = 4
        form.Show()
        Application.DoEvents()
        width = form.Width
        height = form.Height
        shot = Bitmap(width, height)
        form.DrawToBitmap(shot, Rectangle(0, 0, width, height))
        canvas = Bitmap(1366, 768)
        from System.Drawing import Graphics

        graphics = Graphics.FromImage(canvas)
        graphics.Clear(MIST_C)
        x = max(0, (1366 - width) // 2)
        y = max(0, (768 - height) // 2)
        graphics.DrawImage(shot, x, y, width, height)
        graphics.Dispose()
        canvas.Save(str(destination), ImageFormat.Png)
        shot.Dispose()
        canvas.Dispose()
        form.Close()
    except Exception as exc:
        from slides.about_card import render_about_card

        print(f"About window could not be drawn ({exc}). Drawing the About card instead.")
        render_about_card(destination)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--about-snapshot":
        target = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("store/listing/en-US/about.png")
        save_about_snapshot(target)
        print(f"Wrote {target}")
        return
    Application.EnableVisualStyles()
    Application.SetCompatibleTextRenderingDefault(False)
    Application.Run(MainForm())


if __name__ == "__main__":
    main()
