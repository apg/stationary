import datetime
import json
import logging
import os
import re
import urlparse

from functools import wraps
from xml.sax.saxutils import escape as xmlescape
from xml.sax.saxutils import quoteattr as xmlquoteattr

from jinja2 import Environment, FileSystemLoader

from utils import reroot

abspath = os.path.abspath
pathjoin = os.path.join

TASKS = {}

def task(priority=100):
    """Registers task
    """
    global TASKS
    def decorator(func):
        @wraps(func)
        def _inner(*args, **kwargs):
            return func(*args, **kwargs)

        TASKS[func.__name__] = {
            'help': func.__doc__,
            'name': func.__name__,
            'priority': priority,
            'command': func
            }

        return _inner
    return decorator

@task(priority=2)
def build(config):
    """Rebuilds the site.
    """
    sanity_check(config)

    fsloader = FileSystemLoader([pathjoin(config.layout_directory, 
                                          config.layout),
                                 config.src_directory])

    tmplenv = Environment(loader=fsloader)

    # get a global context if exists
    global_ctx = config.base_context() or {}

    src_dir = os.path.abspath(config.src_directory)
    build_dir = os.path.abspath(config.build_directory)
    data_dir = os.path.abspath(config.data_directory)

    for root, dirs, files in os.walk(config.src_directory):
        for f in files:
            if not f.endswith('.html'):
                continue
            root = abspath(root)
            src_file = os.path.join(root, f)
            base_ctx = global_ctx.copy()
            data_ctx = config.read_context(src_file.replace('.html', 
                                                            '.json'))
            base_ctx.update(data_ctx)
    
            dest_file = reroot(pathjoin(root, f),
                               srcdir=src_dir,
                               destdir=build_dir)
            
            dest_dir = os.path.dirname(dest_file)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            logging.info("Rendering file: %s to %s" % (src_file, dest_file))
            render(env=tmplenv, 
                   src=src_file[len(src_dir):],
                   dest=dest_file,
                   context=base_ctx)
                   

@task(priority=1)
def clean(config):
    """Deletes the contents of the build directory.
    """
    if not check_dir(config.build_directory, access=[os.W_OK, os.R_OK]):
        raise SystemExit()
    
    logging.debug("Cleaning up %s" % config.build_directory)
    for root, dirs, files in os.walk(config.build_directory):
        for f in files:
            fp = os.path.join(root, f)
            logging.debug("Removing file %s" % fp)
            os.unlink(fp)
        dirs.extend(os.path.join(root, d) for d in dirs)

    for d in dirs:
        logging.debug("Removing directory %s" % config.d)
        os.rmdir(d)

@task(priority=0)
def sanity_check(config):
    if not check_dir(config.build_directory, access=[os.W_OK], make=True):
        logging.fatal("build directory (%s) is not writable! Aborting." % \
                      config.build_directory)
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
    if exists and not os.path.exists(dir):
        if make:
            os.mkdir(dir, 0750)
        return os.path.exists(dir)

    if access and not all([os.access(dir, a) for a in access]):
        return False

    return True

def render(env=None, src=None, dest=None, context=None):
    tmpl = env.get_template(src)
    with open(dest, 'w') as f:
        f.write(tmpl.render(**context))

