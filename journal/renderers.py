import mistune
import re


MARKDOWNX_MARKDOWNIFY_FUNCTION = "journal.renderers.render_md"

_mistune_plugins = [
    "url",
    "strikethrough",
    "footnotes",
    "table",
    "mark",
    "superscript",
    "subscript",
    "math",
    "spoiler",
]
_markdown = mistune.create_markdown(plugins=_mistune_plugins)


def render_md(s):
    # s = "\n".join(
    #     [
    #         re.sub(r"^(\u2003+)", lambda s: "&emsp;" * len(s[0]), line)
    #         for line in s.split("\n")
    #     ]
    # )
    return _markdown(s)


def render_text(s):
    return mistune.html(s)
