import code
from utils import is_arxiv_id, scrub_arx_id
from conf import NOTES_PATH, LIT_PATH
from collections import OrderedDict

#-----------------------------------------------------------------------------#
#                                Bibliography                                 #
#-----------------------------------------------------------------------------#
LEFT_MARGIN = 9
ENDLINE = '\",\n'
MARGIN_JUST = "\n".ljust(len('"abstract = "'))

def format_collection(lst):
    string = ""
    for i, entry in enumerate(lst):
        if (i+1) % 5 == 0:
            string += MARGIN_JUST + entry
        else:
            string += entry
        if entry != lst[-1]:
            string += ', '
    return string

def format_abstract(abstract):
    fmat_abs = MARGIN_JUST.join(abstract.split('\n'))
    return fmat_abs


def format_arx_info(info_in):
    arx_key_order = ['identifier', 'year', 'author', 'title',
                     'arxivId', 'url', 'urlPDF', 'abstract']
    info = OrderedDict()
    for k in arx_key_order:
        info[k] = info_in[k]
    #info = {**info_in}  # copy
    # Convert collections to string
    info['abstract'] = format_abstract(info['abstract'])
    info['author']    = format_collection(info['author'])
    return info


def format_doi_info(info_in):
    doi_key_order = ['identifier', 'year', 'author', 'title', 'doi',
                     'arxivId', 'url', 'urlPDF', 'keywords', 'abstract']
    info = OrderedDict()
    for k in doi_key_order:
        if k in info_in:
            info[k] = info_in[k]

    info['author']   = format_collection(info['author'])
    info['keywords'] = format_collection(info['keywords'])
    if 'abstract' in info:
        info['abstract'] = format_abstract(info['abstract'])
    return info


def make_bib(info_in):
    if 'doi' in info_in:
        info = format_doi_info(info_in)
    else:
        info = format_arx_info(info_in)
    bib = "@Article{" + info['identifier'] + '\n'
    for k, v in info.items():
        if k == 'identifier': continue
        arxline = k.ljust(LEFT_MARGIN) + '= "' + v + ENDLINE
        bib += arxline
    bib += '}'
    return bib

#-----------------------------------------------------------------------------#
#                                    Notes                                    #
#-----------------------------------------------------------------------------#


# Static
# ======
_N = '\n'
_META = ".. meta::"
_KEYWORDS = "    :keywords: "
_ARX_SUB = ":arXiv_link: |arXivID|_"
_LOCAL_SUB = ":local_pdf: paper_"
#_OTHER_LINK = ":paper_link: |paper_title|_"

# Interpreted
# ===========
SHORT = "\n.. rubric:: **一言でいうと:**"
ABS = "\n.. admonition:: Abstract\n\n    {}\n"

# substitutions
ARX_ID   = ".. |arXivID| replace:: {}" # arXiv ID
ARX_LINK = ".. _arXivID: {}" # Link to arxiv page
LOCAL_LINK = ".. _paper: {}" # link to local pdf copy of paper


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Line:
    H0 = '#'
    H1 = '*'
    H2 = '='
    H3 = '-'
    H4 = '^'
    H5 = '~'
    TR = '--------' # transition marker

    def get_char(self, level):
        assert (0 <= level <= 5) and isinstance(level, int)
        h = getattr(self, f'H{level}')
        return h

    def section(self, text, level=2):
        """ returns a section title with appropriate line(s) """
        #=== line formatting
        h = self.get_char(level)
        length = len(text)
        line = h * length

        #=== title formatting
        title = f"{text}\n{line}"
        if level < 2: # overline
            title = f"{line}\n{title}"
        return title

    def divider(self):
        return f"\n{self.TR}\n"

    def __call__(self, text, level=2):
        return self.section(text, level)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# WIP
class Document:
    def __init__(self, info, path=NOTES_PATH):
        self.info = info
        self.filename = f"{path}/{info['filename']}.rst"

    def format_keywords(self):
        kw = ''
        if 'keywords' in self.info:
            kw = ', '.join([w.lower() for w in self.info['keywords']])
        return kw

    def format_abs(self):
        abstract = 'NONE'
        if 'abstract' in self.info:
            abstract = '\n    '.join(self.info['abstract'].split('\n'))
        return abstract

    def generate_notes(self):
        # get content of interest
        info = self.info
        title   = info['title']
        authors = ", ".join(info['author'])
        year    = info['year']
        url     = info['url']
        keywords = self.format_keywords()
        #abstract = info.get('abstract', 'No Abstract')
        abstract = self.format_abs()
        pub_id   = info['arxivId'] if 'arxivId' in info else info['doi']

        # write file
        line = Line()
        file = open(self.filename, 'w')
        wr = lambda s: file.write(s + '\n')
        wr(_META)
        wr(f"{_KEYWORDS} {keywords}")
        wr(_N)
        wr(line(title, 0))
        #wr(line(authors, 1))
        wr(f"\n **{authors}**")
        wr(_N)
        wr(SHORT + '\n')
        wr(ABS.format(abstract))
        wr(line('Key Points', 2))
        wr(_N)
        wr(line('Additional Notes', 3))
        wr(_N)
        wr(line('Reference', 2))
        wr(f" - publication ID: {pub_id}")
        wr(f" - `paper link <{url}>`_")
        wr(f" - `pdf file <{LIT_PATH + '/' + info['filename'] + '.pdf'}>`_")
        wr(_N)
        file.close()
