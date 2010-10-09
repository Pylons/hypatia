import unittest

class TestQueryWithDSL(unittest.TestCase):
    def test_it(self):
        from repoze.catalog.catalog import Catalog
        from repoze.catalog.indexes.field import CatalogFieldIndex
        from repoze.catalog.indexes.keyword import CatalogKeywordIndex
        from repoze.catalog.indexes.text import CatalogTextIndex

        catalog = Catalog()
        catalog['name'] = CatalogFieldIndex('name')
        catalog['title'] = CatalogFieldIndex('title')
        catalog['text'] = CatalogTextIndex('text')
        catalog['allowed'] = CatalogKeywordIndex('allowed')

        catalog.index_doc(1, Content('name1', 'title1', 'body one', ['a']))
        catalog.index_doc(2, Content('name2', 'title2', 'body two', ['b']))
        catalog.index_doc(3, Content('name3', 'title3', 'body three', ['c']))
        catalog.index_doc(4, Content('name4', 'title4', 'body four',['a', 'b']))
        catalog.index_doc(5, Content('name5', 'title5', 'body five',
                                     ['a', 'b', 'c']))
        catalog.index_doc(6, Content('name6', 'title6', 'body six',['d']))

        query = (
            "(allowed == 'a' and allowed == 'b' and "
            "(name == 'name1' or name == 'name2' or name == 'name3' or "
            "name == 'name4' or name == 'name5') - (title == 'title3')) and "
            "body in text"
        )
        numdocs, result = catalog.query(
            query, sort_index='name', limit=5, names=dict(body='body'))
        self.assertEqual(numdocs, 2)
        self.assertEqual(list(result), [4, 5])

try:
    import ast
except ImportError: #pragma NO COVERAGE
    del TestQueryWithDSL

class Content(object):
    def __init__(self, name, title, text, allowed):
        self.name = name
        self.title = title
        self.text = text
        self.allowed = allowed


