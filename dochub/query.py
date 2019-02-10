import sys
import code
import requests
from unidecode import unidecode
from slugify import slugify


#-----------------------------------------------------------------------------#
#                               Query constants                               #
#-----------------------------------------------------------------------------#
# urls
# ====
doi_url = "http://doi.org/"
ss_api_paper_url    = "https://api.semanticscholar.org/v1/paper/"
arxiv_api_paper_url = "http://export.arxiv.org/api/query?id_list="

class AttrDict(dict):
    """ dict that has dot access """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

#-----------------------------------------------------------------------------#
#                               Utils & Helpers                               #
#-----------------------------------------------------------------------------#
# String stuff
# ============
scrub_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]
to_ascii = lambda s: unidecode(s) # to_ascii('çivicioglu') --> 'civicioglu'


# Formatting
# ==========
is_doi = lambda ref_id: ref_id[2] == '.'
arxiv_abs = lambda arx_id: f"https://arxiv.org/abs/{arx_id}"
arxiv_pdf = lambda arx_id: f"https://arxiv.org/pdf/{arx_id}"


# Parse helpers
# =============
def check_status(status_code):
    if status_code != 200:
        raise Exception(f"\tHTTP Error {status_code}\n")

def extract_authors(response):
    return [to_ascii(author['name']) for author in response['authors']]

def format_identifier(info):
    name = info.author[0].split(' ') # splits first author's name
    identifier = f"{name[-1]}_{name[0][0]}-{info.year}"
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

def query_ss(ref_id):
    """ Query Semantic Scholar (SS) API for given paper reference id

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


    Params
    ------
    ref_id : str
        either a DOI or an arXiv ID

    Returns
    -------
    response : dict
        api json response
    """
    #==== format query url
    req_url = ss_api_paper_url
    ref_is_doi = is_doi(ref_id)
    if not ref_is_doi:
        ref_id = scrub_id(ref_id)
        req_url += 'arXiv:'
    req_url += ref_id

    #==== query
    response = requests.get(req_url)
    status_code = response.status_code
    check_status(status_code)
    response = response.json()
    return response

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
        info.keywords = [slugify(kw['topic']) for kw in response['topics']]

    # arxiv content
    arxivId = response['arxivId']
    if arxivId:
        info.arxivId = arxivId
        info.URL = arxiv_abs(arxivId)
        info.pdf = arxiv_pdf(arxivId)
        arx_resp = query_arxiv(arxivId)
        info.abstract = process_arxiv(arx_resp, abs_only=True)
    return info




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
    except:
        msg = f"""\
        \tQuery unsuccessful for {ref_id}
        \tif valid reference id, then it may not be available
        \tin the semantic scholar database"""
        raise Exception(msg)
