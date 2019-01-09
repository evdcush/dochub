import os
import code
from collections import OrderedDict
from utils import is_arxiv_id, scrub_arx_id, NOTES_PATH, LIT_PATH, LIT_BIB



#-----------------------------------------------------------------------------#
#                                Bibliography                                 #
#-----------------------------------------------------------------------------#
class BibtexEntry:
    """ currently only supporting articles """
    endline = '},\n'
    elem_per_line = 5
    def __init__(self, info):
        self.margin = len(max(info, key=len)) - 1
        self.cont_margin = '\n'.ljust(self.margin + 4) # for clean align with prev line char
        self.info = OrderedDict(**info) # make copy
        self.create()

    def format_abstract(self):
        if 'abstract' in self.info:
            abstract = self.info['abstract'].split('\n')
            self.info['abstract'] = self.cont_margin.join(abstract)

    def format_collection(self, key):
        val = self.info[key]
        last = len(val) - 1
        new_val = ''
        for i, elem in enumerate(val):
            if (i+1) % self.elem_per_line == 0:
                new_val += self.cont_margin
            new_val += elem
            if i != last:
                new_val += ', '
        self.info[key] = new_val

    def create(self):
        # create full bibtex citation
        bibtex = "@Article{" + self.info['identifier'] + '\n'
        self.format_abstract()
        for k, val in self.info.items():
            if k == 'identifier': continue
            if not isinstance(val, str):
                self.format_collection(k)
                val = self.info[k]
            key = k.ljust(self.margin) + '= {'
            bibtex += key + val + self.endline
        self.bibtex = bibtex + '}\n'

    def copy_to_clip(self):
        import pyperclip
        pyperclip.copy(self.bibtex)


    # may want to make this static, so can add clipped citations ez
    def write_to_bibliography(self, file=LIT_BIB):
        # create in init so impossible have instance without 'bibtex'
        #assert hasattr(self, 'bibtex')
        with open(file, 'a') as bib:
            bib.write(self.bibtex)


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
    def __init__(self, info, path=NOTES_PATH):
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
        url     = info['url']
        keywords = self.format_keywords()
        abstract = self.format_abs()
        eprint   = info['arxivId'] if 'arxivId' in info else info['doi']

        # write file
        line = Line()
        file = open(self.filename, 'w')
        wr = lambda s: file.write(s + '\n')
        #==== Header: keywords, title, authors
        wr(_META)
        wr(f"{_KEYWORDS} {keywords}")
        wr(_N)
        wr(line(title, 0))
        wr("\n| **Author:**")
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
