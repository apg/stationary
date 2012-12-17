import logging
import os

from ConfigParser import SafeConfigParser as ConfigParser
from ConfigParser import NoOptionError
from optparse import OptionParser

DEFAULT_PROPERTIES = {
    'base_context': 'base.json',
    'build_directory': 'build/',
    'data_directory': 'data/',
    'layout_directory': 'layout/',
    'layout': 'default',
    'src_directory': 'src/',
    'template_language': 'jinja2',
}

# should probably make these do some validation!
PROPERTY_CONVERTERS = {
    'base_context': str,
    'build_directory': str,
    'data_directory': str,
    'layout_directory': str,
    'src_directory': str,
    'template_language': str,
}

parser = OptionParser()
parser.add_option('-c', '--config', default=None, dest='config',
                  help="path to config file")


# should make this inherit from dict
class Config(object):

    def __init__(self, properties=None):
        self._properties = properties or DEFAULT_PROPERTIES.copy()

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError, e:
            if attr in self._properties:
                return self._properties[attr]
            raise e

    @property
    def base_context(self):
        pass

    def read_context(self, fname):
        """Read the context of fname

        reads the fname as JSON from the data directory if it exists,
        otherwise, {}
        """
        


def read_config(fname=None):
    cp = ConfigParser()
    absname = find_config(fname)
    if absname:
        cp.read(absname)
    else:
        logging.fatal("Config file (%s) not found\n", fname)
        raise SystemExit

    properties = {}
    for section in cp.sections():
        options = cp.options(section)
        if section == 'defaults':
            for o in options:
                t = PROPERTY_TYPES.get(o)
                if t:
                    properties[o] = t(cp.get(section, o))
                else:
                    logging.warn("CONFIG: don't know about option %s "
                                 "in defaults section" % o)

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

