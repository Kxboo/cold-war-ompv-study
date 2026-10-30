"""Build the dependency-free study reader and check local site links.

Run from any directory: python tools/build_site.py
Markdown chapters remain authoritative. The renderer intentionally supports this
repository's prose, tables, lists and fenced code, with a readable Mermaid-source
fallback. The three study diagrams have explicit semantic HTML layouts; their
source remains available in a disclosure. No remote scripts or raw HTML execute.
"""
from html import escape
from html.parser import HTMLParser
import math
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
REPO = 'https://github.com/Kxboo/cold-war-ompv-study'


def slug(text):
    return re.sub(r'[^\w\- ]', '', text.lower().replace('`', '')).replace(' ', '-')


def target_url(url):
    parsed = urlsplit(url)
    if parsed.scheme:
        return url if parsed.scheme in ('https', 'http', 'mailto') else '#'
    if url.startswith('#'):
        return url
    path, separator, fragment = url.partition('#')
    if path.endswith('.md') and Path(path).name[:2].isdigit():
        return Path(path).with_suffix('.html').name + (separator + fragment if separator else '')
    if path.startswith('../evidence/'):
        return '../data/' + path.removeprefix('../evidence/') + (separator + fragment if separator else '')
    if path.startswith('../assets/'):
        return path
    return REPO + '/blob/main/' + path.removeprefix('../') + (separator + fragment if separator else '')


def inline(text):
    tokens = []

    def keep(value):
        tokens.append(value)
        return f'\x00{len(tokens)-1}\x00'

    text = re.sub(r'`([^`]+)`', lambda m: keep('<code>' + escape(m[1]) + '</code>'), text)
    text = re.sub(r'!\[([^\]]*)\]\(([^\s)]+)\)',
                  lambda m: keep(f'<img src="{escape(target_url(m[2]), quote=True)}" alt="{escape(m[1], quote=True)}" loading="lazy">'), text)
    text = re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',
                  lambda m: keep(f'<a href="{escape(target_url(m[2]), quote=True)}">{escape(m[1])}</a>'), text)
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    # Links can contain code tokens from the initial pass. Restore inside-out.
    for _ in range(len(tokens) + 1):
        result = re.sub(r'\x00(\d+)\x00', lambda m: tokens[int(m[1])], text)
        if result == text:
            break
        text = result
    return text


def table_cells(line):
    return [cell.strip() for cell in re.split(r'\|(?=(?:[^`]*`[^`]*`)*[^`]*$)', line.strip().strip('|'))]


