"""DocHub is a personal documents manager for scholarly literature.
It's primary purpose is the acquisition and organization of papers given
an ereference (arXiv ID or doi).

DocHub uses the ArXiv and Semantic Scholar APIs to get citation information
and download papers, and generates notes for a paper using a custom
reStructuredText template.
"""
import os
import sys
import code
import argparse
import pyperclip
from query import Query
import documents
import downloader
from utils import PATH_LIT, PATH_NOTES, LIT_INBOX, LIT_BIBYML

# Parser
# ------
parser = argparse.ArgumentParser(description=__doc__)
adg = parser.add_argument
adg('ref_id', nargs='?', default=None,
    help=('ArXiv ID or DOI for a paper\n'
          'if no ref_id is given, dochub will attempt to read from the inbox file'))

adg('-d', '--download', nargs='?', default=None, const=PATH_LIT, metavar='DPATH',
    help='download paper to default literature dir, or to dir at DPATH')

adg('-n', '--notes', nargs='?', default=None, const=PATH_NOTES, metavar='NPATH',
    help='generate notes file in default notes dir, or to dir at NPATH')

adg('-b', '--bib_no_save', action='store_true',
    help='do not write to bibliography')

file_exists = lambda fpath: os.path.exists(fpath)

def get_info(ref_id):
    api_query = Query(ref_id)
    info = api_query.query()
    return info

def get_paper(info, write_path, overwrite=True):
    #if download_path is None: return
    #==== file path
    paper_filename = info['filename'] + '.pdf'
    paper_path     = f"{write_path}/{paper_filename}"
    if file_exists(paper_path):
        print(f"  {paper_filename} already exists!\n"
               "  proceeding to overwrite")
    #==== download
    ref_id = info.get('arxivId', info['doi'])
    downloader.download(ref_id, paper_path)

def gen_notes(info, write_path):
    #if write_path is None: return
    notes_filename = info['filename'] + '.rst'
    notes_path = f"{write_path}/{notes_filename}"
    #==== file path
    if not file_exists(notes_path):
        notes = documents.Document(info)
        notes.generate_notes()
    else:
        print('Notes already exist!')

def get_citation(info):
    bib = documents.BibtexEntry(info)
    print(bib.bibtex)
    bib.copy_to_clip()
    return bib



if __name__ == '__main__':
    args = parser.parse_args()
    if args.ref_id is None:
        print('TODO: processing multiple ids from file not yet supported')
        #ref_id = utils.read_inbox_file()
    else:
        ref_id = args.ref_id

    # Query
    info = get_info(ref_id)
    #code.interact(local=dict(globals(), **locals()))

    # Citation
    citation = get_citation(info)

    # Download
    if args.download is not None:
        dpath = args.download
        if dpath != PATH_LIT:
            dpath = os.path.abspath(dpath)
        get_paper(info, dpath)
    code.interact(local=dict(globals(), **locals()))
    # Notes
    if args.notes is not None:
        npath = args.notes
        if npath != PATH_NOTES:
            npath = os.path.abspath(npath)
        gen_notes(info, npath)



#=============================================================================#
#                                                                             #
#        888888888888    ,ad8888ba,    88888888ba,      ,ad8888ba,            #
#             88        d8"'    `"8b   88      `"8b    d8"'    `"8b           #
#             88       d8'        `8b  88        `8b  d8'        `8b          #
#             88       88          88  88         88  88          88          #
#             88       88          88  88         88  88          88          #
#             88       Y8,        ,8P  88         8P  Y8,        ,8P          #
#             88        Y8a.    .a8P   88      .a8P    Y8a.    .a8P           #
#             88         `"Y8888Y"'    88888888Y"'      `"Y8888Y"'            #
#                                                                             #
"""===========================================================================#

# TODOS
# -----
- All files must use same set of info keys. Currently, it looks like documents
  may be using it's own set of info keys

UPDATE STATUS
X query
X dochub interface
/ downloader
O notes
O bibtex
O utils


#==========================================================================="""
