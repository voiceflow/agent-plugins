"""Check that packaged Markdown names only real MCP tools, CLI commands, skills, and files.

The surface snapshot comes from scripts/refresh_surface.py. The account MCP serves v3
tool names: the operation `<operation>` of the snapshot tool `voiceflow_<group>` is the
v3 tool `vf_<group>_<operation>`, and v3 adds the tools in V3_META_TOOLS. A `vf_*` name
passes only when v3 serves it, so an operation the MCP always refuses does not pass.
An older `voiceflow_<group>.<operation>` name never passes, because v3 does not serve it.
Every problem is reported as `path:line: reason`, so one run lists everything to fix.

Each skill must work when it is installed alone, so no file in a skill folder may refer to
a path outside that folder. Skills name each other instead, as in "the `voiceflow-wiring`
skill". The check reads Markdown links, images, reference definitions, and `<...>` targets,
and also paths written in code or plain text, in every file of every skill.
"""
import fnmatch
import json
from pathlib import Path
from urllib.parse import unquote
import re
import unicodedata

SURFACE = Path("tests/fixtures/voiceflow-surface.json")
# Tools v3 serves that are not operations of the snapshot. Search, the two callers, and the docs tools came
# with voiceflow/creator-app#24625 and COR-16000. The callers are listed only on a `dynamic=true` connection.
V3_META_TOOLS = frozenset({
    "vf_describe_operations", "vf_get_started", "vf_skill_list", "vf_skill_load",
    "vf_search_operations", "vf_call_read_operation", "vf_call_write_operation",
    "vf_docs_ask", "vf_docs_search", "vf_docs_read_page",
})
V3_TOKEN = re.compile(r"(?<![\w{])vf_[a-z0-9_*]*[a-z0-9*]")
INTERNAL_NAMES = re.compile(
    r"\b(?:describe_operations|audit_wiring|propose_test|skill_read"
    r"|request_(?:secret|integration|mcp_server|phone_number)|grep_transcripts"
    r"|get_debug_transcript|get_transcript_from_url|diff_environments|check_function"
    r"|wait_for_test_runs|ask_question|set_plan|clear_plan|show_[a-z_]+|Atlas|GLM)\b"
    r"|\b(?i:safe mode|autonomous mode)\b")
# Markdown link destinations: inline links and images, with an optional `<...>` target and title,
# and reference definitions. A footnote (`[^1]: text`) is not a definition.
INLINE_LINK = re.compile(
    r"!?\[(?:[^\[\]\\]|\\.|\[(?:[^\[\]\\]|\\.)*\])*\]"
    r"\(\s*(<[^<>\n]*>|[^\s()<>]*(?:\([^\s()<>]*\)[^\s()<>]*)*)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\)))?\s*\)")
DEFINITION = re.compile(r"^ {0,3}\[(?!\^)(?:[^\[\]\\]|\\.)+\]:(?!:)[ \t]*\n?[ \t]*(<[^<>\n]*>|[^\s<>]+)", re.M)
URI_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]+:")
# Path-shaped text in code, prose, and scripts. URLs are blanked out before these run.
URL = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]+://[^\s<>`'\")\]]*|\bmailto:[^\s<>`'\")\]]+")
PATH_CHARS = r"[^\s`'\"()<>\[\]{}|,;*]"
NOT_IN_PATH = r"(?<![\w.~$%/\\-])"
DOT_PATH = re.compile(NOT_IN_PATH + r"\.{1,2}/" + PATH_CHARS + "*")
REPO_PATH = re.compile(NOT_IN_PATH + r"(?:\./)?(voiceflow/)?skills/([A-Za-z0-9][\w.-]*)" + PATH_CHARS + "*")
SKILL_PATH = re.compile(NOT_IN_PATH + r"(voiceflow(?:-[a-z0-9]+)*)/(?:SKILL\.md|references/|scripts/|assets/|LICENSE)"
                        + PATH_CHARS + "*")
