import unittest


class TestMigration(unittest.TestCase):

    def test_migrate_to_0_8_0(self):
        from repoze.catalog.migration import migrate_to_0_8_0
        catalog = DummyCatalog()
        migrate_to_0_8_0(catalog)
        self.assertEqual(catalog['one'].migrated, set([1, 2, 3]))
        self.assertEqual(catalog['two'].migrated, set([1, 2, 3]))
        self.assertEqual(catalog['three'].migrated, False)


    def test_migrate_to_0_8_0_from_document_map(self):
        from repoze.catalog.migration import migrate_to_0_8_0_from_document_map
        catalog = DummyCatalog()
        migrate_to_0_8_0_from_document_map(catalog, catalog.document_map)
        self.assertEqual(catalog['one'].migrated, set([2, 3, 4]))
        self.assertEqual(catalog['two'].migrated, set([2, 3, 4]))
        self.assertEqual(catalog['three'].migrated, False)


class DummyCatalog(dict):

    def __init__(self):
        super(DummyCatalog, self).__init__()
        self['one'] = MigratableDummyIndex(1, 2)
        self['two'] = MigratableDummyIndex(2, 3)
        self['three'] = DummyIndex(3, 4)
        self.document_map = DummyDocumentMap()


class DummyIndex(object):
    migrated = False

    def __init__(self, *docids):
        self._docids = set(docids)


class MigratableDummyIndex(DummyIndex):

    def _migrate_to_0_8_0(self, docids):
        self.migrated = set(docids)

    def _indexed(self):
        return self._docids


class DummyDocumentMap(object):

    def __init__(self):
        self.docid_to_address = {2: '/one', 3: '/one/two', 4: '/three'}
