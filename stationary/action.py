import datetime
import json
import logging
import mimetypes
import os
import os.path as osp
import re
import urlparse
import time
import traceback
import sys
import BaseHTTPServer

from functools import wraps
from xml.sax.saxutils import escape as xmlescape
from xml.sax.saxutils import quoteattr as xmlquoteattr

from jinja2 import Environment, FileSystemLoader

from utils import reroot
from build import build_file, build_data


TASKS = {}
BIND_HOST = 'localhost'
BIND_PORT = 1432

mimetypes.add_type('.coffee', 'text/x-coffeescript')
mimetypes.add_type('.iced', 'text/x-iced-coffeescript')
mimetypes.add_type('.less', 'text/css')


def task(priority=100):
    """Registers task
    """
    def decorator(func):
        TASKS[func.__name__] = {
            'help': func.__doc__,
            'name': func.__name__,
            'priority': priority,
            'command': func
            }

        return func
    return decorator


def mimeof(path):
    t, _ = mimetypes.guess_type(path)
    if t:
        return t
    return 'application/octet-stream'


def make_handler(config):
    class BuildHandler(BaseHTTPServer.BaseHTTPRequestHandler):

        def do_HEAD(s):
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
    
        def do_GET(self):
            """Build/cache and serve a page"""
            src_dir = osp.abspath(config.src_directory)
            build_dir = osp.abspath(config.build_directory)

            try:
                if self.path == '/':
                    self.path = '/index.html'

                base_ctx = config.base_context() or {}
                src_file = osp.join(src_dir, self.path[1:])

                dest_file = reroot(src_file,
                                   srcdir=src_dir,
                                   destdir=build_dir)

                # don't even check if file exists, raise an error if it doesn't
                try:
                    dest_file = build_file(config, src_file, dest_file)
                    self.send_response(200)
                    self.send_header('Content-Type', mimeof(dest_file))
                    self.end_headers()

                    with open(dest_file) as f:
                        self.wfile.write(f.read())
                except IOError:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/plain')
                    self.wfile.write("404 Not found")
            except:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                traceback.print_exc(file=self.wfile)

    return BuildHandler

@task(priority=1)
def build(config):
    """Rebuilds the site.
    """
    sanity_check(config)

    src_dir = osp.abspath(config.src_directory)
    build_dir = osp.abspath(config.build_directory)
    build_data_dir = osp.abspath(config.build_data_directory)

    for root, dirs, files in os.walk(config.src_directory):
        for f in files:
            root = osp.abspath(root)
            src_file = osp.join(root, f)
            dest_file = reroot(src_file,
                               srcdir=src_dir,
                               destdir=build_dir)
            build_file(config, src_file, dest_file)

            if f.endswith('.html'):
                dest_data_file = reroot(src_file,
                                        srcdir=src_dir,
                                        destdir=build_data_dir)
                build_data(config, src_file, dest_data_file)

    # build global data
    global_file = osp.join(config.data_directory, config.base_context_filename)
    global_dest = reroot(global_file, 
                         srcdir=config.data_directory,
                         destdir=build_data_dir)
    build_data(config, global_file, global_dest)


@task(priority=1)
def develop(config):
    """Starts a webserver that rerenders and serves dynamically
    generated pages
    """
    httpd = BaseHTTPServer.HTTPServer((BIND_HOST, BIND_PORT),
                                      make_handler(config))
    logging.info("Listening on http://%s:%d" % (BIND_HOST, BIND_PORT))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info("Stopped listening on http://localhost:1432")


@task(priority=1)
def clean(config):
    """Deletes the contents of the build directory.
    """
    rmdirs = []
    if not check_dir(config.build_directory, access=[os.W_OK, os.R_OK]):
        raise SystemExit()

    logging.info("Cleaning up %s" % osp.abspath(config.build_directory) + '/')
    for root, dirs, files in os.walk(osp.abspath(config.build_directory) + '/'):
        for f in files:
            fp = osp.join(root, f)
            logging.debug("Removing file %s" % fp)
            os.unlink(fp)
        rmdirs.extend(osp.join(root, d) for d in dirs)

    for d in rmdirs:
        logging.debug("Removing directory %s" % d)
        os.rmdir(d)


@task(priority=0)
def sanity_check(config):
    if not check_dir(config.build_directory, access=[os.W_OK], make=True):
        logging.fatal("build directory (%s) is not writable! Aborting." % \
                      config.build_directory)
        raise SystemExit()

    if not check_dir(config.build_data_directory, access=[os.W_OK], make=True):
        logging.fatal("build data directory (%s) is not writable! Aborting." % \
                      config.build_data_directory)
        raise SystemExit()
    
    if not check_dir(config.src_directory, access=[os.R_OK]):
        logging.fatal("source directory (%s) is not readable or doesn't "
                      "exist! Aborting" %  config.src_directory)
        raise SystemExit()
        
    if not check_dir(config.data_directory, access=[os.R_OK]):
        logging.warning("data directory (%s) is not readable or doesn't "
                        "exist! This might make things funky" % \
                        config.data_directory)


@task(priority=-1)
def help(config, *args):
    """Prints a helpful help message.
    """
    if len(args) == 1:
        task = TASKS.get(args[0])
        if task:
            print task['name']
            print '---'
            print task['help']
        else:
            logging.error("Can't get help on %s, it doesn't exist!" % \
                              args[0])
    else:
        print 'Available tasks'
        print '---'
        for name in sorted(TASKS.keys()):
            print ' ', name
        print


def check_dir(dir, exists=True, access=None, make=False):
    if exists and not osp.exists(dir):
        if make:
            os.makedirs(dir)
        return osp.exists(dir)

    if access and not all([os.access(dir, a) for a in access]):
        return False

    return True