ABSOLUTE_PATH = re.compile(r"(?<![\w.$%-])(?:~|\$\w+|\$\{\w+\}|%\w+%|[A-Za-z]:)?[/\\]" + PATH_CHARS + "+")
TRAILING = ".,:;!?"
# Path references that may leave their skill folder: (file below voiceflow/skills, exact path text).
# Keep this list tiny, and say for each entry why a skill installed alone still works.
OUTSIDE_SKILL_ALLOWED = {
    # scripts/build.py publishes this guide on the website for chat assistants. They have no skill
    # loader and reach the entry skill only through this link, which the build rewrites to a bundle
    # path. Where the entry skill is not installed, the guide still works through its own links.
    ("voiceflow-setup/references/setup.md", "../../voiceflow/SKILL.md"),
}
HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*")
HTML_ANCHOR = re.compile(r"<a\s+(?:[^>]*?\s)?(?:id|name)=\"([^\"]+)\"", re.I)
FENCE = re.compile(r"\s*(`{3,}|~{3,})")
TOOL_SPAN = re.compile(r"(voiceflow_[a-z0-9_]+)(?:\.([a-z][a-z0-9_]*))?(?![\w.])")
OPERATION_SPAN = re.compile(r"[a-z][a-z0-9_]*")
OPERATION_GAP = re.compile(r"\s*(?:/\s*|,?\s*operation\s+)?")
SKILL_SPAN = re.compile(r"voiceflow-[a-z0-9][a-z0-9-]*")
MD_PATH_SPAN = re.compile(r"(?:\.{1,2}/)*[\w.-]+(?:/[\w.-]+)+\.md")
TOKEN = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'|\S+")
COMMAND_WORD = re.compile(r"[a-z][a-z0-9-]*")
FLAG = re.compile(r"--[a-z0-9][a-z0-9-]*|-[A-Za-z]")
SHELL_SEPARATOR = re.compile(r"&&|\|\||\$\(|[;|()]")
CLI_PREFIX = re.compile(r"\bCLI\s+$")
SKILL_BEFORE = re.compile(r"\bskills?\s+$", re.I)
SKILL_AFTER = re.compile(r"\s*skills?\b", re.I)
BACKTICKS = re.compile(r"`+")


def load_surface(root):
    return json.loads((root / SURFACE).read_text(encoding="utf-8"))


def v3_slugs(tools):
    """Map each v3 tool name to its snapshot slug, `vf_<group>_<operation>` to `voiceflow_<group>.<operation>`.

    Both halves can hold underscores, so a name goes to the longest group first, as the server names them.
    """
    slugs = {}
    for tool in sorted(tools, key=len, reverse=True):
        group = tool[len("voiceflow_"):]
        for operation in sorted(tools[tool]):
            slugs.setdefault(f"vf_{group}_{operation}", f"{tool}.{operation}")
    return slugs


def v3_names(surface):
    """Every tool name the account MCP v3 serves: each operation the MCP does not always refuse, and the meta tools."""
    refused = surface["mcp"]["refused"]
    return frozenset(name for name, slug in v3_slugs(surface["mcp"]["tools"]).items()
                     if (refused.get(slug) or {}).get("when") != "always") | V3_META_TOOLS


def parse(text):
    """Split Markdown into prose blocks, fenced command lines, and headings, keeping line numbers."""
    prose, fenced, headings, block = [], [], [], []
    fence, pending = None, None

    def flush():
        if block:
            prose.append((block[0][0], "\n".join(content for _, content in block)))
            block.clear()

    for number, line in enumerate(text.splitlines(), 1):
        opener = FENCE.match(line)
        if opener and opener.group(1)[0] == "`" and "`" in line[opener.end():]:
            opener = None
        if fence:
            if opener and opener.group(1)[0] == fence[0] and len(opener.group(1)) >= len(fence) \
                    and not line[opener.end():].strip():
                fence = None
                if pending:
                    fenced.append(pending)
                    pending = None
                continue
            stripped = line.rstrip()
            if pending:
                pending = (pending[0], pending[1] + " " + stripped.strip())
            else:
                pending = (number, stripped)
            if stripped.endswith(("\\", " `")):
                pending = (pending[0], pending[1].rstrip("\\`").rstrip())
            else:
                fenced.append(pending)
                pending = None
            continue
        if opener:
            flush()
            fence = opener.group(1)
            continue
        if line.strip():
            block.append((number, line))
            heading = HEADING.fullmatch(line)
            if heading:
                headings.append(heading.group(2) or "")
        else:
            flush()
    flush()
    if pending:
        fenced.append(pending)
    return prose, fenced, headings


