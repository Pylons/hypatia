import unittest

class TestFunctional(unittest.TestCase):
    def test_it(self):
        from repoze.catalog.catalog import Catalog
        from repoze.catalog.indexes.field import CatalogFieldIndex
        from repoze.catalog.indexes.keyword import CatalogKeywordIndex
        from repoze.catalog.indexes.text import CatalogTextIndex
        from repoze.catalog import query

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

        numdocs, result = catalog.query(
            query.All('allowed', ['a', 'b'])
            ).And(
            query.Any('name', ['name1', 'name2', 'name3', 'name4', 'name5'])
            ).Not(
            query.Eq('title', 'title3')
            ).And(
            query.Contains('text', 'body')
            ).apply(sort_index='name', limit=5)

        self.assertEqual(numdocs, 2)
        self.assertEqual(list(result), [4, 5])

class Content(object):
    def __init__(self, name, title, text, allowed):
        self.name = name
        self.title = title
        self.text = text
        self.allowed = allowed
        

