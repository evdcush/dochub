import os
import code
from collections import OrderedDict
import yaml
from utils import PATH_NOTES, PATH_LIT, LIT_BIBTEX, LIT_BIBYML



#-----------------------------------------------------------------------------#
#                                Bibliography                                 #
#-----------------------------------------------------------------------------#
class BibtexEntry:
    """ currently only supporting articles """
    endline = '},\n'
    elem_per_line = 5
    def __init__(self, info):
         # for clean align with prev line char
        self.margin = len(max(info, key=len)) - 1
        self.cont_margin = '\n'.ljust(self.margin + 4)
        self.raw_info = info # for yaml bib
        self.info = OrderedDict(**info) # make copy
        self.create()

    def format_abstract(self):
        if 'abstract' in self.info:
            abstract = self.info['abstract'].split('\n')
            self.info['abstract'] = self.cont_margin.join(abstract)

    def format_collection(self, key):
        if key == 'url':
            joiner = f",{self.cont_margin}"
            self.info[key] = joiner.join(self.info[key])
            return
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

    def create_alt(self):
        # create full bibtex citation
        bibtex = "@article{" + self.info['identifier'] + '\n'
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

    def write_yaml_bib(self):
        """ WORRY ABOUT DUPS LATER """
        identifier = self.raw_info['identifier']
        title = self.raw_info['title']
        #code.interact(local=dict(globals(), **locals()))
        with open(LIT_BIBYML) as byml:
            bib = yaml.load(byml)
        # Check existing
        if identifier in bib:
            bib_entry = bib[identifier]
        else:
            bib_entry = dict()

        entry = {}
        for k, v in self.raw_info.items():
            if k == 'identifier': continue
            if k == 'abstract':
                entry[k] = v.replace('\n', ' ')
                continue
            entry[k] = v

        bib_entry[title] = entry

        with open(LIT_BIBYML, 'w') as byml:
            bib[identifier] = bib_entry
            yaml.dump(bib, byml, default_flow_style=False)


    def write_bibtex_bib(self):
        with open(LIT_BIBTEX, 'a') as btex:
            btex.write(self.bibtex + '\n')


    # may want to make this static, so can add clipped citations ez
    def write_to_bibliography(self, file=LIT_BIBTEX):
        # create in init so impossible have instance without 'bibtex'
        #assert hasattr(self, 'bibtex')
        self.write_yaml_bib()
        self.write_bibtex_bib()
        #with open(file, 'a') as bib: bib.write(self.bibtex)

#def W_yml(fname, obj):
#    with open(fname, 'w') as file:
#        yaml.dump(obj, file, default_flow_style=False)
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
        authors = ", ".join(info['authors'])
        year    = info['year']
        url     = '\n    '.join(info['url'])
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
