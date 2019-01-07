import fire
import requests
import pyperclip
import feedparser

from documents import make_bib
from conf import SS_API_URL, ARX_API_URL, DOI_URL
from utils import scrub_arx_id



# Arxiv processing stuff
# ======================
def is_arxiv_id(stripped_id):
    """ arx IDs always have 4 leading digits """
    pre = stripped_id.split('.')[0]
    return len(pre) == 4

#-----------------------------------------------------------------------------#
#                                    Arxiv                                    #
#-----------------------------------------------------------------------------#

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

    # map info
    # --------
    info = dict(year=year, author=authors, abstract=abstract, title=title,
                url=url, urlPDF=url_pdf, arxivId=arx_id, identifier=identifier)
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
    info = {}
    # Get all relevant info
    # ---------------------
    info['year']       = str(res['year'])
    info['author']     = [auth['name'] for auth in res['authors']]
    info['identifier'] = info['author'][0].split(' ')[-1].lower() + info['year']
    info['title']      = res['title']
    info['doi']        = res['doi']
    info['keywords']   = [topic['topic'] for topic in res['topics']]

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


def arxq(arxid):
    res = arx_query(arxid)
    pub_info = parse_arx(res)
    #arx_bib  = make_bib_dynamic(pub_info)
    #arx_bib = make_bib(pub_info)
    #print(arx_bib)
    #pyperclip.copy(arx_bib)
    return pub_info

def sscholarq(doi):
    res = semscholar_query(doi)
    pub_info = parse_ss(res)
    return pub_info
    #ss_bib = make_bib(pub_info)
    #print(ss_bib)

def query(pub_id):
    sid = scrub_arx_id(pub_id)
    if is_arxiv_id(sid):
        info = arxq(sid)
    else:
        info = sscholarq(pub_id)
    bib = make_bib(info)
    print(bib)
    pyperclip.copy(bib)

doi_samp = "10.1038/nature16961"
arx_samp = "https://arxiv.org/abs/1706.03762"
