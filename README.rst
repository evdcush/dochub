######
dochub
######
A project to manage papers and notes in one location.

.. contents::


Features
========
Dochub is used to get citation information, update a bibliography, download papers, and generate notes from a template.

query
-----
Dochub uses the ArXiv, Semantic Scholar (SS), and CrossRef (CR) APIs to find citation information given a DOI or arxiv ID.

Semantic Scholar
^^^^^^^^^^^^^^^^
Because it can queried with either arxiv ID or doi, and because of the rich information provided, SS is the primary API used.

**Overview** of the semantic scholar api response data (from the ``query_ss`` docstring in ``query.py``):

:arxivId: arxiv id, eg '1706.03762'
:doi: paper doi, eg '10.1038/nature16961'
:title: publication title, eg 'The Whale Optimization Algorithm'
:year: year of publication
:authors: list of paper authors, with fields:

    :authorId: SS author id
    :name: authors name 'First Last'
    :url: SS page for author
:citationVelocity:
    "a weighted average of the publication's citations for
    the last 3 years..., which indicates how popular and
    lasting the publication is" (higher is better)

:citations: list of publications citing this paper, with fields:

    [arxivId, authors, doi, isInfluential, paperId, title, url, venue, year]
        :isInfluential: whether this paper was influential to the citing publication

:influentialCitationCount: number of citations where this paper ``isInfluential``
:paperId: unique hash for this paper on SS,eg:

    ``paperId = '0b0cf7e00e7532e38238a9164f0a8db2574be2ea'``

    ``url = 'https://www.semanticscholar.org/paper/' + paperId``
:url: link to publication on semantic scholar (as demonstrated above with ``paperId``)
:references: list of publications (within SS database) this paper cites.

    same fields as citations (only, ``isInfluential`` now means the reference
    was influential to this paper)

:topics: list of topics (keywords) relevant to paper, with fields:

    :topic: name of topic; eg 'Machine Translation'
    :topicId: topic id on SS; eg '34995'
    :url: link to topic on SS; eg 'https://www.semanticscholar.org/topic/34995')

:venue: where the paper was published or featured.

    Typically this means the journal, such as 'ArXiv', 'Nature', etc..., but if the paper was
    featured in a conference, venue may be the conference name (eg 'NIPS')


ArXiv
^^^^^
The arxiv API is only used to retrieve the abstract for a paper, or when SS has not catalogued an arxiv publication (common with very recent works). Otherwise, SS provides more information.

CrossRef
^^^^^^^^
The CrossRef api has perhaps the most info on any given doi. Currently, CrossRef is only queried when SS fails or for citation count, but I plan on using CR more extensively, as it has the most extensive catalog and has better support for publications that are *not* of type ``journal-article``, such as ``inproceedings`` or ``book`` which are not as common on SS.


Download
--------
Dochub additionally has some limited support for downloading publications. Dochub can download any arxiv paper (as all publications on arxiv have freely available pdfs). For non-arxiv publications, Dochub will download a paper if it is available through SS. There is experimental support for downloading paywalled publications through LibGen.

Documents
---------
Dochub uses ``pybtex`` to format citations in either bibTex format or as yaml entries. There is also an opinionated reStructuredText template used to generate notes.

----

Requirements
============
- Python >= 3.6
    - ``pyperclip`` for copying support
    - ``unidecode`` or ``slugify``; currently both are being used, but I will probably drop one
    - ``requests``, ``feedparser``

All python packages can be installed via ``pip``.

-----

License
-------
This project is licensed under the LGPL 3.0.

Acknowledgement
^^^^^^^^^^^^^^^
This project has used code from several other well-established projects, including:

- `Bibcure <https://github.com/bibcure/bibcure>`_
- `papis <https://github.com/papis/papis>`_
- `pylibgen <https://github.com/JoshuaRLi/pylibgen>`_




Roadmap
^^^^^^^
- sample usage
- **Better CrossRef support.** CrossRef has an extensive catalog, and the best citation data.
- **Richer citation entries.** Currently, citations use a fixed format and fields, and assume all publications are of type ``journal-article``.
- **More robust libgen support.** The api url for libgen and response data has changed several times; it is now hardcoded.
    - libgen also, surprisingly, has accurate citation info. This could potentially allow dochub to support ISBN queries as well--something none of the currently supported APIs do.
- **cleanup CLI**
- **Zotero support**


