Installing :mod:`repoze.catalog`
================================

How To Install
--------------

You will need `Python <http://python.org>`_ version 2.4 or better to
run :mod:`repoze.catalog`.  Development of :mod:`repoze.catalog` is
done primarily under Python 2.6, so that version is recommended.
:mod:`repoze.catalog` also runs under Python 2.4 and 2.5 with limited
functionality.  It does *not* run under Python 3.X.

.. warning:: To succesfully install :mod:`repoze.catalog`, you will need an
   environment capable of compiling Python C code.  See the
   documentation about installing, e.g. ``gcc`` and ``python-devel``
   for your system.  You will also need :term:`setuptools` installed
   within your Python system in order to run the ``easy_install``
   command.

It is advisable to install :mod:`repoze.catalog` into a
:term:`virtualenv` in order to obtain isolation from any "system"
packages you've got installed in your Python version (and likewise, to
prevent :mod:`repoze.catalog` from globally installing versions of
packages that are not compatible with your system Python).

After you've got the requisite dependencies installed, you may install
:mod:`repoze.catalog` into your Python environment using the following
command::

  $ easy_install repoze.catalog

What Gets Installed
-------------------

When you ``easy_install`` :mod:`repoze.catalog`, various Zope
libraries and ZODB are installed.
