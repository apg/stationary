import json
import logging
import os
import subprocess

from ConfigParser import SafeConfigParser as ConfigParser
from ConfigParser import NoOptionError
from optparse import OptionParser

from jinja2 import Environment, FileSystemLoader

from utils import reroot

pathjoin = os.path.join
abspath = os.path.abspath

DEFAULT_PROPERTIES = {
    'base_context_filename': '_global.json',
    'build_directory': abspath('build/'),
    'data_directory': abspath('data/'),
    'layout_directory': abspath('layout/'),
    'layout': 'default',
    'src_directory': abspath('src/'),
    'template_language': 'jinja2',
}

make_absolute = lambda x: abspath(str(x))

# should probably make these do some validation!
PROPERTY_CONVERTERS = {
    'base_context_filename': str,
    'build_directory': make_absolute,
    'data_directory': make_absolute,
    'layout_directory': make_absolute,
    'layout': str,
    'src_directory': make_absolute,
    'template_language': str,
}

parser = OptionParser()
parser.add_option('-c', '--config', default=None, dest='config',
                  help="path to config file")
parser.add_option('-d', '--debug', action='store_true', dest='debug',
                  help="turn on debug output")


# TODO: should make this inherit from dict
class Config(object):

    def __init__(self, properties=None):
        self._properties = properties or DEFAULT_PROPERTIES.copy()
        self._template_env = None

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError, e:
            if attr in self._properties:
                return self._properties[attr]
            raise e

    def base_context(self):
        base_file = pathjoin(self.data_directory,
                             self.base_context_filename)
        return load_context_file(base_file)
        # if os.path.exists(base_file):
        #     if os.access(base_file, os.R_OK):
        #         with open(base_file) as o:
        #             return json.load(o)
        #     else:
        #         logging.warning("base context '%s' exists, "
        #                         "but is not readable.", base_file)
        # return {}

    @property
    def template_env(self):
        if not self._template_env:
            loader = FileSystemLoader([pathjoin(self.layout_directory,
                                                self.layout),
                                       self.src_directory])
            self._template_env = Environment(loader=loader)
        return self._template_env

    def read_context(self, src_file):
        """Read the context for source file `src_file`

        reads the fname as JSON from the data directory if it exists,
        otherwise, {}
        """
        src_file = abspath(src_file)
        try:
            data_file = reroot(src_file, 
                               srcdir=self.src_directory,
                               destdir=self.data_directory)
            return load_context_file(data_file)
        except ValueError, e:
            logging.warning(str(e))
        except Exception, e:
            logging.error(str(e))
        return {}


def load_context_file(path):
    return find_and_read_context(path) or {}


def find_and_read_context(path):
    """Read a context file as a string, potentially with preprocessing
    """
    preprocessors = [
        (None, None),
        ('coffee %s', '.coffee'),
        ('iced %s', '.iced')
        ]
    for cmd, suffix in preprocessors:
        data_file = (path + suffix) if suffix else path
        if os.path.exists(data_file):
            if os.access(data_file, os.R_OK):
                if cmd:
                    output = subprocess.check_output(["coffee", data_file])
                    return json.loads(output)
                else:
                    with open(data_file) as o:
                        return json.load(o)
            else:
                logging.warning("data context '%s' exists, "
                                "but is not readable." % data_file)
                return None
    logging.debug("data context does '%s' does not exist." % data_file)


def read_config(fname=None):
    properties = DEFAULT_PROPERTIES.copy()
    cp = ConfigParser()
    absname = find_config(fname)
    if absname:
        cp.read(absname)
    else:
        logging.warning("Config file (%s) not found\n" % fname)
        return Config(properties=properties)

    for section in cp.sections():
        options = cp.options(section)
        if section == 'stationary':
            for o in options:
                t = PROPERTY_CONVERTERS.get(o)
                if t:
                    properties[o] = t(cp.get(section, o))
                else:
                    logging.warn("don't know about option %s "
                                 "in stationary section of config" % o)

    return Config(properties=properties)


def find_config(fname):
    cands = ['stationary', 'Stationary']
    if fname:
        cands.append(fname)

    for c in reversed(cands):
        a = os.path.abspath(c)
        if os.path.exists(a):
            return a

    return None