def render_flowchart(source):
    """Render the study's known DAGs, retaining source without executing Mermaid."""
    nodes = dict(re.findall(r'([A-Za-z][A-Za-z0-9_]*)\[([^\]]+)\]', source))
    edges = re.findall(r'([A-Za-z][A-Za-z0-9_]*)(?:\[[^\]]+\])?\s*-->\s*([A-Za-z][A-Za-z0-9_]*)', source)
    edge_set = set(edges)

    def node(key, extra=''):
        return f'<div class="flow-node {extra}">{escape(nodes[key])}</div>'

    def sequence(keys, class_name='flow-sequence'):
        return f'<ol class="{class_name}">' + ''.join(f'<li><span class="flow-node">{escape(nodes[key])}</span></li>' for key in keys) + '</ol>'

    capture = {('A', 'B'), ('B', 'C'), ('B', 'D'), ('C', 'E'), ('E', 'F'), ('F', 'G'), ('D', 'H'), ('H', 'I')}
    port = {('A', 'B'), ('A', 'C'), ('C', 'D'), ('B', 'E'), ('D', 'E'), ('C', 'F'), ('F', 'G')}
    body = caption = ''
    if edge_set == capture and all(key in nodes for key in 'ABCDEFGHI'):
        body = sequence(['A', 'B'], 'flow-entry')
        body += '<div class="flow-fork-label">Two export paths <span aria-hidden="true">↙ &nbsp; ↘</span></div>'
        body += '<div class="flow-branches">'
        body += f'<section class="flow-branch"><h4>{escape(nodes["C"])}</h4>{sequence(["E", "F", "G"])}</section>'
        body += f'<section class="flow-branch archive-branch"><h4>{escape(nodes["D"])}</h4>{sequence(["H", "I"])}</section></div>'
        caption = 'Capture lifecycle: the ordinary bake and the source archive follow separate paths.'
    elif edge_set == port and all(key in nodes for key in 'ABCDEFG'):
        body = node('A', 'flow-origin')
        body += '<div class="flow-fork-label">Reference and candidate <span aria-hidden="true">↙ &nbsp; ↘</span></div>'
        body += '<div class="flow-branches comparison-branches">'
        body += '<section class="flow-branch"><h4>Reference execution</h4>' + sequence(['B']) + '</section>'
        body += '<section class="flow-branch"><h4>Translated candidate</h4>' + sequence(['C', 'D']) + '</section></div>'
        body += '<div class="flow-merge"><span aria-hidden="true">↘ &nbsp; ↙</span>' + node('E', 'flow-result') + '</div>'
        body += '<div class="flow-offshoot"><p>Separate branch from translation</p>' + sequence(['F', 'G'], 'flow-entry') + '</div>'
        caption = 'Port experiment: compare aligned reference and candidate outputs; validate BO3 integration separately.'
    elif edges and len(edges) == len(nodes) - 1 and len(edge_set) == len(edges):
        targets = {target for _, target in edges}
        starts = set(nodes) - targets
        next_node = dict(edges)
        if len(starts) == 1 and len(next_node) == len(edges):
            chain = [starts.pop()]
            while chain[-1] in next_node and next_node[chain[-1]] not in chain:
                chain.append(next_node[chain[-1]])
            if len(chain) == len(nodes):
                body = '<ol class="flow-linear">' + ''.join(f'<li><span class="flow-number">{index+1:02}</span><span>{escape(nodes[key])}</span></li>' for index, key in enumerate(chain)) + '</ol>'
                caption = 'Material composition, in sequence. Virtual-texture storage, geometry and final lighting are separate systems.'
    if not body:
        return '<pre class="diagram-source"><code>' + escape(source) + '</code></pre><p class="diagram-caption">Flowchart source · arrows show the process direction.</p>'
    return '<figure class="flow-diagram"><figcaption>' + caption + '</figcaption>' + body + '</figure><details class="flow-source"><summary>View diagram source</summary><pre><code>' + escape(source) + '</code></pre></details>'


