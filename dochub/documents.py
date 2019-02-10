import os
import code
from collections import OrderedDict
from pybtex.database import BibliographyData, Entry
import yaml
from utils import PATH_NOTES, PATH_LIT, LIT_BIBTEX, LIT_BIBYML

#=============================================================================#
#                                                                             #
#                  I8,        8        ,8I  88  88888888ba                    #
#                  `8b       d8b       d8'  88  88      "8b                   #
#                   "8,     ,8"8,     ,8"   88  88      ,8P                   #
#                    Y8     8P Y8     8P    88  88aaaaaa8P'                   #
#                    `8b   d8' `8b   d8'    88  88""""""'                     #
#                     `8a a8'   `8a a8'     88  88                            #
#                      `8a8'     `8a8'      88  88                            #
#                       `8'       `8'       88  88                            #
#                                                                             #
#=============================================================================#
"""
Overhauled query, made it simpler and independent
now need to make functions for bibtex, that is actually valid bibtex

"""

#-----------------------------------------------------------------------------#
#                                Bibliography                                 #
#-----------------------------------------------------------------------------#
def make_bib_entry(info, style='bibtex'):
    """ Makes a bibliography entry from the processed api info

    Uses pybtex to output a valid bibliography entry.
    style='bibtex' --> "standard" bibtex format
    style='yaml'   --> yaml format (easily convertible to bibtex)

    """
    # create instances
    bib_entry = BibliographyData()
    entry = Entry('article')
    fields = type(entry.fields)() # pybtex.utils.OrderedCaseInsensitiveDict

    # helper
    def add_field(k):
        if k in info:
            v = info[k]
            if isinstance(v, list):
                v = ', '.join(v)
            fields[k] = str(v)

    #==== add fields
    add_field('year')
    add_field('title')
    add_field('author')
    add_field('arxivId')
    add_field('DOI')
    add_field('keywords')
    add_field('abstract')
    add_field('URL')
    add_field('pdf')
    add_field('filename')

    #==== update instances
    entry.fields = fields
    bib_entry.add_entry(info.identifier, entry)
    #return bib_entry.to_string('bibtex')
    return bib_entry.to_string(style)

#-----------------------------------------------------------------------------#
#                                    Notes                                    #
#-----------------------------------------------------------------------------#


# Static
# ======
_N   = '\n'
_TAB = '\n    ' # spaces rule, tabs drool
_META = ".. meta::"
_KEYWORDS = "    :keywords:"
_ARX_SUB = ":arXiv_link: |arXivID|_"
_LOCAL_SUB = ":local_pdf: paper_"
#_OTHER_LINK = ":paper_link: |paper_title|_"

# Interpreted
# ===========
ONELINER = "\n.. rubric:: **一言でいうと:**"
ABS      = "\n.. admonition:: Abstract\n\n    {}\n"

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
    tab = '\n    '
    def __init__(self, info, path=PATH_NOTES):
        self.info = info
        self.filename = f"{path}/{info['filename']}.rst"

    def format_keywords(self):
        kw = ''
        if 'keywords' in self.info:
            kw = ', '.join([w.lower() for w in self.info['keywords']])
        return kw

    def format_abs(self):
        abstract = '(Unavailable)'
        if 'abstract' in self.info:
            abstract = _TAB.join(self.info['abstract'].split('\n'))
        return abstract

    def generate_notes(self):
        assert not os.path.exists(self.filename) # don't overwrite notes
        # get content of interest
        info = self.info
        title   = info['title']
        authors = ", ".join(info['author'])
        year    = info['year']
        url     = '\n    '.join(info['URL'])
        keywords = self.format_keywords()
        abstract = self.format_abs()
        eprint   = info['arxivId'] if 'arxivId' in info else info['DOI']

        # write file
        line = Line()
        file = open(self.filename, 'w')
        wr = lambda s: file.write(s + '\n')
        #==== Header: keywords, title, authors
        wr(_META)
        wr(f"{_KEYWORDS} {keywords}")
        wr(_N)
        wr(line(title, 0))
        wr("\n| **Authors:**")
        wr(f"| {authors}")
        wr(_N)
        #==== Body: <oneliner>, abstract, <notes area>, year, eprint, url
        wr(ONELINER + '\n')
        wr(ABS.format(abstract))
        wr(line('Key Points', 2))
        wr(_N)
        wr(line('Additional Notes', 3))
        wr(_N)
        wr(line('Reference', 2))
        wr(f":year: {year}")
        wr(f":eprint: {eprint}")
        wr(f":link: {url}")
        wr(_N)
        file.close()
