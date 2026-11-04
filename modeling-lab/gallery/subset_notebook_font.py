"""Build the notebook's self-hosted WOFF2 from a local LXGW WenKai TTF.

Requires fonttools[woff]. Run from any directory with the source font path.
The four catalogue entrances supply the default glyph set, including no-script
text. Use --pages, --output and --stylesheet for a separate page-specific font.
"""

import argparse
import hashlib
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont


SITE = Path(__file__).resolve().parents[2] / "docs"
ENTRIES = (
    "index.html",
    "model-library/index.html",
    "web-library/index.html",
    "space-library/index.html",
)


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.fragments = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignored = max(0, self.ignored - 1)

    def handle_data(self, data):
        if not self.ignored:
            self.fragments.append(data)


def site_path(value):
    """Resolve a docs-relative path without allowing writes outside the site."""
    path = Path(value)
    if path.is_absolute():
        raise argparse.ArgumentTypeError("Expected a path relative to docs")
    resolved = (SITE / path).resolve()
    if not resolved.is_relative_to(SITE.resolve()):
        raise argparse.ArgumentTypeError("Path must remain inside docs")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font", type=Path, help="Path to LXGWWenKai-Regular.ttf")
    parser.add_argument(
        "--pages", nargs="+", type=site_path,
        default=[SITE / entry for entry in ENTRIES],
        help="One or more HTML paths relative to docs (default: four entrances)",
    )
    parser.add_argument(
        "--output", type=site_path, default=SITE / "fonts/notebook-hand.woff2",
        help="Output WOFF2 path relative to docs",
    )
    parser.add_argument(
        "--stylesheet", type=site_path, default=SITE / "notebook-design.css",
        help="CSS path relative to docs whose font URL receives the content hash",
    )
    args = parser.parse_args()
    destination = args.output
    stylesheet = args.stylesheet
    font_url = Path(os.path.relpath(destination, stylesheet.parent)).as_posix()
    font_url_pattern = re.escape(font_url) + r"(?:\?v=[0-9a-f]+)?"
    stylesheet_text = stylesheet.read_text(encoding="utf-8-sig")
    if len(re.findall(font_url_pattern, stylesheet_text)) != 1:
        raise ValueError(f"Expected one {font_url} URL in {stylesheet.relative_to(SITE)}")

    text = PageText()
    for entry in args.pages:
        text.feed(entry.read_text(encoding="utf-8-sig"))
    characters = set("".join(text.fragments))
    characters.update(chr(code) for code in range(32, 127))
    codepoints = {ord(character) for character in characters if character.isprintable()}

    font = TTFont(args.font, recalcTimestamp=False)
    available = set(font.getBestCmap())
    missing = sorted(codepoints - available)
    options = subset.Options()
    options.flavor = "woff2"
    options.recalc_timestamp = False
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    options.name_languages = [0x409]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=codepoints & available)
    subsetter.subset(font)

    # Use a project-specific family while retaining copyright and licence names.
    names = font["name"]
    replacements = {
        1: "Notebook WenKai",
        3: "NotebookWenKai-Regular-WebSubset",
        4: "Notebook WenKai Regular",
        6: "NotebookWenKai-Regular",
    }
    for record in list(names.names):
        if record.nameID in replacements:
            names.setName(
                replacements[record.nameID],
                record.nameID,
                record.platformID,
                record.platEncID,
                record.langID,
            )
    font.flavor = "woff2"
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(destination)
    font.close()

    result = {
        "file": destination.relative_to(SITE).as_posix(),
        "sourceSha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
        "sourcePages": [entry.relative_to(SITE).as_posix() for entry in args.pages],
        "requestedCodepoints": len(codepoints),
        "includedCodepoints": len(codepoints & available),
        "fallbackCharacters": [chr(code) for code in missing],
        "bytes": destination.stat().st_size,
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }
    (destination.parent / "subset-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    css, replacements = re.subn(
        font_url_pattern,
        lambda _: f"{font_url}?v={result['sha256'][:8]}",
        stylesheet_text,
    )
    if replacements != 1:
        raise ValueError(f"Expected one {font_url} URL in {stylesheet.relative_to(SITE)}")
    stylesheet.write_text(css, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