def code_spans(text):
    """Yield (start, end, content) for each CommonMark code span in a prose block."""
    position = 0
    while True:
        opening = BACKTICKS.search(text, position)
        if not opening:
            return
        if opening.start() and text[opening.start() - 1] == "\\":
            position = opening.end()
            continue
        run = opening.group()
        closing = re.compile(rf"(?<!`){run}(?!`)").search(text, opening.end())
        if not closing:
            position = opening.end()
            continue
        content = text[opening.end():closing.start()].replace("\n", " ")
        if len(content) > 1 and content.startswith(" ") and content.endswith(" ") and content.strip():
            content = content[1:-1]
        yield opening.start(), closing.end(), content
        position = closing.end()


def prose_spans(prose):
    """Yield (line, content, adjacent span, command text, names a skill) for every code span.

    The adjacent span is the next span when only whitespace, `/`, or `, operation` separates
    them, as in MCP `voiceflow_agent` `get`. A span right after the word CLI reads as a
    `vf` command, as in CLI `agent get`. A span next to the word skill names a skill.
    """
    for start, block in prose:
        spans = list(code_spans(block))
        for index, (offset, end, content) in enumerate(spans):
            following = spans[index + 1] if index + 1 < len(spans) else None
            adjacent = following[2] if following and OPERATION_GAP.fullmatch(block[end:following[0]]) else None
            command = content
            if CLI_PREFIX.search(block[:offset]) and not re.match(r"\$?\s*vf\b", content):
                command = "vf " + content
            named_skill = bool(SKILL_BEFORE.search(block[:offset]) or SKILL_AFTER.match(block, end))
            yield start + block.count("\n", 0, offset), content, adjacent, command, named_skill


def edit_distance(first, second):
    previous = list(range(len(second) + 1))
    for index, char in enumerate(first, 1):
        current = [index]
        for other_index, other in enumerate(second, 1):
            current.append(min(previous[other_index] + 1, current[-1] + 1,
                               previous[other_index - 1] + (char != other)))
        previous = current
    return previous[-1]


def without_code(text):
    """Blank out code spans so links and names inside them are not read as Markdown."""
    for start, end, _ in code_spans(text):
        text = text[:start] + re.sub(r"[^\n]", " ", text[start:end]) + text[end:]
    return text


def link_destinations(masked):
    """Yield (offset, destination) for each inline link, image, and reference definition in a prose block.

    Pass the block through without_code first. Angle brackets around a destination are removed.
    """
    for pattern in (INLINE_LINK, DEFINITION):
        for match in pattern.finditer(masked):
            destination = match.group(1)
            if destination.startswith("<") and destination.endswith(">"):
                destination = destination[1:-1].strip()
            if destination:
                yield match.start(1), destination


def is_url(destination):
    return bool(URI_SCHEME.match(destination))


def skill_folder(skills, path):
    """Return the skill folder below skills that holds path, or None for a file outside every skill."""
    if not path.is_relative_to(skills):
        return None
    parts = path.relative_to(skills).parts
    return skills / parts[0] if len(parts) > 1 else None


