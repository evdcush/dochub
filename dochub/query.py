from collections import OrderedDict
import code
import slugify
import requests
#import feedparser
import utils
from utils import SS_API_URL, ARX_API_URL, DOI_URL, INFO_KEYS


class Query:
    ss_api_url  = "https://api.semanticscholar.org/v1/paper/"
    arx_api_url = "http://export.arxiv.org/api/query?id_list="
    arx_tdn_url = 'http://arxiv.org'
    info_keys = ['identifier', 'year', 'month', 'title', 'authors', 'arxivId',
                 'doi', 'url', 'urlPDF', 'filename', 'keywords', 'abstract']
    def __init__(self, ref_id):
        self.format_query(ref_id)

    @staticmethod
    def scrub_id(u):
        """ extracts arxiv ID """
        return u.strip('htps:/warxiv.orgbdf').split('v')[0]

    @staticmethod
    def is_arxiv_id(ref_id, scrubbed=True):
        # arxiv IDs always have 4 leading digits
        scrubbed_id = ref_id if scrubbed else Query.scrub_id(ref_id)
        pre = scrubbed_id.split('.')[0]
        return len(pre) == 4

    def format_query(self, ref_id):
        """ assigns request url and reference ID based on whether arxiv or doi
        """
        scrubbed_id = self.scrub_id(ref_id)

        # Arxiv
        if self.is_arxiv_id(scrubbed_id):
            self.ref_id = self.arxivId = scrubbed_id
            self.url_ss  = self.ss_api_url + 'arXiv:' + scrubbed_id
            self.url_arx = self.arx_api_url + scrubbed_id
            self.urlPDF = f"{self.arx_tdn_url}/pdf/{scrubbed_id}"
        # doi
        else:
            self.ref_id = self.doi = ref_id  # assumes doi
            self.url_ss = self.ss_api_url + ref_id

    def query_semantic_scholar(self, unknown_ref=False):
        """ queries Semantic Scholar API (https://api.semanticscholar.org/v1/paper/)
        NB: Currently only supporting queries for papers (not authors)

        Unlike the ArXiv API, the response from Semantic Scholar is already
        fairly processed and can be used as-is, hence the attr assignment

        Params
        ------
        ref_id : str
            arxiv ID or DOI; arxiv URLs also accepted
        unknown_ref : bool
            whether API response should include references inaccessible to SS

        Returns
        -------
        API response : dict
            query response data fields:
            ['arxivId', 'authors', 'citationVelocity', 'citations', 'doi',
             'influentialCitationCount', 'paperId', 'references', 'title',
             'topics', 'url', 'venue', 'year']
        """
        #==== Query API
        response = requests.get(self.url_ss)
        status_code = response.status_code
        if status_code != 200:
            raise Exception(f"  {status_code}: HTTP error\n"
                            f"  ref id: {self.ref_id}")
        for attribute, value in response.json().items():
            if value is not None:
                setattr(self, attribute, value)


    def query_arxiv(self):
        """ Retrieves publication info of interest
        If the arxiv paper is available on SS (ie, the SS query was successful),
        this function only extracts the abstract from the arxiv API,
        and uses the info from SS for everything else
        """
        import feedparser
        # Query arxiv API
        # ---------------
        response = feedparser.parse(self.url_arx)

        # Process response
        # ----------------
        status_code = response.get('status')
        if status_code != 200:
            raise Exception(f"  {response.get('status')}: HTTP error\n"
                            f"  ref id: {self.ref_id}")
        response = response['entries'][0]
        self.abstract = response.get('summary', 'Unavailable')

        # If SS query unsuccessful
        if not hasattr(self, 'year'):
            self.year     = response['published'][:4]  # eg: '2017-06-12T17...'
            self.authors  = response['authors']
            self.title    = response['title']
            self.url      = f"{self.arx_tdn_url}/abs/{self.arxivId}"


    def process_response(self):
        """ cherry pick and format data of interest from API response
        Since much of the collection-type data is a dictionary, we want to
        extract only the values of interest into a list
        (eg, the author names, and not their SS author IDs)
        """
        assert hasattr(self, 'year') # ensure parse only called after query

        # Interpreted attributes
        # ----------------------
        author_lname = self.authors[0]['name'].split(' ')[-1].lower()
        self.year = str(self.year)
        self.identifier = f"{author_lname}{self.year}"
        self.filename = utils.format_filename(self.identifier, self.title)
        self.authors  = [author['name'] for author in self.authors]
        if hasattr(self, 'topics'):
            self.keywords = [slugify.slugify(kw['topic']) for kw in self.topics]

        # Processed response attr
        self.info = OrderedDict()
        for key in self.info_keys:
            if hasattr(self, key):
                self.info[key] = getattr(self, key)

    def query(self):
        try:
            self.query_semantic_scholar()
            if hasattr(self, 'url_arx'):
                self.query_arxiv()
        except:
            # Not arxiv ---> doi was invalid
            if not hasattr(self, 'url_arx'):
                raise Exception('Refence ID is neither valid DOI or arxiv ID')
            else:
                self.query_arxiv() # will raise exception if invalid arxiv
        self.process_response()
        return self.info





