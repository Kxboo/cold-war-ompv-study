"""Site publication checks: source citations, internal navigation and evidence."""
from pathlib import Path
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_site import check_links, inline, render_flowchart, render_markdown, target_url


class SiteTests(unittest.TestCase):
    def test_code_in_a_pinned_citation_keeps_link_and_code_semantics(self):
        rendered = inline("[Pinned `abc123`](https://github.com/a/b/blob/abc123/file.cpp#L3-L9)")
        self.assertEqual(rendered, '<a href="https://github.com/a/b/blob/abc123/file.cpp#L3-L9">Pinned <code>abc123</code></a>')

    def test_chapter_links_and_evidence_remap_without_losing_fragments(self):
        self.assertEqual(target_url('06-capture-workflow.md#practical-reproduction-and-retention'), '06-capture-workflow.html#practical-reproduction-and-retention')
        self.assertEqual(target_url('../evidence/shader-validation.json'), '../data/shader-validation.json')
        self.assertEqual(target_url('../examples/ompv_reference.py'), 'https://github.com/Kxboo/cold-war-ompv-study/blob/main/examples/ompv_reference.py')

    def test_source_code_and_table_content_escape_html(self):
        rendered, headings = render_markdown('# Example\n\n| Code | Value |\n| --- | ---: |\n| `a < b` | 2 |\n\n```text\n<not-an-element>\n```\n')
        self.assertIn('<code>a &lt; b</code>', rendered)
        self.assertIn('&lt;not-an-element&gt;', rendered)
        self.assertNotIn('<not-an-element>', rendered)
        self.assertEqual(headings, [(1, 'Example', 'example')])

    def test_generated_site_links_resolve(self):
        documents, links = check_links()
        self.assertGreaterEqual(documents, 9)
        self.assertGreater(links, 100)

    def test_all_current_flowcharts_have_semantic_layouts_and_preserve_labels(self):
        count = 0
        for path in (ROOT / 'docs').glob('*.md'):
            for source in re.findall(r'```mermaid\n(.*?)```', path.read_text(encoding='utf-8'), re.S):
                rendered = render_flowchart(source)
                self.assertIn('<figure class="flow-diagram">', rendered, path.name)
                self.assertIn('<summary>View diagram source</summary>', rendered)
                visible = rendered.split('<details')[0]
                for label in re.findall(r'[A-Za-z][A-Za-z0-9_]*\[([^\]]+)\]', source):
                    from html import escape
                    self.assertIn(escape(label), visible, path.name)
                count += 1
        self.assertEqual(count, 3)

    def test_published_report_and_displayed_metrics_match_saved_evidence(self):
        report = json.loads((ROOT / 'evidence' / 'shader-validation.json').read_text())
        copied = json.loads((ROOT / 'site' / 'data' / 'shader-validation.json').read_text())
        self.assertEqual(report, copied)
        index = (ROOT / 'site' / 'index.html').read_text(encoding='utf-8')
        for channel in ('colour_srgb', 'normal_xy', 'roughness', 'ao'):
            for metric in ('mae_8bit', 'p99_8bit', 'max_8bit'):
                self.assertIn(f'{report[channel][metric]:.6f}', index)


if __name__ == '__main__':
    unittest.main()
