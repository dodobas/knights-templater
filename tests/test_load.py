from .utils import TemplateTestCase, Mock

from knights import Template


class LoadTagTest(TemplateTestCase):

    def test_load_default(self):
        t = Template('{! knights.defaultfilters !}')
        self.assertIn('title', t.parser.filters)