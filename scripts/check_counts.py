#!/usr/bin/env python3
"""Check that every count in README.md matches the verbs actually listed,
and that every category's "Copy as list" block matches its table.

    python3 scripts/check_counts.py         # report problems, exit 1 if any
    python3 scripts/check_counts.py --fix   # rewrite the counts in place
    python3 scripts/check_counts.py --fix --phrases   # new non-"Phrases" category goes under Spinner Phrases

Counts live in three places: each category heading, its table-of-contents
entry, and the totals in the intro. --fix updates all three, and adds a
missing table-of-contents entry (under Spinner Phrases if the name ends in
"Phrases" or --phrases is given, otherwise under Spinner Verbs).

Each `| Verb |` table is followed
by a collapsed "Copy as list" block holding the same entries as quoted
strings, ready to paste into settings.json. --fix regenerates these too.
"""
import json
import re
import sys
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"

BUILT_HEADING = re.compile(r"^## Built-in Default Verbs \((\d+)\)$")
SEPARATOR = re.compile(r"^\|[\s|:-]+\|$")
HEADING = re.compile(r"^### (.+) \((\d+)\)$")
TOC = re.compile(r"^- \[(.+) \((\d+)\)\]\(#(.+)\)$")


def slug(title):
    """GitHub's anchor for a heading."""
    return re.sub(r"[^a-z0-9 \-]", "", title.lower()).replace(" ", "-")


def is_verb_row(lines, i):
    """A table row that is not the header (the row just above the |---| line)."""
    if not lines[i].startswith("| "):
        return False
    return not (i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]))


def cell_text(row):
    """The entry as the rendered table shows it: code spans and \\| unescaped."""
    cell = row.strip()[1:-1].strip()
    cell = re.sub(r"(`+) ?(.+?) ?\1", r"\2", cell)
    return cell.replace("\\|", "|")


def copy_block(verbs):
    quoted = ",\n".join(json.dumps(v, ensure_ascii=False) for v in verbs)
    return ["<details>", "<summary>Copy as list</summary>", "", "```",
            *quoted.split("\n"), "```", "", "</details>"]


def sync_copy_lists(lines):
    """Add or refresh the "Copy as list" block after every | Verb | table.

    Returns the updated lines and the headings whose block was missing or stale.
    """
    out, stale, heading = [], [], None
    i = 0
    while i < len(lines):
        if lines[i].startswith("#"):
            heading = lines[i].lstrip("# ")
        if not (lines[i] == "| Verb |" and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1])):
            out.append(lines[i])
            i += 1
            continue
        end = i + 2
        while end < len(lines) and lines[end].startswith("| "):
            end += 1
        out += lines[i:end]
        want = copy_block([cell_text(r) for r in lines[i + 2:end]])
        # An existing block sits after one blank line; replace it whole.
        have_at = end + 1
        if lines[end:have_at + 2] == ["", "<details>", "<summary>Copy as list</summary>"]:
            close = lines.index("</details>", have_at)
            have, i = lines[have_at:close + 1], close + 1
        else:
            have, i = None, end
        if have != want:
            stale.append(heading)
        out += [""] + want
    return out, stale


def main():
    fix = "--fix" in sys.argv
    lines = README.read_text().split("\n")
    problems = []

    # The built-in defaults are one comma-separated paragraph.
    built_in = None
    for i, l in enumerate(lines):
        m = BUILT_HEADING.match(l)
        if m:
            para = next(x for x in lines[i + 1:] if x.strip() and not x.startswith("These "))
            built_in = len([v for v in para.split(",") if v.strip()])
            if int(m.group(1)) != built_in:
                problems.append(f"Built-in heading says {m.group(1)}, list has {built_in}")
                lines[i] = f"## Built-in Default Verbs ({built_in})"
    if built_in is None:
        print("Built-in Default Verbs section not found")
        return 1

    # Category sections start after the last table-of-contents entry.
    toc_rows = [i for i, l in enumerate(lines) if TOC.match(l)]
    body_start = toc_rows[-1] + 1

    actual = {}
    current = None
    for i in range(body_start, len(lines)):
        m = HEADING.match(lines[i])
        if m:
            current = m.group(1)
            if current in actual:
                problems.append(f"duplicate category: {current}")
            actual[current] = 0
        elif current and is_verb_row(lines, i):
            actual[current] += 1

    seen = {name: set() for name in actual}
    current = None
    for i in range(body_start, len(lines)):
        m = HEADING.match(lines[i])
        if m:
            current = m.group(1)
            declared = int(m.group(2))
            if declared != actual[current]:
                problems.append(
                    f"{current}: heading says {declared}, table has {actual[current]}"
                )
                lines[i] = f"### {current} ({actual[current]})"
        elif current and is_verb_row(lines, i):
            verb = lines[i].strip("| ").strip()
            if verb in seen[current]:
                problems.append(f"{current}: duplicate verb '{verb}'")
            seen[current].add(verb)

    in_toc = set()
    for i in toc_rows:
        name, declared, anchor = TOC.match(lines[i]).groups()
        in_toc.add(name)
        if name not in actual:
            problems.append(f"table of contents lists unknown category: {name}")
            continue
        want = f"- [{name} ({actual[name]})](#{slug(f'{name} ({actual[name]})')})"
        if lines[i] != want:
            problems.append(f"table of contents entry out of date: {name}")
            lines[i] = want
    phrases_at = next(i for i, l in enumerate(lines) if l == "### Spinner Phrases")
    for name in actual:
        if name in in_toc:
            continue
        problems.append(f"missing from table of contents: {name}")
        # Names ending in "Phrases" go under Spinner Phrases; use --phrases
        # for any other category that belongs there.
        as_phrases = name.endswith("Phrases") or "--phrases" in sys.argv
        entry = f"- [{name} ({actual[name]})](#{slug(f'{name} ({actual[name]})')})"
        rows = [i for i in toc_rows if (i > phrases_at) == as_phrases]
        after = [i for i in rows if TOC.match(lines[i]).group(1).casefold() > name.casefold()]
        at = after[0] if after else rows[-1] + 1
        lines.insert(at, entry)
        toc_rows = [i + (i >= at) for i in toc_rows] + [at]
        toc_rows.sort()
        phrases_at += phrases_at >= at

    additional = sum(actual.values())
    intro = {
        r"\*\*\d+ built-in defaults\*\*": f"**{built_in} built-in defaults**",
        r"the \d+ built-in defaults": f"the {built_in} built-in defaults",
        r"\*\*[\d,]+ spinner verbs\*\*": f"**{additional + built_in:,} spinner verbs**",
        r"\*\*[\d,]+ additional verbs\*\* across \d+ themed categories": (
            f"**{additional:,} additional verbs** across {len(actual)} themed categories"
        ),
    }
    for i in range(body_start):
        if BUILT_HEADING.match(lines[i]):
            continue
        for pattern, want in intro.items():
            found = re.search(pattern, lines[i])
            if found and found.group(0) != want:
                problems.append(f"intro totals out of date: '{found.group(0)}' should be '{want}'")
                lines[i] = re.sub(pattern, want, lines[i])

    lines, stale = sync_copy_lists(lines)
    problems += [f"copy list out of date: {h}" for h in stale]

    if not problems:
        print(f"OK: {len(actual)} categories, {additional:,} additional verbs.")
        return 0
    for p in problems:
        print(p)
    if fix:
        README.write_text("\n".join(lines))
        print("\nCounts and copy lists rewritten. Re-run without --fix to confirm.")
        return 0
    print("\nRun `python3 scripts/check_counts.py --fix` to update them.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
