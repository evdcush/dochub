import os
import sys
from slugify import slugify

#-----------------------------------------------------------------------------#
#                                    Paths                                    #
#-----------------------------------------------------------------------------#
# Directory paths
# ===============
_DOCHUB_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = "/".join(_DOCHUB_PATH.split('/')[:-1])
PATH_LIT   = f"{PROJECT_ROOT}/Literature"
PATH_NOTES = f"{PROJECT_ROOT}/Notes"

# File paths
# ----------
LIT_INBOX = f"{PATH_LIT}/inbox.txt"
LIT_BIBTEX = f"{PATH_LIT}/library.bib"
# including a yaml bib until I get bibtex parsing stuff dialed in
LIT_BIBYML = f"{PATH_LIT}/library.yml"
DOC_LOG = f"{_DOCHUB_PATH}/doc.log" # record of use



#-----------------------------------------------------------------------------#
#                                     API                                     #
#-----------------------------------------------------------------------------#

# API urls
# --------
SS_API_URL  = 'https://api.semanticscholar.org/v1/paper/'
#SS_API_URL_PAPER = 'https://api.semanticscholar.org/v1/paper/'
ARX_API_URL = 'http://export.arxiv.org/api/query?id_list='

# TDNs
# ----
DOI_URL     = 'http://doi.org/'
ARX_ABS_URL = 'http://arxiv.org/abs/'
ARX_PDF_URL = 'http://arxiv.org/pdf/'



INFO_KEYS = ['identifier', 'year', 'month', 'title', 'authors', 'arxivId',
             'doi', 'url', 'urlPDF', 'filename', 'keywords', 'abstract']


#-----------------------------------------------------------------------------#
#                                  Functions                                  #
#-----------------------------------------------------------------------------#
# Arxiv utils
scrub_arx_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]

def is_arxiv_id(stripped_id):
    """ arx IDs always have 4 leading digits """
    pre = stripped_id.split('.')[0]
    return len(pre) == 4

def slug_keywords(keywords):
    slugged_kw = [slugify(kw) for kw in keywords]
    return slugged_kw

def slug_title(title):
    """ slugify a space-dilineated title (string)
    NB: DOES NOT LOWERCASE! I prefer titled strings for readability,
        the 'slug' is just to remove all non alpha chars

    Examples
    --------
    title = 'Prefrontal Cortex as a Meta-Reinforcement Learning System'
    slug_title(title)
    >>> Prefrontal_Cortex_as_a_Meta_Reinforcement_Learning_System

    title = '"Cute" Non-descriptive Paper Title: Followed by Descriptive Subtitle'
    slug_title(title)
    >>> Cute_Non_descriptive_Paper_Title_Followed_by_Descriptive_Subtitle
    """
    slug = slugify(title, separator='_', lowercase=False)
    return slug

def format_filename(identifier, title):
    """ filenames are formatted as: lastnameYEAR--This_is_the_Paper_Title
    eg: vaswani2017--Attention_Is_All_You_Need
    """
    fname = identifier + '--' + slug_title(title)
    return fname

def read_inbox_file(inbox_file=LIT_INBOX, clear_inbox=True):
    with open(inbox_file) as ibx:
        ref_ids = ibx.read().split('\n')[1:]

    # TODO
    if clear_inbox:
        pass

    return ref_ids




#-----------------------------------------------------------------------------#
#                                   Samples                                   #
#-----------------------------------------------------------------------------#

arx_samples = ["1710.07035v1",
               "1805.11014v1.pdf",
               "1811.03555",
               "https://arxiv.org/abs/1706.03762",           # attn all u need
               "https://www.arxiv.org/pdf/1802.07740v2.pdf", # machine theory mind
               ]

doi_samples = ["10.1038/nature16961",          # alphago
               "10.1162/089976606775093909",   # comp model learn precor b. ganglia
               "10.1007/978-3-319-67669-2_11", # why firefly work?
               "10.1038/s41593-018-0147-8",    # cortex net
               "10.1016/j.advengsoft.2016.01.008", # whale opt
               "10.1016/j.advengsoft.2013.12.007"  # grey-wolf
               ]

_DOI_SAMPLE = "10.1038/nature16961"              # alphago
_ARX_SAMPLE = "https://arxiv.org/abs/1706.03762" # attention is all you need
