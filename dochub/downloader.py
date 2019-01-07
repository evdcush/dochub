"""
ACKNOWLEDGEMENT:
    Code for downloading from libgen by doi was
    adapted from bibcure's scihub2pdf module:
        https://github.com/bibcure/scihub2pdf
    and is licensed under the GNU AGPL-3.0

Downloading
-----------
Primary paper source is arXiv, and arXiv ids are always preferred over doi.
Papers that are not published to arXiv are identified instead by their doi.
Generally, doi papers are behind a journal paywall, so libgen is used.

"""

import sys
import code
import requests
from lxml import html
from lxml.etree import ParserError
from urllib.request import urlretrieve

from utils import scrub_arx_id
from conf import ARX_PDF_URL

#-----------------------------------------------------------------------------#
#                                     doi                                     #
#-----------------------------------------------------------------------------#
class LibGen:
    def __init__(self,
                 headers={},
                 libgen_url="http://libgen.io/scimag/ads.php",
                 xpath_pdf_url="/html/body/table/tr/td[3]/a"):
        self.headers       = headers
        self.libgen_url    = libgen_url
        self.xpath_pdf_url = xpath_pdf_url
        self.doi = None
        self.pdf_file = None
        self.pdf_url  = None
        self.page_url = None
        self.html_tree    = None
        self.html_content = None
        self.req_sess = requests.Session()

    def navigate_to(self, doi, pdf_file):
        params = dict(doi=doi, downloadname='')
        response = self.req_sess.get(
            self.libgen_url,
            params=params,
            headers=self.headers
        )
        self.page_url = response.url
        self.pdf_file = pdf_file
        print(f"\n\tDOI: {doi}")
        print(f"\tLibGen Link: {self.page_url}")
        status = response.status_code
        found = status == 200
        if not found:
            raise Exception(f'ERROR: libgen response status {status}')
        self.html_content = response.content

    def generate_tree(self):
        try:
            self.html_tree = html.fromstring(self.html_content)
            success = True
        except ParserError:
            print("\tUnable to parse libgen html")
            print(self.page_url)
            sys.exit()

    def get_pdf_url(self):
        html_a = self.html_tree.xpath(self.xpath_pdf_url)
        if len(html_a) == 0:
            raise Exception(f"\tPDF link for {self.page_url} not found")
        else:
            url = html_a[0].attrib["href"]
            if url.startswith("//"):
                url = "http:" + url
            self.pdf_url = url

    def download(self, doi, fname):
        self.navigate_to(doi, fname)
        self.generate_tree()
        self.get_pdf_url()
        urlretrieve(self.pdf_url, self.pdf_file)


def doi_download(doi, fname=None):
    libgen = LibGen()
    if fname is None:
        fname = f"{doi.replace('/', '_')}.pdf"
    libgen.download(doi, fname)



#-----------------------------------------------------------------------------#
#                                    arXiv                                    #
#-----------------------------------------------------------------------------#

def arx_download(url, fname=None):
    # likely redundant strip,
    # but weakens preconditions on url to allow arx ids
    arx_id = scrub_arx_id(url)
    if fname is None:
        fname = arx_id + '.pdf'
    url = ARX_PDF_URL + arx_id
    urlretrieve(url, fname)
    print(f'  Downloaded {fname}')


#-----------------------------------------------------------------------------#
#                                    Main                                     #
#-----------------------------------------------------------------------------#
sample_arx = '1706.03762'
sample_doi = '10.1038/nature16961'
sample_doi_whale = '10.1016/j.advengsoft.2016.01.008'

def download(pub_id):
    sid = scrub_arx_id(pub_id)
    if len(sid.split('.')[0]) == 4:
        # arx ids always begin YYMM
        arx_download(sid)
    else:
        doi_download(pub_id)

if __name__ == '__main__':
    pub_id = sys.argv[1]
    download(pub_id)