def local_targets(path, skill):
    """Yield every local path a Markdown file links, or names as a backticked `.md` path.

    A link resolves from the file's folder. A backticked path resolves from the file's folder and
    from the skill folder, as the reference check reads it, so both candidates are yielded.
    """
    prose, _, _ = parse(path.read_text(encoding="utf-8"))
    for _, block in prose:
        for _, destination in link_destinations(without_code(block)):
            target = destination.partition("#")[0]
            if target and not is_url(destination):
                yield (path.parent / unquote(target)).resolve()
        for _, _, content in code_spans(block):
            if MD_PATH_SPAN.fullmatch(content):
                for base in (path.parent, skill):
                    yield (base / content).resolve()


def cli_invocations(text):
    """Yield (command path, flags) for each `vf` command in a code span or a shell line."""
    for segment in SHELL_SEPARATOR.split(text):
        tokens = TOKEN.findall(segment)
        if tokens[:1] == ["$"]:
            tokens = tokens[1:]
        if tokens[:1] != ["vf"]:
            continue
        words = []
        for token in tokens[1:]:
            if not COMMAND_WORD.fullmatch(token):
                break
            words.append(token)
        flags = []
        for token in tokens[1 + len(words):]:
            name = token.split("=", 1)[0]
            if FLAG.fullmatch(name):
                flags.append(name)
        yield " ".join(words), flags


