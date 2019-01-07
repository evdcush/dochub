import sys
import query
import documents
import downloader
from conf import LIT_PATH

def get_paper(pub_id):
    info = query.query(pub_id)
    downloader.download(pub_id, f"{LIT_PATH}/{info['filename']}.pdf")
    notes = documents.Document(info)
    notes.generate_notes()

if __name__ == '__main__':
    pub_id = sys.argv[1]
    get_paper(pub_id)
