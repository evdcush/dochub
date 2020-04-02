#!/usr/bin/env python
"""DocHub is a personal documents manager for scholarly literature.
It's primary purpose is the acquisition and organization of papers given
an ereference (arXiv ID or doi).

DocHub uses the ArXiv, Semantic Scholar, and CrossRef APIs to get citation
information and download papers, and generates notes for a paper
using a custom reStructuredText template.
"""
import os
import sys
import argparse
import pyperclip

from query import query, get_citation_count
import documents
import downloader
from utils import PATH_PAPERS, PATH_NOTES, LIT_INBOX, LIT_BIBYML

# Parser
# ------
parser = argparse.ArgumentParser(description=__doc__)
adg = parser.add_argument
adg('ref_id', nargs='?', default=None,
    help=('ArXiv ID or DOI for a paper'))

adg('-i', '--inbox', action='store_true',
    help='add the ref id to the inbox file')

adg('-d', '--download', nargs='?', default=None, const=PATH_PAPERS, metavar='DPATH',
    help='download paper to default literature dir, or to dir at DPATH')

adg('-n', '--notes', nargs='?', default=None, const=PATH_NOTES, metavar='NPATH',
    help='generate notes file in default notes dir, or to dir at NPATH')

#adg('--no-bib', action='store_true', help='do not write to bibliography')

adg('-c', '--count-citations', action='store_true')


# Feature functions
# -----------------
file_exists = lambda fpath: os.path.exists(fpath)

def add_to_inbox(ref_id, inbox_file=LIT_INBOX):
    flag = 'a' if file_exists(inbox_file) else 'w'
    with open(inbox_file, flag) as ibx:
        ibx.write(ref_id + '\n')
    print(f"inboxed {ref_id}")

#def get_info(ref_id):
#    info = query(ref_id)
#    return info
get_info = lambda ref_id: query(ref_id)

def get_paper(info, write_path, overwrite=True):
    #==== file path
    paper_filename = info['filename'] + '.pdf'
    paper_path     = f"{write_path}/{paper_filename}"
    if file_exists(paper_path):
        print(f"  {paper_filename} already exists!\n"
               "  proceeding to overwrite")
    #==== download
    #if 'arxivId' in info:
    #    ref_id = info['arxivId']
    #else:
    #    if 'DOI' not in info:
    #        raise ValueError('No valid reference ID available for download')
    #    ref_id = info['DOI']
    #downloader.download(ref_id, paper_path)
    downloader.download_from_response(info, paper_path)

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

def get_link_from_clipboard():
    url = pyperclip.paste()
    return url


if __name__ == '__main__':
    parser = utils.PARSER
    parser.description = __doc__
    args = parser.parse_args()
    if args.ref_id is None:
        ref_id = get_link_from_clipboard()
        #sys.exit()
        #ref_id = utils.read_inbox_file()
    else:
        ref_id = args.ref_id

    # count citations
    if args.count_citations:
        get_citation_count(ref_id)
        sys.exit()

    # Inbox only?
    if args.inbox:
        add_to_inbox(ref_id)
        #sys.exit()

    # Query
    info = get_info(ref_id)

    # Citation
    citation = get_citation(info, )#write_to_bib=True)

    # Download
    if args.download is not None:
        dpath = args.download
        if dpath != PATH_PAPERS:
            dpath = os.path.abspath(dpath)
        get_paper(info, dpath)

    # Notes
    if args.notes is not None:
        npath = args.notes
        if npath != PATH_NOTES:
            npath = os.path.abspath(npath)
        gen_notes(info, npath)