###############################################################################
#                                                                             #
#    8888888888                                          888                  #
#    888                                                 888                  #
#    888                                                 888                  #
#    8888888    888  888  8888b.  88888b.d88b.  88888b.  888  .d88b.          #
#    888        `Y8bd8P'     "88b 888 "888 "88b 888 "88b 888 d8P  Y8b         #
#    888          X88K   .d888888 888  888  888 888  888 888 88888888         #
#    888        .d8""8b. 888  888 888  888  888 888 d88P 888 Y8b.             #
#    8888888888 888  888 "Y888888 888  888  888 88888P"  888  "Y8888          #
#                                               888                           #
#                                               888                           #
#                                               888                           #
#                                                                             #
#            d8888 8888888b.  8888888                                         #
#           d88888 888   Y88b   888                                           #
#          d88P888 888    888   888                                           #
#         d88P 888 888   d88P   888         SEMANTIC SCHOLAR                  #
#        d88P  888 8888888P"    888                                           #
#       d88P   888 888          888                                           #
#      d8888888888 888          888                                           #
#     d88P     888 888        8888888                                         #
#                                                                             #
#                                                                             #
#  8888888b.                                                                  #
#  888   Y88b                                                                 #
#  888    888                                                                 #
#  888   d88P  .d88b.  .d8888b  88888b.   .d88b.  88888b.  .d8888b   .d88b.   #
#  8888888P"  d8P  Y8b 88K      888 "88b d88""88b 888 "88b 88K      d8P  Y8b  #
#  888 T88b   88888888 "Y8888b. 888  888 888  888 888  888 "Y8888b. 88888888  #
#  888  T88b  Y8b.          X88 888 d88P Y88..88P 888  888      X88 Y8b.      #
#  888   T88b  "Y8888   88888P' 88888P"   "Y88P"  888  888  88888P'  "Y8888   #
#                               888                                           #
#                               888                                           #
#                               888                                           #
#                                                                             #
###############################################################################

