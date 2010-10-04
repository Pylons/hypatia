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
        
        catalog.index_doc(1, Content('name1', 'title1', 'text one', ['a']))
        catalog.index_doc(2, Content('name2', 'title2', 'text two', ['b']))
        catalog.index_doc(3, Content('name3', 'title3', 'text three', ['c']))
        catalog.index_doc(4, Content('name4', 'title4', 'text four',['a', 'b']))
        catalog.index_doc(5, Content('name5', 'title5', 'text five',['b', 'c']))
        catalog.index_doc(6, Content('name6', 'title6', 'text six',['d']))

        textq = query.Text('text', 'text')
        eqq = query.Eq('name', 'name1')
        neq = query.NotEq('name', 'name2')

        numdocs, result = catalog.query(textq).And(eqq).And(neq).apply(
            sort_index='name')

        self.assertEqual(numdocs, 1)
        self.assertEqual(list(result), [1])

class Content(object):
    def __init__(self, name, title, text, allowed):
        self.name = name
        self.title = title
        self.text = text
        self.allowed = allowed
        