def render_markdown(source):
    lines = source.splitlines()
    output, headings, used_slugs = [], [], {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith('```'):
            language = line[3:].strip()
            block = []
            index += 1
            while index < len(lines) and not lines[index].startswith('```'):
                block.append(lines[index])
                index += 1
            index += 1
            if language == 'mermaid':
                output.append(render_flowchart('\n'.join(block)))
            else:
                output.append(f'<pre class="code-block"><code>{escape(chr(10).join(block))}</code></pre>')
            continue
        heading = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading:
            level, title = len(heading[1]), heading[2]
            anchor = slug(title)
            count = used_slugs.get(anchor, 0)
            used_slugs[anchor] = count + 1
            if count:
                anchor += f'-{count}'
            headings.append((level, title, anchor))
            output.append(f'<h{level} id="{escape(anchor)}">{inline(title)}</h{level}>')
            index += 1
            continue
        if index + 1 < len(lines) and '|' in line and re.match(r'^\s*\|?\s*:?-{3}', lines[index + 1]):
            headers = table_cells(line)
            alignments = table_cells(lines[index + 1])
            index += 2
            rows = []
            while index < len(lines) and lines[index].strip() and '|' in lines[index]:
                rows.append(table_cells(lines[index]))
                index += 1
            output.append('<div class="table-scroll"><table><thead><tr>')
            for column, cell in enumerate(headers):
                style = ' style="text-align:right"' if column < len(alignments) and alignments[column].endswith(':') else ''
                output.append(f'<th scope="col"{style}>{inline(cell)}</th>')
            output.append('</tr></thead><tbody>')
            for row in rows:
                output.append('<tr>')
                for column, cell in enumerate(row):
                    style = ' style="text-align:right"' if column < len(alignments) and alignments[column].endswith(':') else ''
                    output.append(f'<td{style}>{inline(cell)}</td>')
                output.append('</tr>')
            output.append('</tbody></table></div>')
            continue
        item = re.match(r'^(\s*)([-*]|\d+\.)\s+(.+)', line)
        if item:
            ordered = item[2][0].isdigit()
            tag = 'ol' if ordered else 'ul'
            output.append(f'<{tag}>')
            while index < len(lines):
                item = re.match(r'^(\s*)([-*]|\d+\.)\s+(.+)', lines[index])
                if not item or item[2][0].isdigit() != ordered:
                    break
                contents = [item[3]]
                index += 1
                while index < len(lines) and lines[index].startswith('  ') and not re.match(r'^\s*([-*]|\d+\.)\s+', lines[index]):
                    contents.append(lines[index].strip())
                    index += 1
                output.append('<li>' + inline(' '.join(contents)) + '</li>')
            output.append(f'</{tag}>')
            continue
        if line.startswith('> '):
            block = []
            while index < len(lines) and lines[index].startswith('> '):
                block.append(lines[index][2:])
                index += 1
            rendered, _ = render_markdown('\n'.join(block))
            output.append('<blockquote>' + rendered + '</blockquote>')
            continue
        if re.fullmatch(r'\s*([-*_])\1{2,}\s*', line):
            output.append('<hr>')
            index += 1
            continue
        paragraph = [line]
        index += 1
        while index < len(lines) and lines[index].strip():
            if re.match(r'^(#{1,6}\s|```|> |\s*[-*]\s|\s*\d+\.\s)', lines[index]):
                break
            paragraph.append(lines[index])
            index += 1
        output.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(output), headings


def make_art():
    """Original procedural wireframe illustration. No captured assets."""
    width, height = 720, 560
    points = {}
    size = 13
    for y in range(size):
        for x in range(size):
            ridge = 51 * math.exp(-((x - 6) ** 2 / 13 + (y - 4) ** 2 / 15))
            ridge += 24 * math.exp(-((x - 3) ** 2 / 5 + (y - 9) ** 2 / 8))
            ripple = 7 * math.sin(x * .67 + y * .2) * math.cos(y * .52)
            points[x, y] = (360 + (x - y) * 25, 113 + (x + y) * 13.5 - ridge - ripple)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Synthetic terrain and categorical control samples</title>',
           '<desc id="desc">An original procedural height field, with a wireframe, categorical control markers, and a highlighted four-sample footprint. This is an illustration, not captured game terrain.</desc>',
           '<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#cbd1bf" stroke-width=".5" opacity=".35"/></pattern></defs>',
           '<rect x="25" y="30" width="670" height="480" fill="url(#grid)"/>',
           '<path d="M60 304 360 468 660 304M360 468v31M60 304v31M660 304v31" fill="none" stroke="#bdc4ae" stroke-width=".8" stroke-dasharray="3 5"/>']
    for diagonal in range(2 * size - 2):
        for x in range(size - 1):
            y = diagonal - x
            if not 0 <= y < size - 1:
                continue
            corners = [points[x, y], points[x + 1, y], points[x + 1, y + 1], points[x, y + 1]]
            is_warm = x >= 7 or (x >= 4 and y < 4)
            fill = '#d9bd91' if is_warm else '#b7c0a4'
            if x > 8 and y > 6:
                fill = '#c4c3a6'
            polygon = ' '.join(f'{px:.2f},{py:.2f}' for px, py in corners)
            svg.append(f'<polygon points="{polygon}" fill="{fill}" fill-opacity=".75" stroke="#78876b" stroke-width=".6"/>')
            svg.append(f'<path d="M{corners[0][0]:.2f} {corners[0][1]:.2f}L{corners[2][0]:.2f} {corners[2][1]:.2f}" stroke="#78876b" stroke-width=".3" opacity=".45"/>')
    for y in range(1, size - 1, 2):
        for x in range(1, size - 1, 2):
            px, py = points[x, y]
            fill = '#bb7541' if x >= 7 or (x >= 4 and y < 4) else '#4f6647'
            svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="3" fill="{fill}" stroke="#f5f3ec" stroke-width="1.1"/>')
    cell = [points[5, 5], points[7, 5], points[7, 7], points[5, 7]]
    svg.append('<polygon points="' + ' '.join(f'{px:.2f},{py:.2f}' for px, py in cell) + '" fill="#e57b3c" fill-opacity=".16" stroke="#ac4f28" stroke-width="1.6"/>')
    for (px, py), label in zip(cell, ['007', '007', '007', '002']):
        svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4.5" fill="#f4efdd" stroke="#a94b27" stroke-width="1.5"/>')
        svg.append(f'<text x="{px+7:.2f}" y="{py-7:.2f}" font-family="Consolas,monospace" font-size="9" fill="#7a3a22">{label}</text>')
    cx, cy = sum(p[0] for p in cell) / 4, sum(p[1] for p in cell) / 4
    svg += [f'<path d="M{cx:.2f} {cy-5:.2f}V54H502" fill="none" stroke="#a94b27" stroke-width=".8"/>',
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3" fill="#a94b27"/>',
            '<text x="510" y="51" font-family="Consolas,monospace" font-size="9" letter-spacing="1" fill="#a94b27">FOUR SAMPLES</text>',
            '<text x="510" y="67" font-family="Consolas,monospace" font-size="8" fill="#64705b">one shading location</text>',
            '<path d="M110 326v98h100" fill="none" stroke="#7c886e" stroke-width=".8"/>',
            '<text x="217" y="428" font-family="Consolas,monospace" font-size="9" fill="#58674d">CATEGORICAL CONTROL FIELD</text>',
            '<text x="34" y="494" font-family="Consolas,monospace" font-size="8" letter-spacing="1" fill="#79836c">SYNTHETIC GEOMETRY / NOT TO SCALE</text>',
            '<path d="M610 468h38m-19-19v38" stroke="#7e896f" stroke-width=".8"/><text x="616" y="507" font-family="Consolas,monospace" font-size="8" fill="#79836c">XY</text>', '</svg>']
    (SITE / 'assets' / 'terrain-field.svg').write_text('\n'.join(svg) + '\n', encoding='utf-8')