"""
#### Full API response ####
(lists values truncated)

ref_id = '1706.03762'
res = query_semantic_scholar(ref_id)

# - - - - - - - - - - - - - - - -

arxivId : str
    the arxiv id, eg: '1706.03762'. Often None for doi queries

# - - - - - - - - - - - - - - - -

authors : list(dict)
    list of paper authors, with fields:
        'authorId' : str; SS author id
            'name' : str; authors name 'First Last'
             'url' : str; SS page for author
    eg:
    [{'authorId': '40348417',
      'name': 'Ashish Vaswani',
      'url': 'https://www.semanticscholar.org/author/40348417'},
     {'authorId': '1846258',
      'name': 'Noam Shazeer',
      'url': 'https://www.semanticscholar.org/author/1846258'},
     {'authorId': '3443442',
      'name': 'Illia Polosukhin',
      'url': 'https://www.semanticscholar.org/author/3443442'}]

# - - - - - - - - - - - - - - - -

citationVelocity : int
    "a weighted average of the publication's citations for
    the last 3 years..., which indicates how popular and
    lasting the publication is"
    eg: 460

# - - - - - - - - - - - - - - - -

citations : list(dict)
    list of publications citing this paper, with fields:
        arxivId, authors, doi, isInfluential, paperId,
        title, url, venue, year
    eg:
    [{'arxivId': '1803.00144',
      'authors': [{'authorId': '40895509',
        'name': 'Trieu H. Trinh',
        'url': 'https://www.semanticscholar.org/author/40895509'},
       {'authorId': '2555924',
        'name': 'Andrew M. Dai',
        'url': 'https://www.semanticscholar.org/author/2555924'},
       {'authorId': '1821711',
        'name': 'Thang Luong',
        'url': 'https://www.semanticscholar.org/author/1821711'},
       {'authorId': '2827616',
        'name': 'Quoc V. Le',
        'url': 'https://www.semanticscholar.org/author/2827616'}],
      'doi': None,
      'isInfluential': True,
      'paperId': '5806e5ab55c4b43a2bd8721e3b7abe3e9a5f335d',
      'title': 'Learning Longer-term Dependencies in RNNs with Auxiliary Losses',
      'url': 'https://www.semanticscholar.org/paper/5806e5ab55c4b43a2bd8721e3b7abe3e9a5f335d',
      'venue': 'ICML',
      'year': 2018},
     {'arxivId': None,
      'authors': [],
      'doi': None,
      'isInfluential': True,
      'paperId': 'b183af31572476e5c33cbc8527b881de3d55899c',
      'title': 'Modern Neural Network Architectures',
      'url': 'https://www.semanticscholar.org/paper/b183af31572476e5c33cbc8527b881de3d55899c',
      'venue': '',
      'year': 2018},
     {'arxivId': '1711.11575',
      'authors': [{'authorId': '47864801',
        'name': 'Han Hu',
        'url': 'https://www.semanticscholar.org/author/47864801'},
       {'authorId': '30107062',
        'name': 'Jiayuan Gu',
        'url': 'https://www.semanticscholar.org/author/30107062'},
       {'authorId': '47294008',
        'name': 'Zheng Zhang',
        'url': 'https://www.semanticscholar.org/author/47294008'},
       {'authorId': '3304536',
        'name': 'Jifeng Dai',
        'url': 'https://www.semanticscholar.org/author/3304536'},
       {'authorId': '1732264',
        'name': 'Yichen Wei',
        'url': 'https://www.semanticscholar.org/author/1732264'}],
      'doi': None,
      'isInfluential': True,
      'paperId': 'c13291eaf9ca1b91ef3feb9d58a9a894130631e3',
      'title': 'Relation Networks for Object Detection',
      'url': 'https://www.semanticscholar.org/paper/c13291eaf9ca1b91ef3feb9d58a9a894130631e3',
      'venue': 'CVPR',
      'year': 2018}]

# - - - - - - - - - - - - - - - -

doi : str | None
    The paper's doi (often None for arXiv papers)

# - - - - - - - - - - - - - - - -

influentialCitationCount : int
    number of citing publications where this paper had
    a significant impact (in other words, citations where this paper was
    very influential)

# - - - - - - - - - - - - - - - -

paperId : str
    unique paper ID hash for this paper on Semantic Scholar, eg:
        if paperId = '0b0cf7e00e7532e38238a9164f0a8db2574be2ea':
            SS_link_to_paper = 'https://www.semanticscholar.org/paper/' + paperId

# - - - - - - - - - - - - - - - -

references : list(dict)
    list of publications (known to SS) citing this paper, with fields:
        arxivId, authors, doi, isInfluential, paperId,
        title, url, venue, year
    eg:
    [{'arxivId': '1608.05859',
      'authors': [{'authorId': '40170001',
        'name': 'Ofir Press',
        'url': 'https://www.semanticscholar.org/author/40170001'},
       {'authorId': '1776343',
        'name': 'Lior Wolf',
        'url': 'https://www.semanticscholar.org/author/1776343'}],
      'doi': None,
      'isInfluential': False,
      'paperId': '1f6358ab4d84fd1192623e81e6be5d0087a3e827',
      'title': 'Using the Output Embedding to Improve Language Models',
      'url': 'https://www.semanticscholar.org/paper/1f6358ab4d84fd1192623e81e6be5d0087a3e827',
      'venue': 'EACL',
      'year': 2017},
     {'arxivId': '1701.06538',
      'authors': [{'authorId': '1846258',
        'name': 'Noam Shazeer',
        'url': 'https://www.semanticscholar.org/author/1846258'},
       {'authorId': '1861312',
        'name': 'Azalia Mirhoseini',
        'url': 'https://www.semanticscholar.org/author/1861312'},
       {'authorId': '50351613',
        'name': 'Krzysztof Maziarz',
        'url': 'https://www.semanticscholar.org/author/50351613'},
       {'authorId': '36347083',
        'name': 'Andy Davis',
        'url': 'https://www.semanticscholar.org/author/36347083'},
       {'authorId': '2827616',
        'name': 'Quoc V. Le',
        'url': 'https://www.semanticscholar.org/author/2827616'},
       {'authorId': '1695689',
        'name': 'Geoffrey E. Hinton',
        'url': 'https://www.semanticscholar.org/author/1695689'},
       {'authorId': '48448318',
        'name': 'Jeff Dean',
        'url': 'https://www.semanticscholar.org/author/48448318'}],
      'doi': None,
      'isInfluential': False,
      'paperId': '436b07bebaa1d1f05ef85415e10374048d25334d',
      'title': 'Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer',
      'url': 'https://www.semanticscholar.org/paper/436b07bebaa1d1f05ef85415e10374048d25334d',
      'venue': 'ArXiv',
      'year': 2017},
     {'arxivId': '1412.7449',
      'authors': [{'authorId': '1689108',
        'name': 'Oriol Vinyals',
        'url': 'https://www.semanticscholar.org/author/1689108'},
       {'authorId': '40527594',
        'name': 'Lukasz Kaiser',
        'url': 'https://www.semanticscholar.org/author/40527594'},
       {'authorId': '3148376',
        'name': 'Terry K Koo',
        'url': 'https://www.semanticscholar.org/author/3148376'},
       {'authorId': '1754497',
        'name': 'Slav Petrov',
        'url': 'https://www.semanticscholar.org/author/1754497'},
       {'authorId': '1701686',
        'name': 'Ilya Sutskever',
        'url': 'https://www.semanticscholar.org/author/1701686'},
       {'authorId': '1695689',
        'name': 'Geoffrey E. Hinton',
        'url': 'https://www.semanticscholar.org/author/1695689'}],
      'doi': None,
      'isInfluential': False,
      'paperId': '289e3e6b84982eb65aea8e3a64f2f6916c98e87e',
      'title': 'Grammar as a Foreign Language',
      'url': 'https://www.semanticscholar.org/paper/289e3e6b84982eb65aea8e3a64f2f6916c98e87e',
      'venue': 'NIPS',
      'year': 2015}]

# - - - - - - - - - - - - - - - -

title : str
    publication title, eg: 'Attention Is All You Need'

# - - - - - - - - - - - - - - - -

topics : list(dict)
    list of topics (keywords) relevant to paper, with fields:
        topic, topicId, url
    eg:
    [{'topic': 'BLEU',
      'topicId': '250421',
      'url': 'https://www.semanticscholar.org/topic/250421'},
     {'topic': 'Transformer',
      'topicId': '6977',
      'url': 'https://www.semanticscholar.org/topic/6977'},
     {'topic': 'Machine translation',
      'topicId': '34995',
      'url': 'https://www.semanticscholar.org/topic/34995'},
     {'topic': 'Convolutional neural network',
      'topicId': '29860',
      'url': 'https://www.semanticscholar.org/topic/29860'},
     {'topic': 'Encoder',
      'topicId': '16744',
      'url': 'https://www.semanticscholar.org/topic/16744'},
     {'topic': 'Parsing',
      'topicId': '1910',
      'url': 'https://www.semanticscholar.org/topic/1910'},
     {'topic': 'Network architecture',
      'topicId': '58473',
      'url': 'https://www.semanticscholar.org/topic/58473'},
     {'topic': 'Convolution',
      'topicId': '571',
      'url': 'https://www.semanticscholar.org/topic/571'},
     {'topic': 'Transduction (machine learning)',
      'topicId': '18628',
      'url': 'https://www.semanticscholar.org/topic/18628'},
     {'topic': 'Graphics processing unit',
      'topicId': '8807',
      'url': 'https://www.semanticscholar.org/topic/8807'},
     {'topic': 'Artificial neural network',
      'topicId': '6213',
      'url': 'https://www.semanticscholar.org/topic/6213'}]

# - - - - - - - - - - - - - - - -

url : str
    link to publication on semantic scholar, which is just
    "https://www.semanticscholar.org/paper/" + paperId
    eg:
    'https://www.semanticscholar.org/paper/0b0cf7e00e7532e38238a9164f0a8db2574be2ea'

# - - - - - - - - - - - - - - - -

venue : str
    where the paper was published or featured. Typically this means the
    journal, such as 'ArXiv', 'Nature', etc..., but if the paper was
    featured in a conference, venue may be the conference name, for example
    this paper's venue: 'NIPS'

# - - - - - - - - - - - - - - - -

year : int
    year of publication, eg 2017

"""
