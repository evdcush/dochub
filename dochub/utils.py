import os
import sys

#-----------------------------------------------------------------------------#
#                                    Paths                                    #
#-----------------------------------------------------------------------------#
# Directory paths
# ===============
_DOCHUB_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = "/".join(_DOCHUB_PATH.split('/')[:-1])
LIT_PATH   = f"{PROJECT_ROOT}/Literature"
NOTES_PATH = f"{PROJECT_ROOT}/Notes"

# File paths
# ----------
LIT_INBOX = f"{LIT_PATH}/inbox.yml"
LIT_BIB   = f"{LIT_PATH}/library.bib"


# API urls
# --------
SS_API_URL  = 'https://api.semanticscholar.org/v1/paper/'
ARX_API_URL = 'http://export.arxiv.org/api/query?id_list='

# TDNs
# ----
DOI_URL     = 'http://doi.org/'
ARX_ABS_URL = 'http://arxiv.org/abs/'
ARX_PDF_URL = 'http://arxiv.org/pdf/'

# Samples
# -------
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

_DOI_SAMPLE = "10.1038/nature16961"
_ARX_SAMPLE = "https://arxiv.org/abs/1706.03762"

#-----------------------------------------------------------------------------#
#                                  Functions                                  #
#-----------------------------------------------------------------------------#
# Arxiv utils
scrub_arx_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]

def is_arxiv_id(stripped_id):
    """ arx IDs always have 4 leading digits """
    pre = stripped_id.split('.')[0]
    return len(pre) == 4


