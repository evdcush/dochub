import os
import sys
import traceback
import pyperclip
from slugify import slugify
#from query import query, get_citation_count
import query

class AttrDict(dict):
    # just a dict mutated/accessed by attribute instead index
    # NB: not pickleable
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


#-----------------------------------------------------------------------------#
#                                    Paths                                    #
#-----------------------------------------------------------------------------#
# Directory paths
# ===============
_DOCHUB_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = "/".join(_DOCHUB_PATH.split('/')[:-1])
PATH_LIT   = f"{PROJECT_ROOT}/Literature"
PATH_PAPERS = PATH_LIT + '/Library/Papers'
PATH_NOTES = f"{PROJECT_ROOT}/Notes/Inbox"

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



INFO_KEYS = ['identifier', 'year', 'month', 'title', 'author', 'arxivId',
             'doi', 'url', 'urlPDF', 'filename', 'keywords', 'abstract']


#-----------------------------------------------------------------------------#
#                                  Functions                                  #
#-----------------------------------------------------------------------------#
# DOI / ARXIV arg check
is_doi = lambda ref_id: ref_id[:3] == '10.'
scrub_arx_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]

def check_id(ref_id):
    """ weak arg check to see if id is either doi or arxiv
    returns scrubbed id if valid

    dois assumed to always start '10.'
    arx assumed to either be a well-formed link to arxiv,
    or a bare arxiv id
    """
    if not ref_id[:3] == '10.': # DOI
        ref_id = scrub_arx_id(ref_id)
        yymm = ref_id.split('.')[0] # '1904'
        assert len(yymm) == 4 and yymm.isdigit()
    return ref_id


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
    fname = identifier + '-' + slug_title(title)
    return fname

def read_inbox_file(inbox_file=LIT_INBOX, clear_inbox=True):
    with open(inbox_file) as ibx:
        ref_ids = ibx.read().split('\n')[1:]

    # TODO
    if clear_inbox:
        pass

    return ref_ids

def get_link_from_clipboard():
    url = pyperclip.paste()
    return url

def add_to_inbox(ref_id, inbox_file=LIT_INBOX):
    flag = 'a' if file_exists(inbox_file) else 'w'
    with open(inbox_file, flag) as ibx:
        ibx.write(ref_id + '\n')
    print(f"inboxed {ref_id}")

def gen_notes(info, write_path):
    notes_filename = info['filename'] + '.rst'
    notes_path = f"{write_path}/{notes_filename}"
    #==== file path
    if not file_exists(notes_path):
        notes = documents.Document(info)
        notes.generate_notes()
    else:
        print('Notes already exist!')

def get_citation(info, write_to_bib=False):
    bib = documents.make_bib_entry(info)
    print(bib)
    pyperclip.copy(bib)
    return bib


def get_paper(info, write_path, overwrite=True):
    #==== file path
    paper_filename = info['filename'] + '.pdf'
    paper_path     = f"{write_path}/{paper_filename}"
    if file_exists(paper_path):
        print(f"  {paper_filename} already exists!\n"
               "  proceeding to overwrite")
    downloader.download_from_response(info, paper_path)

#-----------------------------------------------------------------------------#
#                                   Parser                                    #
#-----------------------------------------------------------------------------#
cli = argparse.ArgumentParser()
subparsers = cli.add_subparsers(dest='subcmd')


# Subcommand decorator
# ====================
def argp(*names_or_flags, **kwargs):
    """ subparser args """
    return names_or_flags, kwargs

def subcmd(*parser_args, parent=subparsers):
    """Decorator to define a new subcommand in a sanity-preserving way.

    The function will be stored in the ``func`` variable when the parser
    parses arguments so that it can be called directly like so::
        args = cli.parse_args()
        args.func(args)

    Usage example::
        @subcmd(argp("-d", help="Enable debug mode", action="store_true"))
        def foo(args):
            print(args)

    Then on the command line::
        $ python cli.py foo -d
    """
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for args, kwargs in parser_args:
            parser.add_argument(*args, **kwargs)
        parser.set_defaults(func=func)
    return decorator

'''
#==== main func
if __name__ == '__main__':
    args = cli.parse_args()
    if args.subcmd is None:
        cli.print_help()
    else:
        args.func(args)
'''

# Primary args
# ============
cli.add_argument('id', type=str, nargs='?', default=None, metavar='arx | doi'
    help='ArXiv ID or DOI for a paper; checks clipboard if not provided')

cli.add_argument('-i', '--no_inbox', action='store_true',
    help='do not add ref id to inbox file')

cli.add_argument('-n', '--notes', nargs='?', default=None,
    const=PATH_NOTES, metavar='path/to/notes',
    help='generate notes file in notes dir')

# Subcommand args
# ===============
#@subcmd(argp('id', type=str, metavar='arx | doi', help='count citations'))
@subcmd()
def count(args):
    query.get_citation_count(args.id)
    sys.exit()


@subcmd(argp('-d', '--dpath', nargs='?', default=None, const=PATH_PAPERS,
    help='download paper to dpath'))
def dl(args):
    dpath = args.dpath
    if dpath != PATH_PAPERS:
        dpath = os.path.abspath(dpath)
    # Download
    get_paper(args.info, dpath)


def main():
    args = cli.parse_args()
    sub_command = args.subcmd

    # Process publication ID
    # ======================
    ref_id = args.id
    if ref_id is None:
        try:
            ref_id = get_link_from_clipboard()
        except:
            print('ERROR retrieiving ref id from clipboard')
    ref_id = check_id(ref_id) # will terminate if invalid
    args.id = ref_id

    # Count citations opt
    if sub_command == 'count':
        # count will exit after call
        cli.func(args)


    # Full query
    # ==========
    # Write to inbox
    if not args.no_inbox:
        add_to_inbox(ref_id)

    # query APIs
    info = query.query(ref_id)
    args.info = info

    # get bib entry
    bib_entry = get_citation(info)

    # Download
    if sub_command == 'dl':
        cli.func(args)  # WILL CONTINUE after dl

    # generate notes
    if args.notes is not None:
        npath = args.notes
        if npath != PATH_NOTES:
            npath = os.path.abspath(npath)
        gen_notes(info, npath)

    return 0

if __name__ == '__main__':
    try:
        ret = main()
    except:
        traceback.print_exc()
    sys.exit(ret)


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
