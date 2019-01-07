
scrub_arx_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]

def is_arxiv_id(stripped_id):
    """ arx IDs always have 4 leading digits """
    pre = stripped_id.split('.')[0]
    return len(pre) == 4




#====================================================================================#
#   ____    ____    _____  __     __    ____     ____   ____    ___   ____    _____  #
#  |  _ \  |  _ \  | ____| \ \   / /   / ___|   / ___| |  _ \  |_ _| |  _ \  |_   _| #
#  | |_) | | |_) | |  _|    \ \ / /    \___ \  | |     | |_) |  | |  | |_) |   | |   #
#  |  __/  |  _ <  | |___    \ V /      ___) | | |___  |  _ <   | |  |  __/    | |   #
#  |_|     |_| \_\ |_____|    \_/      |____/   \____| |_| \_\ |___| |_|       |_|   #
#                                                                                    #
#====================================================================================#
"""
was for arxiv stuff only, and supports full search query
adapt whatever needed
"""
#====================================================================================#
#====================================================================================#
#====================================================================================#
#====================================================================================#

'''
import os
import sys
import yaml
import argparse
from requests.exceptions import HTTPError
from urllib.request import urlretrieve
from urllib.parse import quote_plus, urlencode
import feedparser
import code


#=============================================================================#
#                                                                             #
#                  ██████   █████  ████████ ██   ██ ███████                   #
#                  ██   ██ ██   ██    ██    ██   ██ ██                        #
#                  ██████  ███████    ██    ███████ ███████                   #
#                  ██      ██   ██    ██    ██   ██      ██                   #
#                  ██      ██   ██    ██    ██   ██ ███████                   #
#                                                                             #
#=============================================================================#

# Query constants
# ===============
API_URL = 'http://export.arxiv.org/api/query?{}'
sample_paper_url = 'https://arxiv.org/abs/1706.03762' # all you need is attention
#query_kwargs = dict(search_query="", start=0, max_responses=10, sort_by="relevance", sort_order="descending")
#'http://export.arxiv.org/api/query?search_query=&start=0&max_responses=10&sort_by=relevance&sort_order=descending&id_list=1706.03762'

# Path to root project dir
# ========================
PROJECT_CODE_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_PATH = '/'.join(PROJECT_CODE_PATH.split('/')[:-1])
conf_file = PROJECT_CODE_PATH + '/configs/config.yml'


#=============================================================================#
#                                                                             #
#                     ███████ ██    ██ ███    ██  ██████                      #
#                     ██      ██    ██ ████   ██ ██                           #
#                     █████   ██    ██ ██ ██  ██ ██                           #
#                     ██      ██    ██ ██  ██ ██ ██                           #
#                     ██       ██████  ██   ████  ██████                      #
#                                                                             #
#=============================================================================#


class AttrDict(dict):
    # just a dict mutated/accessed by attribute instead index
    # NB: not pickleable
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def ld_yaml(ypath):
    with open(ypath) as stream:
        yml = yaml.load(stream)
        return yml

def wr_yaml(obj, ypath):
    with open(ypath, 'x') as stream:
        yaml.dump(obj, stream)


# Load user conf
# ==============
raw_conf = ld_yaml(conf_file)
conf = raw_conf['user_conf']
CONFIG = AttrDict({k: f'{PROJECT_PATH}/{v}' for k,v in conf.items()})


#=============================================================================#
#                                                                             #
#                  ██████   █████  ██████  ███████ ███████                    #
#                  ██   ██ ██   ██ ██   ██ ██      ██                         #
#                  ██████  ███████ ██████  ███████ █████                      #
#                  ██      ██   ██ ██   ██      ██ ██                         #
#                  ██      ██   ██ ██   ██ ███████ ███████                    #
#                                                                             #
#=============================================================================#
parser = argparse.ArgumentParser()

# Sort options in API query
# =========================
sort_by = ['relevance', 'lastUpdatedDate', 'submittedDate']
sort_order = ['ascending', 'descending']

# Argparser; query defaults
# =========================
adg = parser.add_argument


class QueryParser:
    def __init__(self, user_conf=CONFIG):
        self.parser = argparse.ArgumentParser()
        self.user_config = user_conf
        self.add_args()

    def add_args(self):
        adg = self.parser.add_argument
        #==== arXiv API query opts
        adg('-i', '--id_list',     nargs='+', default=[])
        adg('-q', '--search_query', type=str, default='')
        adg('-s', '--start',        type=int, default=0)
        adg('-m', '--max_results',  type=int, default=10)
        adg('-b', '--sort_by',      type=str, default='relevance', choices=sort_by)
        adg('-o', '--sort_order',   type=str, default='descending', choices=sort_order)

        #==== user opts
        adg('-f', '--from_file',     type=str, default='/home/evan/.NSync/Resources/inbox_read.yml')#self.user_config.paper_inbox_file) # default, if id_list empty
        adg('-w', '--download_dir',  type=str, default=self.user_config.papers_dir)
        adg('-n', '--notes_dir',     type=str, default=self.user_config.notes_inbox_dir)
        adg('-x', '--bibtex_file',   type=str, default=self.user_config.library_bibtex)
        adg('-g', '--glossary_file', type=str, default=self.user_config.glossary_file)
        adg('-r', '--readme_file',   type=str, default=self.user_config.readme_file)

    def parse_args(self, *args):
        """ parse args and build query """
        args = self.parser.parse_args(*args)
        self.process_args(args)

    def process_args(self, args):
        # Process arXiv IDs
        # =================
        if len(args.id_list) == 0:
            #==== if no urls / ids passed to id_list, get from file
            paper_urls = ld_yaml(args.from_file)['arxiv']
            args.id_list = self.get_arx_ids_from_url_list(paper_urls)
            #if len(paper_urls) == 0:
            #    #==== Check whether valid query can be made from args
            #    if args.search_query == '':
            #        raise Exception('Please submit a query item '
            #            'through "--search_query", "--id_list", \n'
            #            'or a non-empty yaml file of urls/ids keyed to "arxiv" via "--from_file"')
            #else:
            #    args.id_list = self.get_arx_ids_from_url_list(paper_urls)
        else:
            args.id_list = self.get_arx_ids_from_url_list(args.id_list)
        self.args = args

    @staticmethod
    def get_arx_id_from_url(url):
        # strips everything from url except ID (also accepts already formatted IDs)
        return url.strip('htps:/arxiv.orgbdf').split('v')[0]

    def get_arx_ids_from_url_list(self, url_list):
        """ Strips each url in list to it's ID
        (safe for already properly strpped IDs as well)
        Returns: a string of all IDs, comma-dilineated for url_encoding
        """
        # get arxiv ids from a list of arxiv urls
        ID_set = set() # no duplicates
        for url in url_list:
            arx_id = self.get_arx_id_from_url(url)
            ID_set.add(arx_id)
        return ','.join(ID_set)

    def build_arxiv_query(self):
        args = self.args
        query_kwargs = dict(id_list=args.id_list,
                            search_query=args.search_query,
                            start=args.start,
                            max_results=args.max_results,
                            sort_by=args.sort_by,
                            sort_order=args.sort_order)
        url_encoding = urlencode(query_kwargs)
        self.arxiv_query = API_URL.format(url_encoding)


#=============================================================================#
#                                                                             #
#                  ██████  ██    ██ ███████ ██████  ██    ██                  #
#                 ██    ██ ██    ██ ██      ██   ██  ██  ██                   #
#                 ██    ██ ██    ██ █████   ██████    ████                    #
#                 ██ ▄▄ ██ ██    ██ ██      ██   ██    ██                     #
#                  ██████   ██████  ███████ ██   ██    ██                     #
#                     ▀▀                                                      #
#                                                                             #
#=============================================================================#

# unneeded arXiv info
PRUNE_KEYS = ['updated_parsed', 'published_parsed', 'arxiv_primary_category',
              'summary_detail', 'author', 'author_detail', 'guidislink',
              'title_detail', 'tags', 'id']
FILE_NAME_AUTHOR_CUTOFF = 3

class ArxivQuery:
    def __init__(self, arxiv_query_url):
        self.arxiv_query_url = arxiv_query_url

    def query_arxiv(self):
        # Send request to arXiv API
        # -------------------------
        response = feedparser.parse(self.arxiv_query_url)

        # Check if request was successful
        # -------------------------------
        response_status = response.get('status')
        if response_status != 200:
            raise Exception(f"QUERY: HTTP Error \n"
                f"{str(response.get('status', 'no status'))}")
        self.response = response['entries']
        self.process_query_response()

    def process_query_response(self):
        self.prune_response()
        self.entries = []
        for entry in self.response:
            self.entries.append(self.process_entry(entry))


    def prune_response(self):
        # Not sure this is necessary, since we extract what we want
        #  in process_entry already
        for entry in self.response:
            for k in PRUNE_KEYS:
                entry.pop(k, None)

    @staticmethod
    def process_entry(entry):
        """ Get information of interest from API response entry
        #=== Desired info:
          *   PDF url : url to PDF file of paper
          * Arxiv url : url to arxiv page for paper (abstract)
          *     title : paper title
          *  abstract : paper abstract
          *      year : year the paper was published to arxiv
          *   authors : paper authors
        #=== Optional info: (not always available)
          * journal ref : paper journal ref
          *         doi : paper doi code
        Params
        ------
        response : dict <str>
            dictionary (json) of all information about a paper from the API
        """
        info = {}

        # Get pdf links
        # -------------
        for link in entry['links']:
            if link.get('title', False) == 'pdf':
                info['pdf_url'] = link['href']

        # Get paper info
        # --------------
        info['arxiv_url'] = entry.pop('link')
        info['title']     = entry.pop('title').strip()
        info['abstract']  = entry.pop('summary').replace('\n', ' ') # space char
        info['year']      = entry.pop('published')[:4] # eg '2017-07-27T08:18:33Z'
        info['authors']   = [a['name'] for a in entry['authors']]
        info['arxiv_id']  = info['arxiv_url'].split('/')[-1]

        # Optional info
        # -------------
        if 'arxiv_doi' in entry:
            info['doi'] = entry.pop('arxiv_doi')
        if 'arxiv_journal_ref' in entry:
            info['journal_ref'] = entry.pop('arxiv_journal_ref')
        return info

    def format_title(self, raw_title):
        """
        2015--Fernando.C_et.al--My_Paper_is_About_This_Thing--1504.1395.pdf
        'Schema Networks: Zero-shot Transfer with a Generative Causal Model of\n  Intuitive Physics'
        'Schema_Networks-_Zero-shot_Transfer with a Generative Causal Model of\n  Intuitive Physics'
        """
        max_len = 95
        double_space = '  '
        title = raw_title.strip().replace('\n', '')
        #=== get rid of excessive whitespace
        while double_space in title:
            title = title.replace(double_space, ' ')

        #=== replace spaces with underscores;
        #    titles with colon are double-spaced @ colon
        title = title.replace(' ', '_').replace(':', '_')

        #=== truncate the long boyes
        affix = '--' if len(title) < max_len else '-_-'
        title = title[:max_len-1] + affix
        return title

    def format_authors(self, authors_list):
        """ Authors format:
        single-author: Lastname_Firstname
        authors <= 3: Lastname.F_Lastname.F_Lastname.F
        authors > 3: FirstAuthorLastname.F_et.al

        NOTE: "not supported" means the filename for authors will be incorrect
            Middle names, honorifics, initials, and
            multi-part names (eg 'de Freitas', 'Van den Oord')
            are not supported yet
            - surnames are assumed to come last;
              - languages where surname is first are not supported
              - affixed titles or honorifics are not supported
                (eg, phd, md, sir, etc..)
        """
        def _get_name(a):
            aname = a.split(' ')
            fname, lname = aname[0], aname[-1]
            return fname, lname

        num_auth = len(authors_list)
        if num_auth == 1:
            fname, lname = _get_name(authors_list[0])
            authors = f'{lname}_{fname}--'
        elif num_auth <= FILE_NAME_AUTHOR_CUTOFF:
            authors = ''
            for auth in authors_list:
                fname, lname = _get_name(auth)
                authors += f'{lname}.{fname[0]}_'
            authors = authors[:-1] + '--'
        else:
            fname, lname = _get_name(authors_list[0])
            authors = f'{lname}.{fname[0]}_et.al--'
        return authors


    def format_filenames(self):
        #if valid_query_info(info):
        for info in self.entries:
            # Get filename details
            # --------------------
            year    = f"{info['year']}--"
            authors = self.format_authors(info['authors'])
            title   = self.format_title(info['title'])
            arx_id  = info['arxiv_id']
            # Format filename
            # ---------------
            # {year}--{authors}--{title}--{arx_id}.pdf
            file_name = f"{year}{authors}{title}{arx_id}"
            info['file_name'] = file_name
            print(f"Finished processing {file_name}")


#=============================================================================#
#                                                                             #
#   ██████   ██████  ██     ██ ███    ██ ██       ██████   █████  ██████      #
#   ██   ██ ██    ██ ██     ██ ████   ██ ██      ██    ██ ██   ██ ██   ██     #
#   ██   ██ ██    ██ ██  █  ██ ██ ██  ██ ██      ██    ██ ███████ ██   ██     #
#   ██   ██ ██    ██ ██ ███ ██ ██  ██ ██ ██      ██    ██ ██   ██ ██   ██     #
#   ██████   ██████   ███ ███  ██   ████ ███████  ██████  ██   ██ ██████      #
#                                                                             #
#=============================================================================#



class DocDownloader:
    def __init__(self, entries, path_conf=CONFIG):
        self.entries = entries
        self.dst_paper = path_conf.papers_dir
        self.dst_notes = path_conf.notes_inbox_dir
        self.lib_bib   = path_conf.library_bibtex

    def download_files(self):
        for entry in self.entries:
            fname = f"{self.dst_paper}/{entry['file_name']}.pdf"
            urlretrieve(entry['pdf_url'], fname)
            self.make_notes(entry)

    def update_bibtex(self, entry):
        pass

    def update_readme(self, entry):
        pass

    def make_notes(self, entry):
        title = entry['title']
        abstract = entry['abstract']
        arx_id = entry['arxiv_id']
        year = entry['year']
        authors = entry['authors']
        filename = entry['file_name']
        original_link = entry['arxiv_url']
        paper_link_arx = entry['pdf_url']
        paper_link_local = self.dst_paper + '/' + filename + '.pdf'
        notes_dir = self.dst_notes
        notes_file = f"{notes_dir}/{filename}.rst"
        # format authors
        author_print = ', '.join([f"{a.split(' ')[0][0]}. {a.split(' ')[-1]}" for a in authors[:3]])
        #==== Make rst
        notes = open(notes_file, 'x')
        wr = lambda s: notes.write(s + '\n')
        wr('.. meta::')
        wr('    :keywords: ')
        wr('')
        # print title and authors
        title_line = '#' * len(title)
        authors_line = '~' * len(author_print)
        wr(f"{title_line}\n{title}\n{title_line}")
        wr(f"{authors_line}\n{author_print}\n{authors_line}")
        wr('')
        wr(f':arxiv_link: |arXivID|_')
        wr(f':local_pdf: paper_')
        wr('')
        wr('.. rubric:: **一言でいうと:**')
        wr('.. admonition:: Abstract')
        wr('')
        wr(f'    {abstract}')
        wr('')
        wr('')
        wr('Summary\n=======')
        wr('- lorem ipsum dolor sit amet')
        wr('- Maecenas turpis leo, gravida')
        wr('')
        wr('')
        wr('Method\n------')
        wr('- poseure mattis lectus')
        wr('- curabitur ut mauris nec')
        wr('')
        wr('')
        wr('Notes\n-----')
        wr('Etiam accumsan sapien nec ex porta semper. Nulla sed augue sagittis, laoreet odio imperdiet')
        wr('\n\n\n')
        wr('See Also\n^^^^^^^^')
        wr('this paper like this or github code')
        wr('\n\n')
        wr('References\n-----------')
        wr('\n.. Substitutions\n')
        wr(f'.. |arXivID| replace:: {arx_id}')
        wr(f'.. _arXivID: {original_link}')
        wr(f'.. _paper: {paper_link_local}')
        notes.close()


#=============================================================================#
#         ███    ██ ██      ██████      ███    ███ ██ ███████  ██████         #
#         ████   ██ ██      ██   ██     ████  ████ ██ ██      ██              #
#         ██ ██  ██ ██      ██████      ██ ████ ██ ██ ███████ ██              #
#         ██  ██ ██ ██      ██          ██  ██  ██ ██      ██ ██              #
#         ██   ████ ███████ ██          ██      ██ ██ ███████  ██████         #
#                                                                             #
#=============================================================================#
import summa
from summa import summarizer, keywords
from nltk.stem import WordNetLemmatizer

sample = ("Rewards are sparse in the real world and most today's reinforcement learning "
        "algorithms struggle with such sparsity. One solution to this problem is to "
        "allow the agent to create rewards for itself - thus making rewards dense and "
        "more suitable for learning. In particular, inspired by curious behaviour in "
        "animals, observing something novel could be rewarded with a bonus. Such bonus "
        "is summed up with the real task reward - making it possible for RL algorithms "
        "to learn from the combined reward. We propose a new curiosity method which uses "
        "episodic memory to form the novelty bonus. To determine the bonus, the current "
        "observation is compared with the observations in memory. Crucially, the "
        "comparison is done based on how many environment steps it takes to reach the "
        "current observation from those in memory - which incorporates rich information "
        "about environment dynamics. This allows us to overcome the known \"couch-potato\" "
        "issues of prior work - when the agent finds a way to instantly gratify itself "
        "by exploiting actions which lead to hardly predictable consequences. We test "
        "our approach in visually rich 3D environments in ViZDoom, DMLab and MuJoCo. In "
        "navigational tasks from ViZDoom and DMLab, our agent outperforms the "
        "state-of-the-art curiosity method ICM. In MuJoCo, an ant equipped with our "
        "curiosity module learns locomotion out of the first-person-view curiosity only.")

#=== Default is accurate
summ = summarizer.summarize(sample) # ratio is default 0.2

#=== But 0.6 ratio really hits all the main points better than rest
summ6 = summarizer.summarize(sample)

# Keywords
kw = keywords.keywords(sample) # doesn't appear to lemmatize


""" PLAN
NEVERMIND, just do this when you have everything else dialed in

* similarity scores based on abstracts
* similarity scores based on shared references (overlap)
* similarity scores based on keywords in text
    - WOULD REQUIRE PARSING PDF no f'n way, huge PITA

********** SEMANTIC SCHOLAR PROVIDES KEYWORDS THROUGH 'TOPICS' in API

"""



'''
