import logging
import urllib
import futures
import functools
import config
from GoogleReader import  CONST
from GoogleReader.reader import GoogleReader

def verify_num_tags():
    pass
    # TODO

def set_up():
    gr = GoogleReader()
    gr.identify(config.username, config.password)
    gr.login()
    return gr

def format_url(url):
    """Google stores the url without duplicate // in the body and without trailing /'s. Also, www. is optional.
    We remove www. for simplicity.
    """
    if url[7:11] == 'www.':
        url = url[11:]
    else:
        url = url[7:]
    url = url.rstrip('/')
    return 'http://' + url.replace('//', '/')

def do_line(gr, line, line_num):
    split = line.rstrip().split(',')
    # remove www. and right / from home page for consistency and percent quote homepage
    # TODO add support for https and urls that don't include http
    if split[0][7:11] == 'www.':
        home_page = split[0][:7] + split[0][11:]
    else:
        home_page = split[0]
    home_page = urllib.quote_plus(home_page.rstrip('/'))
    if split[3] == 'N/A':
        country = 'none'
    else:
        country = split[3]
    url = format_url(split[1])
    logging.info("%s %s" % (str(line_num), line.rstrip()))
    return gr.add_subscription(url=url, labels=['home_page:' + home_page.encode('utf-8'), 'type:' + split[2],
                                                'country:' + country])

def log_feed(line_num, job):
    if job.exception():
        logging.error('%d %r' % (line_num, job.exception()))
    else:
        logging.info('%d %s\n' % (line_num, job.result()))

def main():
    gr = set_up()
    logging.info('User set up.')
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for line_num, line in enumerate(open('longfeeds.txt')):
            job = executor.submit(do_line, gr, line, line_num)
            job.add_done_callback(functools.partial(log_feed, line_num))

if __name__ == '__main__':
    import argparse
    import datetime

    log_file = 'logs/' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '.log'
    logging.basicConfig(filename=log_file, filemode='w', level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logging.info('Program Started')

    parser = argparse.ArgumentParser(description='Interface with Google Reader.')
    parser.add_argument('--clean', action='store_true', default=False, help='erases all entries and tags from Google Reader.')
    args = parser.parse_args()
    if args.clean:
        gr = set_up()
        logging.info('Google Reader Cleaned.')
        gr.del_all_subscriptions()
        gr.disable_all_tags()
    else:
        main()
    logging.info('Program Terminated')
