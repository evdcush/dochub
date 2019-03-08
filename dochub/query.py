"""
There are three apis that can be queried using this module:
arXiv, Semantic Scholar, and CrossRef

# Overview of API features
# ========================
Overall, the semantic scholar is the best API. It supports both arxiv and doi
paper IDs, it provides both citations to paper and the paper's references
(that are available in SS database), and it provides keywords to paper.
It's data response is already very well organized, and it has interesting
metrics on how "influential" a paper is. Approximate citation counts.

arXiv
-----
+ fast (feedparser)
+ includes article abstract
+ always has link to pdf
+ supports queries for many paper IDs*
+ supports general search queries*
- only supports articles published to arxiv
- somewhat redundant data fields in response
- very little information about an article beyond big bois (year, title, auth, etc.)

* Not (yet) supported in this module

Semantic Scholar
----------------
+ new hotness
+ supports paper queries for arxiv ids AND DOI
+ includes citations on paper!
  + and thereby an estimate of the paper's citation count
+ includes paper references!
+ includes paper keywords!
+ interesting metrics for paper "importance" or "influence"
+ sensible, convenient response data structure (less processing needed)
- no abstracts
- database not comprehensive enough (query will fail on valid doi inputs)
- links always point to SS' link, rather than original publisher link (very minor gripe)

CrossRef
--------
+ fast
+ loads of data
+ loads of data
+ citation count (keyed 'is-referenced-by-count') # but like SS, not 100% up-to-date or comprehensive as google scholar
+ fairly comprehensive info on publisher
+ data fields are formatted in standard bibtex format (eg 'URL', 'DOI', 'author' instead of 'url', 'doi', 'authors')
+ keywords
- loads of data
- fairly raw response (needs more processing than the other featured APIs)
  - almost no response field-value is atomic; everything in list (sometimes with unrelated vals)


Query flow
==========
Currently,
All queries are assumed to be 'article' (even though chapters,
inproceedings, books, etc. are frequently queried). Only single-paper
queries are supported (multiple ids from input or file to be supported later).

* Query SS api with input pub id (doi or arxiv)
  * if arxiv id, get abstract and paper link from arxiv API
  * if SS fails on doi, check crossref
* process response for primary data of interest:
  year, authors, title, keywords, pub id, abstract
* return data processed into a dict

"""
import sys
import code
import subprocess
from typing import List, Set, Dict, Tuple, Optional

import requests
from unidecode import unidecode
from slugify import slugify


#-----------------------------------------------------------------------------#
#                               Query constants                               #
#-----------------------------------------------------------------------------#
# urls
# ====
doi_url = "http://doi.org/"
ss_api_paper_url = "https://api.semanticscholar.org/v1/paper/"
crossref_api_url = "http://api.crossref.org/works/"
arxiv_api_paper_url = "http://export.arxiv.org/api/query?id_list="

class AttrDict(dict):
    """ dict that has dot access (cannot pickle) """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

#-----------------------------------------------------------------------------#
#                               Utils & Helpers                               #
#-----------------------------------------------------------------------------#
# String stuff
# ============
is_doi   = lambda ref_id: ref_id[2] == '.'
scrub_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]
to_ascii = lambda s: unidecode(s) # to_ascii('çivicioglu') --> 'civicioglu'

# arxiv urls
arxiv_abs = lambda arx_id: f"https://arxiv.org/abs/{arx_id}"
arxiv_pdf = lambda arx_id: f"https://arxiv.org/pdf/{arx_id}"

# ss pdf url
ss_pdf = lambda pid: f'https://pdfs.semanticscholar.org/{pid[:4]}/{pid[4:]}.pdf'

# Parse helpers
# =============
def check_status(status_code):
    if status_code != 200:
        raise ValueError(status_code)

def check_url_exist(url):
    """ uses wget to check if a url exists
    Only used currently for checking if SS has paper available

    wget args
    ---------
    -q : quiet
    --spider : don't download (just navigate to site)
    --max-redirect 0 : don't follow redirects
        ss will redirect if no paper
    """
    shcmd = f'wget -q --spider --max-redirect 0 {url}'
    return subprocess.run(shcmd, shell=True).returncode == 0


