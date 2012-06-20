import unittest
from .. import query as q


class TestQueryBase(object):
    def test_it(self):
        from ..catalog import Catalog
        from ..catalog import CatalogQuery
        from ..field import FieldIndex
        from ..keyword import KeywordIndex
        from ..text import TextIndex

        catalog = Catalog()
        catalog['name'] = FieldIndex('name')
        catalog['title'] = FieldIndex('title')
        catalog['text'] = TextIndex('text')
        catalog['allowed'] = KeywordIndex('allowed')

        catalog.index_doc(1, Content('name1', 'title1', 'body one', ['a']))
        catalog.index_doc(2, Content('name2', 'title2', 'body two', ['b']))
        catalog.index_doc(3, Content('name3', 'title3', 'body three', ['c']))
        catalog.index_doc(4, Content('name4', None, 'body four',['a', 'b']))
        catalog.index_doc(5, Content('name5', 'title5', 'body five',
                                     ['a', 'b', 'c']))
        catalog.index_doc(6, Content('name6', 'title6', 'body six',['d']))

        q = CatalogQuery(catalog)

        numdocs, result = q.query(
            self.query, sort_index='name', limit=5, names=dict(body='body'))
        self.assertEqual(numdocs, 2)
        self.assertEqual(list(result), [4, 5])


class TestQueryWithCQE(unittest.TestCase, TestQueryBase):
    query = (
        "(allowed == 'a' and allowed == 'b' and "
        "(name == 'name1' or name == 'name2' or name == 'name3' or "
        "name == 'name4' or name == 'name5') and not(title == 'title3')) and "
        "body in text"
        )


class TestQueryWithPythonQueryObjects(unittest.TestCase, TestQueryBase):
    query = (
        q.All('allowed', ['a', 'b']) &
        q.Any('name', ['name1', 'name2', 'name3', 'name4', 'name5']) &
        q.Not(q.Eq('title', 'title3')) &
        q.Contains('text', 'body')
        )


class Content(object):
    def __init__(self, name, title, text, allowed):
        self.name = name
        if title:
            self.title = title
        self.text = text
        self.allowed = allowed


