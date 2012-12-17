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

    # get a global context if exists
    global_ctx = read_context(base_context)
    

    for root, dirs, files in os.walk(config.src_directory):
        for f in files:
            print "Rendering file: %s" % os.path.join(root, f)
            base_ctx = global_ctx.copy()

            

@task(priority=1)
def clean(config):
    """Deletes the contents of the build directory.
    """
    if not check_dir(config.build_directory, access=[os.W_OK, os.R_OK]):
        raise SystemExit()
    
    logging.debug("Cleaning up %s", config.build_directory)
    for root, dirs, files in os.walk(config.build_directory):
        for f in files:
            fp = os.path.join(root, f)
            logging.debug("Removing file %s", fp)
            os.unlink(fp)
        dirs.extend(os.path.join(root, d) for d in dirs)

    for d in dirs:
        logging.debug("Removing directory %s", config.d)
        os.rmdir(d)

@task(priority=0)
def sanity_check(config):
    if not check_dir(config.build_directory, access=[os.W_OK], make=True):
        logging.fatal("build directory (%s) is not writable! Aborting.", 
                      config.build_directory)
        raise SystemExit()
    
    if not check_dir(config.src_directory, access=[os.R_OK]):
        logging.fatal("source directory (%s) is not readable or doesn't "
                      "exist! Aborting", config.src_directory)
        raise SystemExit()
        
    if not check_dir(config.data_directory, access=[os.R_OK]):
        logging.warning("data directory (%s) is not readable or doesn't "
                        "exist! This might make things funky",
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
            logging.error("Can't get help on %s, it doesn't exist!", args[0])
    else:
        print 'Available tasks'
        print '---'
        for name in sorted(TASKS.keys()):
            print name
        print

def check_dir(dir, exists=True, access=None, make=False):
    if exists and not os.path.exists(dir):
        if make:
            os.mkdir(dir, 0750)
        return os.path.exists(dir)

    if access and not all([os.access(dir, a) for a in access]):
        return False

    return True