# Formatting
# ==========
def extract_authors(response, crossref=False):
    """ gets author names from response and formats them

    author names are converted to ascii (for filenaming purposes),
    and then formatted as typical pronouns

    For example:
    "LINNÉA CLAESSON" would be formatted to "Linnea Claesson"
    (note the unicode 'É' is converted to ascii e, and name is titled)
    """
    authors = []
    format_name = lambda name: to_ascii(name).title()
    if crossref:
        for author in response['author']:
            name = format_name(f"{author['given']} {author['family']}")
            authors.append(name)
    else:
        for author in response['authors']:
            name = format_name(author['name'])
            authors.append(name)
    return authors


def format_identifier(info):
    name = info.author[0].split(' ') # splits first author's name
    identifier = f"{name[-1]}.{name[0][0]}-{info.year}"
    return identifier


def format_filename(info):
    identifier = format_identifier(info)
    title  = slugify(info.title, separator='_', lowercase=False)
    #==== format: Author-YEAR-Title
    filename = f"{identifier}-{title}"
    return filename

#=============================================================================#
#                            _____   __   __  _____  __      __               #
#                    /\     |  __ \  \ \ / / |_   _| \ \    / /               #
#                   /  \    | |__) |  \ V /    | |    \ \  / /                #
#                  / /\ \   |  _  /    > <     | |     \ \/ /                 #
#                 / ____ \  | | \ \   / . \   _| |_     \  /                  #
#                /_/    \_\ |_|  \_\ /_/ \_\ |_____|     \/                   #
#                                                                             #
#=============================================================================#

def query_arxiv(arxiv_id):
    """ Query arxiv API for a given paper ID

    Params
    ------
    arxiv_id : str
        a string containing an arxiv ID; can be embedded in arxiv link
        For example, all the follow are valid inputs:
            "https://arxiv.org/abs/1901.01536"
            "arxiv.org/pdf/1704.02532.pdf"
            "1807.04587"

    Returns
    -------
    response : dict
        arxiv api response for paper
    """
    import feedparser
    arx_id  = scrub_id(arxiv_id)
    req_url = arxiv_api_paper_url + arx_id

    #==== query
    response = feedparser.parse(req_url)
    status_code = response.get('status')
    check_status(status_code)
    response = response['entries'][0]
    return response

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def process_arxiv(response, abs_only=False):
    """ Process arxiv API response

    Params
    ------
    response : dict
        valid arxiv api response

    abs_only : bool
        only return the abstract of paper

    Returns
    -------
    info : str | AttrDict
        paper abstract, if abs_only
        else a dict containing all relevant paper info
    """
    if abs_only:
        return response.get('summary', 'Unavailable')

    #==== process
    arx_id = scrub_id(response['id'])
    info = AttrDict(
        URL = arxiv_abs(arx_id),
        pdf = arxiv_pdf(arx_id),
        year  = response['published'][:4],
        title = response['title'],
        author   = extract_authors(response),
        arxivId  = arx_id,
        abstract = response.get('summary', 'Unavailable'),
        )
    return info


#=============================================================================#
#     _____   ______   __  __              _   _   _______   _____    _____   #
#    / ____| |  ____| |  \/  |     /\     | \ | | |__   __| |_   _|  / ____|  #
#   | (___   | |__    | \  / |    /  \    |  \| |    | |      | |   | |       #
#    \___ \  |  __|   | |\/| |   / /\ \   | . ` |    | |      | |   | |       #
#    ____) | | |____  | |  | |  / ____ \  | |\  |    | |     _| |_  | |____   #
#   |_____/  |______| |_|  |_| /_/    \_\ |_| \_|    |_|    |_____|  \_____|  #
#                                                                             #
#=============================================================================#

