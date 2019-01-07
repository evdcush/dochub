import code
from utils import is_arxiv_id, scrub_arx_id
from collections import OrderedDict

#-----------------------------------------------------------------------------#
#                                Bibliography                                 #
#-----------------------------------------------------------------------------#
LEFT_MARGIN = 9
ENDLINE = '\",\n'
MARGIN_JUST = "\n".ljust(len('"abstract = "'))

def format_list(lst):
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
    info['author']    = format_list(info['author'])
    return info


def format_doi_info(info_in):
    doi_key_order = ['identifier', 'year', 'author', 'title', 'doi',
                     'arxivId', 'url', 'urlPDF', 'keywords', 'abstract']
    info = OrderedDict()
    for k in doi_key_order:
        if k in info_in:
            info[k] = info_in[k]

    info['author']   = format_list(info['author'])
    info['keywords'] = format_list(info['keywords'])
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
SHORT = "\n.. rubric:: **一言でいうと:** {}"
ABS = "\n.. admonition:: Abstract\n    {}\n"

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
    T  = '--------' # transition marker

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
        return f"\n{self.T}\n"

    def __call__(self, text, level=2):
        return self.section(text, level)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# WIP
class Document:
    def __init__(self, doc_content):
        self.doc_filename = 'foo.rst'
        self.doc = doc_content
        self.doc_text = []

    def add_content(self, thing):
        self.doc_text.append(thing)

    def write_file(self):
        with open(self.doc_filename, 'x') as stream:
            for txt in self.doc_text:
                stream.write(txt)

# ORIGINAL NOTES GEN FUNC
'''
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
    wr(f"{authors_line}\n{author_print}\n{authors_line}\n")
    wr(f':arxiv_link: |arXivID|_')
    wr(f':local_pdf: paper_\n')
    wr('.. rubric:: **一言でいうと:**')
    wr('.. admonition:: Abstract')
    wr(f'\n    {abstract}\n')
    wr('\nSummary\n=======')
    wr('- lorem ipsum dolor sit amet')
    wr('- Maecenas turpis leo, gravida')
    wr('')
    wr('\nMethod\n------')
    wr('- poseure mattis lectus')
    wr('- curabitur ut mauris nec')
    wr('')
    wr('\nNotes\n-----')
    wr('Etiam accumsan sapien nec ex porta semper. Nulla sed augue sagittis, laoreet odio imperdiet')
    wr('\n\n')
    wr('\nSee Also\n^^^^^^^^')
    wr('this paper like this or github code')
    wr('\n')
    wr('\nReferences\n-----------')
    wr('\n.. Substitutions\n')
    wr(f'.. |arXivID| replace:: {arx_id}')
    wr(f'.. _arXivID: {original_link}')
    wr(f'.. _paper: {paper_link_local}')
    notes.close()
'''

