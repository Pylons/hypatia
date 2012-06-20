Installing :mod:`hypatia`
=========================

How To Install
--------------

You will need `Python <http://python.org>`_ version 2.6 or better to run
:mod:`hypatia`.  Development of :mod:`hypatia` is done
primarily under Python 2.7, so that version is recommended.  It does *not*
run under Python 3.X.

.. warning:: To succesfully install :mod:`hypatia`, you will need an
   environment capable of compiling Python C code.  See the
   documentation about installing, e.g. ``gcc`` and ``python-devel``
   for your system.  You will also need :term:`setuptools` installed
   within your Python system in order to run the ``easy_install``
   command.

It is advisable to install :mod:`hypatia` into a :term:`virtualenv` in order
to obtain isolation from any "system" packages you've got installed in your
Python version (and likewise, to prevent :mod:`hypatia` from globally
installing versions of packages that are not compatible with your system
Python).

After you've got the requisite dependencies installed, you may install
:mod:`hypatia` into your Python environment using the following
command::

  $ easy_install hypatia

What Gets Installed
-------------------

When you ``easy_install`` :mod:`hypatia` and ZODB are installed.
