#!/usr/bin/env python
"""DocHub is a personal documents manager for scholarly literature.
It's primary purpose is the acquisition and organization of papers given
an ereference (arXiv ID or doi).

DocHub uses the ArXiv and Semantic Scholar APIs to get citation information
and download papers, and generates notes for a paper using a custom
reStructuredText template.
"""
import os, sys, code
import argparse

from query import Query
import documents
import downloader
from utils import PATH_PAPERS, PATH_NOTES, LIT_INBOX, LIT_BIBYML

# Parser
# ------
parser = argparse.ArgumentParser(description=__doc__)
adg = parser.add_argument
adg('ref_id', nargs='?', default=None,
    help=('ArXiv ID or DOI for a paper\n'
          'if no ref_id is given, dochub will attempt to read from the inbox file'))

adg('-i', '--inbox', action='store_true',
    help='add the ref id to the inbox file')

nih_path = '/home/evan/Projects/DocHub/Literature/nih_papers'


#adg('-d', '--download', nargs='?', default=None, const=nih_path, metavar='DPATH',
adg('-d', '--download', nargs='?', default=None, const=PATH_PAPERS, metavar='DPATH',
    help='download paper to default literature dir, or to dir at DPATH')

adg('-n', '--notes', nargs='?', default=None, const=PATH_NOTES, metavar='NPATH',
    help='generate notes file in default notes dir, or to dir at NPATH')

#adg('--no-bib', action='store_true', help='do not write to bibliography')


# Feature functions
# -----------------
file_exists = lambda fpath: os.path.exists(fpath)

def add_to_inbox(ref_id, inbox_file=LIT_INBOX):
    flag = 'a' if file_exists(inbox_file) else 'w'
    with open(inbox_file, flag) as ibx:
        ibx.write(ref_id + '\n')
    print(f"inboxed {ref_id}")

def get_info(ref_id):
    api_query = Query(ref_id)
    info = api_query.query()
    return info

def get_paper(info, write_path, overwrite=True):
    #==== file path
    paper_filename = info['filename'] + '.pdf'
    paper_path     = f"{write_path}/{paper_filename}"
    if file_exists(paper_path):
        print(f"  {paper_filename} already exists!\n"
               "  proceeding to overwrite")
    #==== download
    if 'arxivId' in info:
        ref_id = info['arxivId']
    else:
        if 'doi' not in info:
            raise ValueError('No valid reference ID available for download')
        ref_id = info['doi']
    downloader.download(ref_id, paper_path)

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
    bib = documents.BibtexEntry(info)
    print(bib.bibtex)
    bib.copy_to_clip()
    #if write_to_bib:
    #    bib.write_to_bibliography()
    return bib



if __name__ == '__main__':
    args = parser.parse_args()
    if args.ref_id is None:
        print('TODO: processing multiple ids from file not yet supported')
        #ref_id = utils.read_inbox_file()
    else:
        ref_id = args.ref_id

    # Inbox only?
    if args.inbox:
        add_to_inbox(ref_id)
        #sys.exit()

    # Query
    info = get_info(ref_id)

    # Citation
    citation = get_citation(info, write_to_bib=True)

    # Download
    if args.download is not None:
        dpath = args.download
        if dpath != PATH_PAPERS:
            dpath = os.path.abspath(dpath)
        print(info['doi'])
        get_paper(info, dpath)

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