def query_ss(ref_id, include_unknown_ref=True, citation_count_only=False):
    """ Query Semantic Scholar (SS) API for given paper reference id

    Params
    ------
    ref_id : str
        either a DOI or an arXiv ID

    include_unknown_ref : bool
        include references to papers unavailable in SS catalog

    Returns
    -------
    response : dict
        api json response


    SS response
    -----------
    arxivId : str
        the arxiv id, eg: '1706.03762'; Often None for doi queries

    doi : str
        paper DOI (can be None)

    title : str
        publication title

    year : int
        year of publication

    authors : list(dict)
        list of paper authors, with fields:
            'authorId' : str; SS author id
                'name' : str; authors name 'First Last'
                 'url' : str; SS page for author

    citationVelocity : int
        "a weighted average of the publication's citations for
        the last 3 years..., which indicates how popular and
        lasting the publication is" (higher is better)

    citations : list(dict)
        list of publications citing this paper, with fields:
        [arxivId, authors, doi, isInfluential, paperId, title, url, venue, year]
        isInfluential : bool
            whether this paper was influential to the citing publication

    influentialCitationCount : int
        number of citations where isInfluential

    paperId : str
        unique hash for this paper on Semantic Scholar;
            paperId = '0b0cf7e00e7532e38238a9164f0a8db2574be2ea'
            url = 'https://www.semanticscholar.org/paper/' + paperId

    url : str
        link to publication on semantic scholar

    references : list(dict)
        list of publications (within SS database) this paper cites;
        same fields as citations (only, isInfluential now means the reference
        was influential to this paper)

    topics : list(dict)
        list of topics (keywords) relevant to paper, with fields:
            topic : name of topic (eg 'Machine Translation')
            topicId : topic id on SS (eg '34995')
            url : link to topic on SS
                (eg 'https://www.semanticscholar.org/topic/34995')

    venue : str
        where the paper was published or featured. Typically this means the
        journal, such as 'ArXiv', 'Nature', etc..., but if the paper was
        featured in a conference, venue may be the conference name (eg 'NIPS')
    """
    #==== format query url
    req_url = ss_api_paper_url
    ref_is_doi = is_doi(ref_id)
    if not ref_is_doi:
        ref_id = scrub_id(ref_id)
        req_url += 'arXiv:'
    req_url += ref_id

    if include_unknown_ref:
        req_url += "?include_unknown_references=true"

    #==== query
    response = requests.get(req_url)
    status_code = response.status_code
    check_status(status_code)
    response = response.json()
    if citation_count_only:
        return len(response['citations'])
    return response

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def fuzz_refs(a, b):
    """ score the similarity of two publications based on the
    similarity or distance between their references
    """
    pass
'''
def format_ref(ref):
    """ format reference for notes """
    #[arxivId, authors, doi, isInfluential, paperId, title, url, venue, year]
    ref_pub_id = ''
    authors    = ''
    title      = ''
    year       = ''
    url        = ''

    #==== Check for publication id
    if ref['arxivId']:
        arx_id = ref['arxivId']
        url = arxiv_abs(ref_pub_id) # arxiv.org/abs/ref_pub_id
        ref_pub_id = f"`arXiv:{arx_id} <{url}>`_"
    elif ref['doi']:
        doi = ref['doi']
        url = doi_url + ref_pub_id  # doi.org/ref_pub_id
        ref_pub_id = f"`DOI:{doi} <{url}>`_"
    elif ref['url']:
        url = ref['url'] # semantic scholar link
        ref_pub_id = f"`SemanticScholar <{url}>`_"

    #==== year and title
    if ref['year']:
        year = str(ref['year'])
    if ref['title']:
        title = ref['title']
        title += '.' if title[-1] != '.' else ''

    #==== format authors
    if ref['authors']:
        # get authors
        ref_authors = extract_authors(ref)
        num_authors = len(ref_authors)
        # author string
        first = ref_authors.pop(0)
        fsplit = first.split(' ')
        firstname, restname = fsplit[-1], ' '.join(fsplit[:-1])
        authors = f"{firstname}, {restname}"
        # format string based on num authors
        if num_authors <= 3: # et al. cutoff
            while ref_authors:
                authors += ', '
                if len(ref_authors) == 1:
                    authors += 'and '
                authors += ref_authors.pop(0)
        else:
            authors += ', et al'
        authors += '.' if authors[-1] != '.' else ''

    #==== fully format ref string
    reference = f'{authors} "{title}" {year}, {ref_pub_id}'
    return reference
'''

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def process_ss(response):
    """ Query Semantic Scholar API for given paper reference id

    Params
    ------
    response : dict
        semantic scholar api response for paper

    Returns
    -------
    info : AttrDict
        publication info processed into a dict
    """
    info = AttrDict()

    # As-is
    if response['doi']: info.DOI = response['doi']
    if response['year']: info.year = response['year']
    if response['title']: info.title = response['title']

    # formatting
    if response['authors']:
        info.author = extract_authors(response)
    if response['topics']:
        info.keywords = [kw['topic'] for kw in response['topics']]
    if response['citations']:
        info.citation_count = len(response['citations'])
    if response['references']:
        #[arxivId, authors, doi, isInfluential, paperId, title, url, venue, year]
        info.references = []

    # arxiv content
    arxivId = response['arxivId']
    if arxivId:
        info.arxivId = arxivId
        info.URL = arxiv_abs(arxivId)
        info.pdf = arxiv_pdf(arxivId)
        arx_resp = query_arxiv(arxivId)
        info.abstract = process_arxiv(arx_resp, abs_only=True)
    else:
        info.URL = response['url']
        paper_id = response['paperId']
        pdf_url  = ss_pdf(paper_id)
        if check_url_exist(pdf_url):
            info.pdf = pdf_url
    return info


