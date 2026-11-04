"""Build the notebook's self-hosted WOFF2 from a local LXGW WenKai TTF.

Requires fonttools[woff]. Run from any directory with the source font path.
The four catalogue entrances supply the glyph set, including no-script text.
"""

import argparse
import hashlib
import json
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font", type=Path, help="Path to LXGWWenKai-Regular.ttf")
    args = parser.parse_args()
    text = PageText()
    for entry in ENTRIES:
        text.feed((SITE / entry).read_text(encoding="utf-8-sig"))
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
    destination = SITE / "fonts" / "notebook-hand.woff2"
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(destination)
    font.close()

    result = {
        "file": destination.relative_to(SITE).as_posix(),
        "sourceSha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
        "sourcePages": list(ENTRIES),
        "requestedCodepoints": len(codepoints),
        "includedCodepoints": len(codepoints & available),
        "fallbackCharacters": [chr(code) for code in missing],
        "bytes": destination.stat().st_size,
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }
    (destination.parent / "subset-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    stylesheet = SITE / "notebook-design.css"
    css, replacements = re.subn(
        r"fonts/notebook-hand\.woff2(?:\?v=[0-9a-f]+)?",
        f"fonts/notebook-hand.woff2?v={result['sha256'][:8]}",
        stylesheet.read_text(encoding="utf-8-sig"),
    )
    if replacements != 1:
        raise ValueError("Expected one notebook font URL in notebook-design.css")
    stylesheet.write_text(css, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
