import logging
import os
import os.path as osp
import subprocess

from jinja2 import evalcontextfilter, Markup
from markdown import markdown as convert_markdown
from collections import defaultdict
from utils import reroot

__BUILDERS = defaultdict(lambda: build_static)


def register(*exts):
    """Registers function as a builder, which will build passed in `src_file`
    and returns the destination, given `config` and `src_file`
    """
    def decorator(func):
        for ext in exts:
            __BUILDERS[ext] = func
        return func
    return decorator


def build_file(config, src_file, dest_file):
    """Dispatches to the appropriate builder given file extension

    Each of the handlers should return the path of the file that was
    built. This allows handlers to change extensions as part of the
    build process (for coffee, less, etc)
    """
    dest_dir = osp.dirname(dest_file)
    if not osp.exists(dest_dir):
        os.makedirs(dest_dir)

    _, ext = osp.splitext(src_file)
    return __BUILDERS[ext](config, src_file, dest_file)
        

@register('.html')
def build_html(config, src_file, dest_file):
    """Builds HTML files from templates
    
    TODO: this should be generalized such that other templating engines
          can be utilized (as the config suggests)
    """
    src_dir = osp.abspath(config.src_directory)
    base_ctx = config.base_context() or {}
    data_ctx = config.read_context(src_file.replace('.html', '.json'))
    base_ctx.update(data_ctx)

    dest_dir = osp.dirname(dest_file)

    if not osp.exists(dest_dir):
        os.makedirs(dest_dir)

    logging.info("Rendering file: %s to %s" % (src_file, dest_file))
    render_jinja2(env=config.template_env, 
                  src=src_file[len(src_dir):],
                  dest=dest_file,
                  context=base_ctx)

    return dest_file


def build_static(config, src_file, dest_file):
    """Copies src_file to proper destination.

    Handler for files that need not be touched.
    """
    # copy the file
    logging.info("Copying file: %s to %s" % (src_file, dest_file))
    with open(src_file, 'rb') as src:
        with open(dest_file, 'wb') as dest:
            dest.write(src.read())

    return dest_file


@register('.js')
def build_js(config, src_file, dest_file):
    """Attempts to build javascript, coffee, or iced-coffee-script files.

    * If extension is .coffee, or .iced, build and change to .js.
    * If extension is .js, this is just `build_static`

    TODO: make this compile (iced-)coffee files, both files exist and the
    js file is older than the coffee.
    """
    if not osp.exists(src_file):
        base, _ = osp.splitext(src_file)
        for ext, func in [('.coffee', build_coffee), ('.iced', build_iced)]:
            if osp.exists(base + ext):
                dbase, _ = osp.splitext(dest_file)
                return func(config, base + ext, dbase + '.js')

    return build_static(config, src_file, dest_file)


@register('.css')
def build_css(config, src_file, dest_file):
    """Attempts to build a css file, or .less to .css should the .css
    be missing.

    * If extension is .less, build_less to thing.css
    * If extension is .css, this is just `build_static`

    TODO: make this compile (iced-)coffee files, both files exist and the
    js file is older than the coffee.
    """
    if not osp.exists(src_file):
        base, _ = osp.splitext(src_file)
        for ext, func in [('.less', build_less)]:
            if osp.exists(base + ext):
                dbase, _ = osp.splitext(dest_file)
                return func(config, base + ext, dbase + '.css')

    return build_static(config, src_file, dest_file)


@register('.coffee')
def build_coffee(config, src_file, dest_file):
    base, ext = osp.splitext(dest_file)
    dest_file = base + '.js'
    logging.info("Building file with coffee: %s to %s" % (src_file, dest_file))
    output = subprocess.check_output(["coffee", "--print", src_file])
    with open(dest_file, 'wb') as f:
        f.write(output)
    return dest_file


@register('.iced')
def build_iced(config, src_file, dest_file):
    base, ext = osp.splitext(dest_file)
    dest_file = base + '.js'
    logging.info("Building file with iced: %s to %s" % (src_file, dest_file))
    output = subprocess.check_output(["iced", "--runtime", "inline",
                                      "--print", src_file])
    with open(dest_file, 'wb') as f:
        f.write(output)
    return dest_file


@register('.less')
def build_less(config, src_file, dest_file):
    """Build src_file to dest_file.css using lessc
    """
    base, ext = osp.splitext(dest_file)
    dest_file = base + '.css'
    logging.info("Building file with lessc: %s to %s" % (src_file, dest_file))
    subprocess.call(["lessc", src_file, dest_file])

    return dest_file


@evalcontextfilter
def markdown(ectx, text):
    result = convert_markdown(text)
    if ectx.autoescape:
        result = Markup(result)
    return result

def render_jinja2(env=None, src=None, dest=None, context=None):
    env.filters['markdown'] = markdown
    tmpl = env.get_template(src)
    with open(dest, 'w') as f:
        f.write(tmpl.render(**context))

