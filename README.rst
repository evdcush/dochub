dochub
######
A project to manage papers and notes in one location. !WIP!

.. contents::


========
Features
========
Dochub is used to get citation information, update a bibliography, download papers, and generate notes from a template.

-----
query
-----
Dochub uses the ArXiv, Semantic Scholar (SS), and CrossRef (CR) APIs to find citation information given a DOI or arxiv ID.

Semantic Scholar
================
Because it can queried with either arxiv ID or doi, and because of the rich information provided, SS is the primary API used.


ArXiv
=====
The arxiv API is only used to retrieve the abstract for a paper, or when SS has not catalogued an arxiv publication (common with very recent works). Otherwise, SS provides more information.

CrossRef
========
The CrossRef api has perhaps the most info on any given doi. Currently, CrossRef is only queried when SS fails or for citation count, but I plan on using CR more extensively, as it has the most extensive catalog and has better support for publications that are *not* of type ``journal-article``, such as ``inproceedings`` or ``book`` which are not as common on SS.

-------

--------
Download
--------
Dochub additionally has some limited support for downloading publications. Dochub can download any arxiv paper (as all publications on arxiv have freely available pdfs). For non-arxiv publications, Dochub will download a paper if it is available through SS. There is experimental support for downloading paywalled publications through LibGen.


---------
Documents
---------
Dochub uses ``pybtex`` to format citations in either bibTex format or as yaml entries. There is also an opinionated reStructuredText template used to generate notes.

----

============
Requirements
============
- Python >= 3.6
    - ``pyperclip`` for copying support
    - ``unidecode`` or ``slugify``; currently both are being used, but I will probably drop one
    - ``requests``, ``feedparser``

All python packages can be installed via ``pip``.

-----

-------
License
-------
This project is licensed under the LGPL 3.0.

Acknowledgement
===============
This project has used code from several other well-established projects, including:

- `Bibcure <https://github.com/bibcure/bibcure>`_
- `papis <https://github.com/papis/papis>`_
- `pylibgen <https://github.com/JoshuaRLi/pylibgen>`_