def slug(heading):
    """Return GitHub's anchor for a heading's text, before duplicate numbering."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = re.sub(r"<[^>]+>", "", text).replace("`", "").replace("*", "").strip().lower()
    text = "".join(char for char in text
                   if char in " -_" or unicodedata.category(char)[0] in "LNM")
    return text.replace(" ", "-")


def anchors(text):
    _, _, headings = parse(text)
    found, counts = set(), {}
    for heading in headings:
        base = slug(heading)
        anchor = base
        while anchor in found:
            counts[base] = counts.get(base, 0) + 1
            anchor = f"{base}-{counts[base]}"
        found.add(anchor)
    found.update(HTML_ANCHOR.findall(text))
    return found


class Checker:
    def __init__(self, root, surface, skill_names=None):
        """Check root/voiceflow. Pass skill_names to accept names of skills that are not in this tree,
        as when one skill is checked alone."""
        self.root = root.resolve()
        self.plugin = self.root / "voiceflow"
        self.skills = self.plugin / "skills"
        self.tools = {tool: set(names) for tool, names in surface["mcp"]["tools"].items()}
        self.refused = surface["mcp"]["refused"]
        self.slugs = v3_slugs(self.tools)
        self.served = v3_names(surface)
        self.commands = set(surface["cli"]["commands"])
        self.groups = {" ".join(command.split()[:size]) for command in self.commands
                       for size in range(1, len(command.split()))}
        self.skill_names = set(skill_names) if skill_names is not None else {
            path.parent.name for path in self.skills.glob("*/SKILL.md")}
        self.anchor_cache = {}

    def files(self):
        return sorted(self.plugin.rglob("*.md"), key=lambda path: path.as_posix())

    def other_skill_files(self):
        """Every file in a skill folder that is not Markdown, such as a script, for the path check."""
        return sorted((path for path in self.skills.rglob("*") if path.is_file() and path.suffix != ".md"
                       and "__pycache__" not in path.parts and skill_folder(self.skills, path)),
                      key=lambda path: path.as_posix())

    def check(self):
        problems = []
        for path in self.files():
            problems.extend(self.check_file(path))
        for path in self.other_skill_files():
            problems.extend(self.check_other_file(path))
        return problems

    def reporter(self, path):
        label = path.relative_to(self.root).as_posix()
        problems = []

        def report(number, reason):
            problems.append((number, f"{label}:{number}: {reason}"))

        return problems, report

    def check_other_file(self, path):
        path = path.resolve()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return []
        problems, report = self.reporter(path)
        self.check_paths(path, text, set(), report)
        return [message for _, message in sorted(problems, key=lambda item: item[0])]

    def check_file(self, path):
        path = path.resolve()
        text = path.read_text(encoding="utf-8")
        prose, fenced, _ = parse(text)
        problems, report = self.reporter(path)

        for number, line in enumerate(text.splitlines(), 1):
            for match in INTERNAL_NAMES.finditer(line):
                report(number, f"internal name \"{match.group()}\" is not public")
            for match in V3_TOKEN.finditer(line):
                self.check_v3_name(match.group(), number, report)
        for number, content, adjacent, command, named_skill in prose_spans(prose):
            self.check_span(path, content, adjacent, command, named_skill, number, report)
        linked = set()
        for start, block in prose:
            masked = without_code(block)
            for offset, destination in link_destinations(masked):
                linked.add(destination)
                self.check_link(path, destination, start + masked.count("\n", 0, offset), report)
        for number, line in fenced:
            self.check_commands(line, number, report)
        self.check_paths(path, text, linked, report)
        return [message for _, message in sorted(problems, key=lambda item: item[0])]

    def allowed_outside(self, path, reference):
        return (path.relative_to(self.skills).as_posix(), reference) in OUTSIDE_SKILL_ALLOWED

    def check_paths(self, path, text, linked, report):
        """Report path text in a skill file that points outside its skill folder.

        A relative path fails when it resolves outside the skill folder. A path rooted at the
        repository or the skills folder fails when it names another skill. An absolute path fails
        when it points into the plugin or into another skill's installed folder. Link destinations
        that the link check already read are skipped, so one link gives one problem.
        """
        skill = skill_folder(self.skills, path)
        if skill is None:
            return

        def outside(number, token, reason):
            if token not in linked and not self.allowed_outside(path, token):
                report(number, f"{reason} \"{token}\"")

        for number, line in enumerate(text.splitlines(), 1):
            line = URL.sub(lambda match: " " * len(match.group()), line)
            for match in DOT_PATH.finditer(line):
                token = match.group().rstrip(TRAILING)
                relative = unquote(token.partition("#")[0])
                target = (path.parent / relative).resolve()
                leaves = not target.is_relative_to(skill)
                if not leaves and not target.exists():
                    leaves = not (skill / relative).resolve().is_relative_to(skill)
                if leaves:
                    outside(number, token, "path leaves the skill folder")
            for match in REPO_PATH.finditer(line):
                rooted, name = match.group(1), match.group(2)
                if name != skill.name and (rooted or name in self.skill_names):
                    outside(number, match.group().rstrip(TRAILING), "path points into another skill")
            for match in SKILL_PATH.finditer(line):
                if match.group(1) in self.skill_names and match.group(1) != skill.name:
                    outside(number, match.group().rstrip(TRAILING), "path points into another skill")
            for match in ABSOLUTE_PATH.finditer(line):
                token = match.group().rstrip(TRAILING)
                normalized = token.replace("\\", "/")
                names = set(re.findall(r"(?:^|/)skills/([\w.-]+)", normalized))
                if ("voiceflow/skills/" in normalized or normalized.startswith(self.plugin.as_posix() + "/")
                        or any(name in self.skill_names and name != skill.name for name in names)):
                    outside(number, token, "absolute path points into the plugin or another skill")

    def check_span(self, path, content, adjacent, command, named_skill, number, report):
        tool = TOOL_SPAN.match(content)
        if tool:
            operation = tool.group(2)
            if operation is None and adjacent and OPERATION_SPAN.fullmatch(adjacent) \
                    and not adjacent.startswith("voiceflow_"):
                operation = adjacent
            self.check_operation(tool.group(1), operation, number, report)
        if SKILL_SPAN.fullmatch(content) and content not in self.skill_names and (
                named_skill or any(edit_distance(content, name) <= 2 for name in self.skill_names)):
            report(number, f"unknown skill \"{content}\"")
        if MD_PATH_SPAN.fullmatch(content):
            self.check_md_path(path, content, number, report)
        self.check_commands(command, number, report)

    def check_operation(self, tool, operation, number, report):
        if tool not in self.tools:
            report(number, f"unknown MCP tool \"{tool}\"")
            return
        group = tool[len("voiceflow_"):]
        if operation is None:
            report(number, f"MCP v3 has no tool \"{tool}\"; name one operation's tool, \"vf_{group}_<operation>\"")
            return
        reference = f"{tool}.{operation}"
        if operation not in self.tools[tool]:
            report(number, f"unknown MCP operation \"{reference}\"")
            return
        refusal = self.refused.get(reference)
        if refusal and refusal["when"] == "always":
            command = f"; name the CLI command \"vf {refusal['cli']}\" instead" if refusal.get("cli") else ""
            report(number, f"MCP always refuses \"{reference}\"{command}")
            return
        report(number, f"MCP v3 has no tool \"{reference}\"; name \"vf_{group}_{operation}\" instead")

    def check_v3_name(self, name, number, report):
        if "*" in name:
            if not any(fnmatch.fnmatchcase(served, name) for served in self.served):
                report(number, f"no MCP v3 tool matches \"{name}\"")
            return
        if name in self.served:
            return
        refusal = self.refused.get(self.slugs.get(name, ""))
        if refusal and refusal["when"] == "always":
            command = f"; name the CLI command \"vf {refusal['cli']}\" instead" if refusal.get("cli") else ""
            report(number, f"MCP always refuses \"{name}\"{command}")
            return
        report(number, f"unknown MCP tool \"{name}\"")

    def check_commands(self, text, number, report):
        for command, _ in cli_invocations(text):
            if command and command not in self.commands and command not in self.groups:
                report(number, f"unknown CLI command \"vf {command}\"")

    def check_md_path(self, path, reference, number, report):
        relative = path.relative_to(self.skills).parts if path.is_relative_to(self.skills) else ()
        skill_root = self.skills / relative[0] if len(relative) > 1 else path.parent
        for base in (path.parent, skill_root):
            target = (base / reference).resolve()
            if target.is_relative_to(self.plugin) and target.is_file():
                return
        report(number, f"missing file \"{reference}\"")

    def check_link(self, path, link, number, report):
        if is_url(link):
            return
        target_text, _, anchor = link.partition("#")
        if target_text:
            target = (path.parent / unquote(target_text)).resolve()
            if not target.is_relative_to(self.plugin):
                report(number, f"link leaves the plugin \"{link}\"")
                return
            skill = skill_folder(self.skills, path)
            if skill and not target.is_relative_to(skill):
                if not self.allowed_outside(path, link):
                    report(number, f"link leaves the skill folder \"{link}\"; name the other skill instead")
                    return
                if not skill_folder(self.skills, target) or not skill_folder(self.skills, target).is_dir():
                    return  # An allowed link whose skill is not installed here, as when a skill is checked alone.
            if not target.is_file():
                report(number, f"missing link target \"{link}\"")
                return
        else:
            target = path
        if anchor and target.suffix == ".md" and unquote(anchor) not in self.anchors(target):
            report(number, f"missing anchor \"#{anchor}\" in {target.relative_to(self.root).as_posix()}")

    def anchors(self, path):
        if path not in self.anchor_cache:
            self.anchor_cache[path] = anchors(path.read_text(encoding="utf-8"))
        return self.anchor_cache[path]


def check_references(root, surface=None):
    """Return every reference problem under root/voiceflow as `path:line: reason` lines."""
    return Checker(root, surface if surface is not None else load_surface(root)).check()


def cli_uses(root):
    """Yield (path:line, command path, flags) for every `vf` command the packaged Markdown names."""
    root = root.resolve()
    for path in sorted((root / "voiceflow").rglob("*.md"), key=lambda path: path.as_posix()):
        prose, fenced, _ = parse(path.read_text(encoding="utf-8"))
        label = path.relative_to(root).as_posix()
        lines = [(number, command) for number, _, _, command, _ in prose_spans(prose)]
        for number, text in sorted(lines + fenced):
            for command, flags in cli_invocations(text):
                if command or flags:
                    yield f"{label}:{number}", command, flags
