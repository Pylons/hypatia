/*****************************************************************************

  Copyright (c) 2002 Zope Foundation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

/*	okascore.c
 *
 *	The inner scoring loop of OkapiIndex._search_wids() coded in C.
 *
 * Example from an indexed Python-Dev archive, where "python" shows up in all
 * but 2 of the 19,058 messages.  With the Python scoring loop,
 *
 *      query: python
 *      # results: 10 of 19056 in 534.77 ms
 *      query: python
 *      # results: 10 of 19056 in 277.52 ms
 *
 * The first timing is cold, the second timing from an immediate repeat of
 * the same query.  With the scoring loop here in C:
 *
 *     query: python
 *     # results: 10 of 19056 in 380.74 ms  -- 40% speedup
 *     query: python
 *     # results: 10 of 19056 in 118.96 ms  -- 133% speedup
 */

#include "Python.h"

#define K1 1.2
#define B  0.75

#ifndef PyTuple_CheckExact
#define PyTuple_CheckExact PyTuple_Check
#endif

static PyObject *
score(PyObject *self, PyObject *args)
{
	/* Believe it or not, floating these common subexpressions "by hand"
	   gets better code out of MSVC 6. */
	const double B_FROM1 = 1.0 - B;
	const double K1_PLUS1 = K1 + 1.0;

	/* Inputs */
	PyObject *result;	/* IIBucket result, maps d to score */
	PyObject *d2fitems;	/* ._wordinfo[t].items(), maps d to f(d, t) */
	PyObject *d2len;	/* ._docweight, maps d to # words in d */
	double idf;		/* inverse doc frequency of t */
	double meandoclen;	/* average number of words in a doc */

	int n, i;

	if (!PyArg_ParseTuple(args, "OOOdd:score", &result, &d2fitems, &d2len,
						   &idf, &meandoclen))
		return NULL;

	n = PyObject_Length(d2fitems);
	for (i = 0; i < n; ++i) {
		PyObject *d_and_f;	/* d2f[i], a (d, f) pair */
		PyObject *d;
		double f;
		PyObject *doclen;	/* ._docweight[d] */
		double lenweight;
		double tf;
		PyObject *doc_score;
		int status;

		d_and_f = PySequence_GetItem(d2fitems, i);
		if (d_and_f == NULL)
			return NULL;
		if (!(PyTuple_CheckExact(d_and_f) &&
		      PyTuple_GET_SIZE(d_and_f) == 2)) {
			PyErr_SetString(PyExc_TypeError,
				"d2fitems must produce 2-item tuples");
			Py_DECREF(d_and_f);
			return NULL;
		}
		d = PyTuple_GET_ITEM(d_and_f, 0);
		f = PyFloat_AsDouble(PyTuple_GET_ITEM(d_and_f, 1));

        if (PyErr_Occurred()) {
			PyErr_SetString(PyExc_TypeError,
				"d2fitem[1] should be a a float");
			return NULL;
        }

		doclen = PyObject_GetItem(d2len, d);
		if (doclen == NULL) {
			Py_DECREF(d_and_f);
			return NULL;
		}

		lenweight = B_FROM1 + B * PyFloat_AsDouble(doclen) / meandoclen;
        if (PyErr_Occurred()) {
			PyErr_SetString(PyExc_TypeError,
				"doclen be a a float");
			return NULL;
        }

		tf = f * K1_PLUS1 / (f + K1 * lenweight);
		doc_score = PyFloat_FromDouble(tf * idf);
		if (doc_score == NULL)
			status = -1;
		else
			status = PyObject_SetItem(result, d, doc_score);
		Py_DECREF(d_and_f);
		Py_DECREF(doclen);
		Py_XDECREF(doc_score);
		if (status < 0)
			return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char score__doc__[] =
"score(result, d2fitems, d2len, idf, meandoclen)\n"
"\n"
"Do the inner scoring loop for an Okapi index.\n";

static PyMethodDef module_functions[] = {
	{"score",	   score,	  METH_VARARGS, score__doc__},
	{NULL}
};

static char module__name__[] = "okascore";
static char module__doc__[] = "inner scoring loop for Okapi rank";

/*
 *  No slot definitions needed multi-phase initialization:
 *
 *  we have no state, and initialize / register no types.
 */
static PyModuleDef_Slot module_slots[] = {
    {0,                 NULL}
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    .m_name     = module__name__,
    .m_doc      = module__doc__,
    .m_methods  = module_functions,
    .m_slots    = module_slots,
};

PyMODINIT_FUNC
PyInit_okascore(void)
{
    return PyModuleDef_Init(&module_def);
}
