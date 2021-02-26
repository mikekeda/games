from django.test import TestCase
from core.templatetags.core_tags import loop, get


class CoreTemplatetagsTest(TestCase):
    def test_templatetags_loop(self):
        result = loop(5)
        self.assertListEqual(list(result), list(range(5)))

        result = loop(5, True)
        self.assertListEqual(list(result), list(reversed(range(5))))

    def test_templatetags_get(self):
        result = get(["q", "w", "e", "r", "t", "y"], 2)
        self.assertEqual(result, "e")