def page(path, content, headings, chapters):
    title = headings[0][1] if headings else path.stem
    navigation = ''.join(f'<a href="{source.stem}.html"' + (' aria-current="page"' if source == path else '') + f'>{source.stem[:2]} &nbsp; {escape(chapter_title)}</a>' for source, chapter_title in chapters)
    toc = ''.join(f'<a href="#{escape(anchor)}">{escape(text)}</a>' for level, text, anchor in headings if level == 2)
    position = [source for source, _ in chapters].index(path)
    previous = chapters[position - 1] if position else None
    following = chapters[position + 1] if position + 1 < len(chapters) else None
    pager = ''
    if previous:
        pager += f'<a href="{previous[0].stem}.html"><span>← PREVIOUS CHAPTER</span>{escape(previous[1])}</a>'
    if following:
        pager += f'<a href="{following[0].stem}.html"><span>NEXT CHAPTER →</span>{escape(following[1])}</a>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#f5f3ec"><meta name="description" content="{escape(title, quote=True)} — the Cold War OMPV research study, with source references and explicit evidence boundaries."><title>{escape(title)} — Cold War OMPV</title><link rel="icon" href="../assets/mark.svg" type="image/svg+xml"><link rel="stylesheet" href="../styles.css"></head>
<body><a class="skip-link" href="#article">Skip to content</a>
<header class="site-header"><a class="wordmark" href="../" aria-label="SuperTerrain Field Notes home"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="M2 16 16 2l14 14-14 14Z"/><path d="m2 16 14 4 14-4M16 2v18l-8 4"/></svg><span>SUPERTERRAIN<small>FIELD NOTES / 001</small></span></a><nav aria-label="Main navigation"><a href="../#explorer">Explorer</a><a href="../#study">The study</a><a class="nav-repo" href="{REPO}">GitHub <span aria-hidden="true">↗</span></a></nav></header>
<div class="reader-header wrap"><a href="../#study">← All field notes</a><p class="eyebrow">CHAPTER {path.stem[:2]} / COLD WAR OMPV</p></div>
<main class="reader-layout wrap"><aside class="reader-sidebar" aria-label="Study navigation"><p class="eyebrow">THE COMPLETE STUDY</p><nav aria-label="Chapters">{navigation}</nav><div class="toc"><p class="eyebrow">ON THIS PAGE</p><nav aria-label="On this page">{toc}</nav></div><details class="reader-mobile-nav"><summary>Chapters &amp; this page</summary><nav aria-label="Mobile chapters">{navigation}</nav><div class="toc"><nav aria-label="Mobile page contents">{toc}</nav></div></details></aside>
<article id="article" class="article-body">{content}<a class="source-link" href="{REPO}/blob/main/docs/{quote(path.name)}">Read this chapter’s Markdown source ↗</a><nav class="chapter-pager" aria-label="Adjacent chapters">{pager}</nav></article></main>
<footer class="site-footer wrap"><div><strong>SUPERTERRAIN</strong><span>Original research notes &amp; synthetic examples.</span></div><p>Independent study. No game assets are distributed.</p><a href="{REPO}/blob/main/NOTICE.md">Credits &amp; scope ↗</a></footer></body></html>
'''


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'id' in attributes:
            self.ids.add(attributes['id'])
        for key in ('href', 'src'):
            if key in attributes:
                self.links.append(attributes[key])


def check_links():
    documents = {}
    for path in SITE.rglob('*.html'):
        parser = LinkCollector()
        parser.feed(path.read_text(encoding='utf-8'))
        documents[path.resolve()] = parser
    failures, count = [], 0
    for path, parser in documents.items():
        for url in parser.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if target.is_dir():
                target = target / 'index.html'
            count += 1
            if not target.is_relative_to(SITE.resolve()) or not target.exists():
                failures.append(f'{path.relative_to(SITE)}: missing target {url}')
            elif parsed.fragment and target.suffix == '.html' and unquote(parsed.fragment) not in documents[target].ids:
                failures.append(f'{path.relative_to(SITE)}: missing anchor {url}')
    if failures:
        raise ValueError('\n'.join(failures))
    return len(documents), count


def main():
    (SITE / 'chapters').mkdir(parents=True, exist_ok=True)
    (SITE / 'data').mkdir(exist_ok=True)
    (SITE / 'assets').mkdir(exist_ok=True)
    sources = sorted((ROOT / 'docs').glob('[0-9][0-9]-*.md'))
    rendered = [(path, *render_markdown(path.read_text(encoding='utf-8'))) for path in sources]
    chapters = [(path, headings[0][1]) for path, _, headings in rendered]
    for path, content, headings in rendered:
        (SITE / 'chapters' / path.with_suffix('.html').name).write_text(page(path, content, headings, chapters), encoding='utf-8')
    for source in (ROOT / 'evidence').glob('*.json'):
        shutil.copyfile(source, SITE / 'data' / source.name)
    for source in (ROOT / 'assets').glob('*.svg'):
        shutil.copyfile(source, SITE / 'assets' / source.name)
    make_art()
    documents, links = check_links()
    print(f'Built {len(chapters)} chapters; checked {links} local links across {documents} HTML documents.')


if __name__ == '__main__':
    main()
