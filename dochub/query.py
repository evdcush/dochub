from collections import OrderedDict
import code
import fire
import requests
import pyperclip
import feedparser
from slugify import slugify

from utils import SS_API_URL, ARX_API_URL, DOI_URL, scrub_arx_id, is_arxiv_id



#-----------------------------------------------------------------------------#
#                                    Arxiv                                    #
#-----------------------------------------------------------------------------#
def ss_keyword_query(arx_id):
    #'https://api.semanticscholar.org/v1/paper/'
    req_url = f"{SS_API_URL}arXiv:{arx_id}"
    response = requests.get(req_url)
    result = response.json()
    kw = [topic['topic'] for topic in result['topics']]
    return kw

# Querying
# ========
def arx_query(raw_arx_id):
    arx_id = scrub_arx_id(raw_arx_id)
    query_url = f"{ARX_API_URL}{arx_id}"

    # Query arxiv API
    # ---------------
    response = feedparser.parse(query_url)

    # Process response
    # ----------------
    if response.get('status') != 200:
        raise Exception("HTTP error for given request")
    result = response['entries'][0]
    return result


def parse_arx(res):
    # Get all relevant info
    # ---------------------
    year, month = res['published'][:7].split('-')  # eg: '2017-06-12T17:57:34Z'
    authors = [auth['name'] for auth in res['authors']]
    abstract = res['summary']
    title   = res['title']

    # interpretted stuff
    # ------------------
    link = res['link']
    url  = link if link[-2] != 'v' else link[:-2]  # do not keep versioned links
    arx_id  = url.split('/')[-1]
    url_pdf = f"http://arxiv.org/pdf/{arx_id}"
    identifier = authors[0].split(' ')[-1].lower() + year  # eg: graves2014

    # get kw from semscholar
    keywords = ss_keyword_query(arx_id)

    # map info
    # --------
    info = OrderedDict(identifier=identifier, year=year, title=title,
                       author=authors, arxivId=arx_id, url=url, urlPDF=url_pdf,
                       keywords=keywords, abstract=abstract)
    return info

#-----------------------------------------------------------------------------#
#                           Semantic scholar (doi)                            #
#-----------------------------------------------------------------------------#
def semscholar_query(doi):
    #'https://api.semanticscholar.org/v1/paper/'
    req_url = f"{SS_API_URL}{doi}"
    response = requests.get(req_url)
    result = response.json()
    return result

def parse_ss(res):
    info = OrderedDict()
    # Get all relevant info
    # ---------------------
    year       = str(res['year'])
    author     = [auth['name'] for auth in res['authors']]
    identifier = author[0].split(' ')[-1].lower() + year
    title      = res['title']
    doi        = res['doi']
    keywords   = [topic['topic'] for topic in res['topics']]

    info = OrderedDict(identifier=identifier, year=year, title=title,
                       author=author, keywords=keywords, doi=doi)

    # URL interpret
    # -------------
    # check if arxiv pub
    arx_id = res['arxivId']
    if arx_id is not None:
        arx_url = "http://arxiv.org/{}/" + str(arx_id)
        url = arx_url.format('abs')
        url_pdf = arx_url.format('pdf')
        # update info
        info['arxivId'] = str(arx_id)
        info['url']     = url
        info['urlPDF']  = url_pdf
    else:
        info['url'] = DOI_URL + res['doi']
    return info

def format_filename(info):
    #code.interact(local=dict(globals(), **locals()))
    fname = info['identifier'] + '__' + slugify(info['title'])
    return fname

#-----------------------------------------------------------------------------#
#                                  Wrappers                                   #
#-----------------------------------------------------------------------------#

def arxq(arxid):
    res = arx_query(arxid)
    pub_info = parse_arx(res)
    return pub_info

def sscholarq(doi):
    res = semscholar_query(doi)
    pub_info = parse_ss(res)
    return pub_info

def query(pub_id):
    sid = scrub_arx_id(pub_id)
    info = arxq(sid) if is_arxiv_id(sid) else sscholarq(pub_id)
    info['filename'] = format_filename(info)
    return info

doi_samp = "10.1038/nature16961"
arx_samp = "https://arxiv.org/abs/1706.03762"
