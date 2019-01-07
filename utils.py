
scrub_arx_id = lambda u: u.strip('htps:/warxiv.orgbdf').split('v')[0]

def is_arxiv_id(stripped_id):
    """ arx IDs always have 4 leading digits """
    pre = stripped_id.split('.')[0]
    return len(pre) == 4