#=============================================================================#
#             _____                              _____            __          #
#            / ____|                            |  __ \          / _|         #
#           | |       _ __    ___    ___   ___  | |__) |   ___  | |_          #
#           | |      | '__|  / _ \  / __| / __| |  _  /   / _ \ |  _|         #
#           | |____  | |    | (_) | \__ \ \__ \ | | \ \  |  __/ | |           #
#            \_____| |_|     \___/  |___/ |___/ |_|  \_\  \___| |_|           #
#                                                                             #
#=============================================================================#

def query_crossref(doi, citation_count_only=False):
    assert is_doi(doi)
    req_url = crossref_api_url + str(doi)

    #==== query
    response = requests.get(req_url)
    status_code = response.status_code
    check_status(status_code)
    response = response.json()['message']
    if citation_count_only:
        return response.get('is-referenced-by-count', None)
    return response

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def process_crossref(response):
    """ process crossref api response
    """
    info = AttrDict()

    # As-is
    info.DOI = response['DOI']
    info.URL = response['URL']
    if response['title']:
        info.title = response['title'].pop(0)

    # formatting
    if response['created']['date-time']: # eg 2008-06-20T08:06:09Z
        info.year = response['created']['date-time'][:4]
    if response['author']:
        info.author = extract_authors(response, crossref=True)
    if response['is-referenced-by-count']:
        info.citation_count = response['is-referenced-by-count']
    #code.interact(local=dict(globals(), **locals()))
    return info


#=============================================================================#
#                          ___   ____    ____    _   _                        #
#                         |_ _| / ___|  | __ )  | \ | |                       #
#                          | |  \___ \  |  _ \  |  \| |                       #
#                          | |   ___) | | |_) | | |\  |                       #
#                         |___| |____/  |____/  |_| \_|                       #
#                                                                             #
#=============================================================================#
def get_book(isbn):
    pass

#=============================================================================#


#-----------------------------------------------------------------------------#
#                                  Interface                                  #
#-----------------------------------------------------------------------------#
def query(ref_id):
    try:
        response = query_ss(ref_id)
        info = process_ss(response)
        info.identifier = format_identifier(info)
        info.filename   = format_filename(info)
        return info
    except ValueError as v:
        print(f"\tHTTP Error {v}")
        if v == '404':
            print("\tUnable to find reference in Semantic Scholar"
                  "\tnow checking CrossRef...\n")
        response = query_crossref(ref_id)
        info = process_crossref(response)
        info.identifier = format_identifier(info)
        info.filename   = format_filename(info)
        return info
    except:
        msg = f"""\
        \tQuery unsuccessful for {ref_id}
        \tif valid reference id, then it may not be catalogued"""
        raise Exception(msg)


def get_citation_count(ref_id):
    """ checks approx. number of citations for given ref id
    if ref is arxiv id, then only check ss api
    if ref is doi, check both ss and crossref api
    """
    if not is_doi(ref_id):
        # arXiv ID
        try:
            ss_num_cit = query_ss(ref_id, citation_count_only=True)
            arx_id = scrub_id(ref_id)
            msg = (f"\nCitation count for {arx_id}:\n"
                   f"\tSemantic Scholar: {ss_num_cit}")
        except:
            msg = (f"\nERROR: No results found from Semantic Scholar")
    else:
        try:
            ss_num_cit = query_ss(ref_id, citation_count_only=True)
            cr_num_cit = query_crossref(ref_id, citation_count_only=True)
            msg = (f"\nCitation count for {ref_id}:\n"
                   f"\tSemantic Scholar: {ss_num_cit}\n"
                   f"\t        CrossRef: {cr_num_cit}\n")
        except:
            msg = (f"\nERROR: No results found from either SS or CrossRef")
    print(msg)
