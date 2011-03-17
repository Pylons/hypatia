"""
Version 0.8.0 introduced a NOT operator which required that indexes keep track
of some data they hadn't previously needed to keep track of. Previously, if a
discriminator returned `default` when indexing a document, the index did not
keep track of the fact that it had seen that docid. In order to properly
implement query negations via the NOT operator, indexes now keep track of all
docids which have been indexed regardless of whether those docids had a value
for the index.

The functions in this module will bring indices in an existing catalog up to
date with this information. If you are using a `DocumentMap`, the easiest way
to migrate your indices will be to call `migrate_to_0_8_0_from_document_map`.
If you are not using a `DocumentMap` but otherwise have a convenient means of
generating the complete set of docids in your catalog, you can use
`migrate_to_0_8_0_from_docids`. Failing both of the previous options, you can
call `migrate_to_0_8_0`, which will try to build up a set of all docids in the
catalog by looking at all of the indexes first.
"""

import BTrees
IF = BTrees.family32.IF


def migrate_to_0_8_0_from_document_map(catalog, document_map):
    migrate_to_0_8_0_from_docids(catalog, document_map.docid_to_address.keys())


def migrate_to_0_8_0(catalog):
    docids = IF.multiunion([IF.Set(index._indexed()) for index
                            in catalog.values() if hasattr(index, '_indexed')])
    migrate_to_0_8_0_from_docids(catalog, docids)


def migrate_to_0_8_0_from_docids(catalog, docids):
    for index in catalog.values():
        migrate = getattr(index, '_migrate_to_0_8_0', None)
        if migrate is not None:
            migrate(docids)
