from .utils import TemplateTestCase, Mock

from knights import Template


class LoadTagTest(TemplateTestCase):

    def test_load_default(self):
        t = Template('{! knights.defaultfilters !}')
        self.assertIn('escape', t.parser.filters)



class CommentTagText(TemplateTestCase):

    def test_comment(self):
        self.assertRendered('{# test #}', '')
