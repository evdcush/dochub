import os
import sys
import pyperclip
import query
import documents
import downloader
from utils import LIT_PATH

file_exists = lambda fpath: os.path.exists(fpath)


def get_paper(pub_id, download=True):
    #=== query
    info = query.query(pub_id)

    #=== bib
    bib = documents.make_bib(info)
    print(bib)
    pyperclip.copy(bib)

    #=== download
    paper_filename = f"{LIT_PATH}/{info['filename']}.pdf"
    if download and not file_exists(paper_filename):
        downloader.download(pub_id, paper_filename)

    #=== notes
    notes = documents.Document(info)
    if not file_exists(notes.filename):
        notes.generate_notes()

if __name__ == '__main__':
    pub_id = sys.argv[1]
    get_paper(pub_id)
