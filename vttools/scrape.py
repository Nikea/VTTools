# ######################################################################
# Copyright (c) 2014, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# Redistribution and use in source and binary forms, with or without   #
# modification, are permitted provided that the following conditions   #
# are met:                                                             #
#                                                                      #
# * Redistributions of source code must retain the above copyright     #
#   notice, this list of conditions and the following disclaimer.      #
#                                                                      #
# * Redistributions in binary form must reproduce the above copyright  #
#   notice this list of conditions and the following disclaimer in     #
#   the documentation and/or other materials provided with the         #
#   distribution.                                                      #
#                                                                      #
# * Neither the name of the Brookhaven Science Associates, Brookhaven  #
#   National Laboratory nor the names of its contributors may be used  #
#   to endorse or promote products derived from this software without  #
#   specific prior written permission.                                 #
#                                                                      #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS  #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT    #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS    #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE       #
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,           #
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES   #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR   #
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)   #
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,  #
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OTHERWISE) ARISING   #
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                          #
########################################################################

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import six
import inspect
import importlib
import logging
import re
from collections import OrderedDict
from numpydoc.docscrape import FunctionDoc, ClassDoc
import numpy

from skxray.core import verbosedict
import abc

logger = logging.getLogger(__name__)

vt_reserved = ('domain', 'window')


class AutowrapError(Exception):
    '''Exception to flag an autowrapping error

    '''
    pass


def obj_src(py_obj, escape_docstring=True):
    """Get the source for the python object that gets passed in

    Parameters
    ----------
    py_obj : callable
        Any python object

    escape_doc_string : bool
        If true, prepend the escape character to the docstring triple quotes

    Returns
    -------
    list
        Source code lines

    Raises
    ------
    IOError
        Raised if the source code cannot be retrieved
    """
    src = inspect.getsource(py_obj)
    if escape_docstring:
        src.replace("'''", "\\'''")
        src.replace('"""', '\\"""')
    return src
    # return src.split('\n')


def docstring_class(pyobj):
    """Get the docstring dictionary of a class

    Parameters
    ----------
    pyobj : function name or class name
        Any object in Python for which you want the docstring

    Returns
    -------
    ClassDoc
        If pyobj is a class

        A dictionary of the formatted numpy docstring can be
            accessed by :code:`return_val[]`
            Keys:
                'Signature': '',
                'Summary': [''],
                'Extended Summary': [],
                'Parameters': [],
                'Returns': [],
                'Raises': [],
                'Warns': [],
                'Other Parameters': [],
                'Attributes': [],
                'Methods': [],
                'See Also': [],
                'Notes': [],
                'Warnings': [],
                'References': '',
                'Examples': '',
                'index': {}
        Taken from:
            https://github.com/numpy/numpydoc/blob/master/numpydoc/docscrape.py#L94
    """
    if inspect.isclass(pyobj):
        return ClassDoc(pyobj)
    else:
        raise ValueError("The pyobj input parameter is not a class."
                         "Your parameter returned {0} from "
                         "type(pyobj)".format(type(pyobj)))


def docstring_func(pyobj):
    """Get the docstring dictionary of a function

    Parameters
    ----------
    pyobj : function name
        Any object in Python for which you want the docstring

    Returns
    -------
    FunctionDoc
        If pyobj is a function or class method

        A dictionary of the formatted numpy docstring can be
            accessed by :code:`return_val[]`
            Keys:
                'Signature': '',
                'Summary': [''],
                'Extended Summary': [],
                'Parameters': [],
                'Returns': [],
                'Raises': [],
                'Warns': [],
                'Other Parameters': [],
                'Attributes': [],
                'Methods': [],
                'See Also': [],
                'Notes': [],
                'Warnings': [],
                'References': '',
                'Examples': '',
                'index': {}
        Taken from:
            https://github.com/numpy/numpydoc/blob/master/numpydoc/docscrape.py#L94
    """
    return FunctionDoc(pyobj)


def _extract_default_vals(pyobj):
    """
    This is a helper function that scrapes default parameter values for
    incorporation into the automatic function wrapper for incorporating
    functions into VisTrails.

    Parameters
    ----------
    pyobj : callable
        Valid python function from which any specified default values will
        be scraped and incorporated into the associated VisTrails object.

    Returns
    -------
    kwarg_defaults : dict
        Dictionary containing PARAMETER : DEFAULT_VALUE pairs.
    """

    try:
        names, _, _, d_vals = inspect.getargspec(pyobj)
        if bool(d_vals):
            return dict(zip(names[-len(d_vals):], d_vals))

    except TypeError:
        logging.debug("getargspec failed on %s", pyobj)

    return dict()


def _type_optional(type_str):
    """
    Helper function to sort out if a parameter is optional

    This assumes the type is given by a string that is compliant with
    the numpydoc format.

    Parameters
    ----------
    type_str : str
        The type specification from the docstring

    Returns
    -------
    type_str : str
        The type specification with out the optional flag

    is_optional : bool
        If the input is optional
    """
    type_str = type_str.strip(' .')
    matches = _OPTIONAL_RE.search(type_str)
    if matches:
        is_optional = True
        type_str, opt_str = matches.groups()
    else:
        is_optional = False

    return type_str, is_optional


_OR_REGEX = re.compile(r'\bor\b')
_OF_REGEX = re.compile(r'\bof\b')
_COMMA_REGEX = re.compile(r'\b, ?\b')
_ENUM_RE = re.compile('\{(.*)\}')
_OPTIONAL_RE = re.compile('(.*?),? *(\(?optional\)?)')


_RE_DICT = {
    "object": re.compile('^(?i)(any|object)$'),
    "array": re.compile('^(?i).*(((np|numpy)\.)?(nd)?array(_|-| |s)?(like)?)'),  # noqa,
    "matrix": re.compile('^(?i)(\((([A-Z0-9.]+,? *){2} ?)\))? *(((np|numpy)\.)?matrix(_|-| )?(like)?)$'),  # noqa,
    # note these three do not match end so 'list of ... ' matches
    "list": re.compile('^(?i)list(-|_| )?(like)?'),
    "tuple": re.compile('(?i)tuple(-|_| )?(like)?'),
    "seq": re.compile('(?i)sequence(-|_| )?(like)?'),
    "dtype": re.compile('^(?i)((np|numpy)[. ])?d(ata)?[- _]?type[-_ ]?(like|code|specifier)?'),  # noqa
    "bool": re.compile('^(?i)bool(ean)?$'),
    "file": re.compile('^(?i)file(name)?[ -_]*(like|handle|object)*$'),
    "scalar": re.compile('^(?i)(scalar|number)'),
    "float": re.compile('^(?i)(((np|numpy)\.)?float(16|32|64|128)?|double|single)'),  # noqa,
    "int": re.compile('^(?i)((np|numpy)\.)?u?int(eger)?(8|16|32|64)?( value|s)?$'),      # noqa
    "complex": re.compile('^(?i)complex$'),
    "dict": re.compile('^(?i)dict(ionary)?$'),
    "str": re.compile('^(?i)str(ing)?([-]?like)?'),
    'callable': re.compile('^(?i)(func(tion)?|callable)'),
}

sig_map = verbosedict({
    'object': 'basic:Variant',
    'array': 'basic:Variant',
    'matrix': 'basic:Variant',
    'list': 'basic:List',
    'tuple': 'basic:List',
    'seq': 'basic:List',
    'dtype': 'basic:String',
    'bool': 'basic:Boolean',
    'file': 'basic:File',
    'scalar': 'basic:Float',
    'float': 'basic:Float',
    'int': 'basic:Integer',
    'complex': 'basic:Variant',
    'dict': 'basic:Dictionary',
    'str': 'basic:String',
    'callable': 'basic:Variant'
})


precedence_list = ('list',
                   'tuple',
                   'seq',
                   'dict',
                   'array',
                   'matrix',
                   'dtype',
                   'str',
                   'scalar',
                   'complex',
                   'float',
                   'int',
                   'bool',
                   'file',
                   'callable',
                   'object')


#   RE Details:
#   WORKS: test_str5 = "(your, mother, was, a, hampster) array"
#   WORKS: test_str5 = "(your, mother, was, a, hampster,) array"
# TODO: We may want to make more thorough use of this RE by using the
#   specified values inside the parentheses as an additional input or output
#   port key (e.g. 2D, 3D, 1xN, NxN, NxM, LxMxN, etc.)


def _enum_type(type_str):
    """
    Helper function to check if the docstring enumerates options

    Parameters
    ----------
    type_str : str
        String specifying the input type. This string was stripped from the
        numpydoc string.

    Returns
    -------
    type_out : str
        The type of the input suitable for translation to VT types

    is_enum : bool
        Boolean switch specifying whether inputs include enumerated options.
    """
    m = _ENUM_RE.search(type_str)
    if bool(m):
        is_enum = True
        enum_list = [_.strip('\'\" ') for _ in m.group(1).split(',')]
        guessed_types = [_guess_enum_val_type(_) for _ in enum_list]
        type_out = guessed_types[0]
        if not all(_ == type_out for _ in guessed_types[1:]):
            raise ValueError('Mixed type enum, docstring parameters are '
                             'improperly defined. Please fix and create pull '
                             'request, or report this error to the Software '
                             'Development Team.')
        if type_out not in ('int', 'str'):
            raise ValueError('Enum is not discrete, docstring parameters are '
                             'improperly defined. Please fix and create pull '
                             'request, or report this error to the Software '
                             'Development Team.')
    else:
        is_enum = False
        enum_list = None
        type_out = type_str

    return type_out, is_enum, enum_list


def _truncate_description(original_description, word_cnt_to_include):
    """
    This function will truncate the stripped doc string to a more manageable
    length for incorporation into wrapped vistrails functions

    Parameters
    ----------
    original_description : list
        This object is the original description stripped from the
        doc string. The object is actually a list of strings.

    word_cnt_to_include : int
        specify the number of words to trim the description down to

    Returns
    -------
    short_description : string
        truncated description that will be passed into vistrails
    """
    short_description = original_description[0]
    # need this twice, might as well stash it
    sd_words = short_description.split(' ')
    # if it's too long, drop some words
    if len(sd_words) > word_cnt_to_include:
        short_description = ' '.join(sd_words[:word_cnt_to_include])

    return short_description


def _guess_enum_val_type(stringy_val):
    """
    Helper function to guess the type of values in an enum are.

    At this point it tries int, float, and complex and then assumes it is
    a string.

    Parameters
    ----------
    stringy_val : str
        The value to guess the type of

    Returns
    -------
    type_str : {'int', 'float', 'complex', 'str'}
        The guessed type as a string.
    """
    od = OrderedDict()
    od['int'] = int
    od['float'] = float
    od['complex'] = complex

    for k, v in six.iteritems(od):
        try:
            v(stringy_val)
            return k
        except ValueError:
            pass
    # give up and assume it is a string
    return 'str'


def _normalize_type(the_type):
    """
    A single entry point for parsing the type.

    This assumes that enums and optional properties have been
    taken care of.

    Parameters
    ----------
    the_type : str
        The type string extracted from the docs

    Returns
    -------
    norm_type : str
        The normalized type
    """
    # get rid of all leading and trailing junk
    the_type = the_type.strip(' .!?-_\t`').rstrip(' .!?-_\t`')
    # if 'or'
    if _OR_REGEX.search(the_type):
        left, right = the_type.split('or', 1)
        return _type_precedence(left, right)

    if _OF_REGEX.search(the_type):
        left, right = the_type.split('of', 1)
        return _of_proc(left, right)

    # Walk the precedence list to see what we get
    for n_type in precedence_list:
        if bool(_RE_DICT[n_type].search(the_type)):
            return n_type

    if _COMMA_REGEX.search(the_type):
        left, right = the_type.split(',', 1)
        return _type_precedence(left, right)

    # of no patterns matched, return None to signal
    # failure and let down-stream sort it out.
    return None


def _of_proc(left, right):
    """
    Processes a type which includes the word 'of'.

    Right now this is very simple and just returns
    the left side.
    """
    left = _normalize_type(left)
    if left in ('list', 'tuple', 'array', 'matrix', 'seq'):
        return left
    return None


def _type_precedence(left, right):
    """
    Reduce a pair of types to a single type by picking
    which one to return.


    """
    left = _normalize_type(left)
    right = _normalize_type(right)
    if left is None:
        return right
    elif right is None:
        return left

    left_i = precedence_list.index(left)
    right_i = precedence_list.index(right)
    return left if left_i < right_i else right


def _enums_equal(left, right):
    """
    Compare two lists of enumn and determine if they are equivalent.
    """
    return set(str(_) for _ in left) == set(str(_) for _ in right)

_enum_error = ('Attempting to automatically create '
              'an enum port for the function named'
              ' {0}. The values for the enum port '
                'defined in the doc string are {1} '
                'with length {2} and there is a '
                'function attribute with values {3} '
                'and length {4}.  Please make sure '
                'the values in the docstring agree '
                'with the values in the function '
                'attribute, as I\'m not sure which '
                'to use.')


def define_input_ports(docstring, func, short_description_word_count=4):
    """Turn the 'Parameters' fields into VisTrails input ports

    Parameters
    ----------
    docstring : List of strings?
        The scraped docstring from the NumpyDocString. This is the output of
        docstring_func()

    func : function
        The actual python function

    Returns
    -------
    input_ports : list
        Dictionaries of meta-data for the input ports of the functions
    """
    input_ports = []

    kwarg_defaults = _extract_default_vals(func)

    for (the_name, the_type, the_description) in docstring['Parameters']:
        # skip in-place returns
        if the_name in ['output', 'out']:
            continue
        # deal with np.frexp
        if not the_type and ':' in the_name:
            the_name, the_type = the_name.split(':')
        # parse and normalize
        type_base, is_optional = _type_optional(the_type)
        type_base, is_enum, enum_list = _enum_type(type_base)
        normed_type = None
        # this is to deal with malformed docstrings like {array, scalar}
        if is_enum and type_base == 'str':
            try_norm = _normalize_type(' or '.join(enum_list))
            if try_norm is not None:
                is_enum = False
                enum_list = []
                logger.warning("abuse of enum  %s |%s <%s>|",
                    func.__name__, the_name, the_type)
                normed_type = try_norm
        # see if we still need to normalize
        if normed_type is None:
            normed_type = _normalize_type(type_base)
        # see if we have a problem
        if normed_type is None:
            raise AutowrapError("Malformed input type |{}: <{}>|".format(
                the_name, the_type))

        # Trim parameter descriptions for incorporation into vistrails
        short_description = _truncate_description(the_description,
                                                  short_description_word_count)

        logger.debug("the_name is {0}. \n\tthe_type is {1} and it is "
                     "optional: {3}. \n\tthe_description is {2}"
                     "".format(the_name, normed_type,
                               short_description,
                               is_optional))

        for port_name in (_.strip() for _ in the_name.split(',')):
            if not port_name:
                continue
            port_type = normed_type
            port_is_enum = is_enum
            port_enum_list = enum_list

            pdict = {'label': short_description,
                     'docstring': '\n'.join(the_description),
                     'optional': is_optional,
                     'signature': sig_map[port_type]}

            if port_name in kwarg_defaults:
                tmp_v = kwarg_defaults[port_name]
                if pdict['signature'] in ['basic:List',
                                          'basic:Variant',
                                          'basic:Dictionary']:
                    logger.info(("Trying to set default value for non-constant"
                                 "type "
                                   "%s: |%s <%s>| (%s)"),
                                   func.__name__, the_name, the_type,
                                   tmp_v)
                else:
                    pdict['default'] = tmp_v
                    pdict['optional'] = True

            # start with the easy ones
            if port_name in vt_reserved:
                port_name = '_' + port_name
            pdict['name'] = port_name

            # deal with if the function as an enum attribute
            if hasattr(func, port_name):
                f_enums = getattr(func, port_name)
                if port_is_enum:
                    # if we already think this is an enum, make sure they
                    # match
                    if not _enums_equal(enum_list, f_enums):
                        format_args = (the_name, enum_list, len(enum_list),
                                       f_enums, len(f_enums))
                        raise ValueError(_enum_error.format(*format_args))

                port_enum_list = f_enums
                port_is_enum = True
            if port_is_enum:
                pdict['entry_type'] = 'enum'
                pdict['values'] = port_enum_list

            logger.debug('port_param_dict: {0}'.format(pdict))
            input_ports.append(pdict)

    return input_ports


def define_output_ports(docstring, short_description_word_count=4):
    """
    Turn the 'Returns' fields into VisTrails output ports

    Parameters
    ----------
    docstring : NumpyDocString #List of strings?
        The scraped docstring from the function being autowrapped into
        vistrails

    Returns
    -------
    input_ports : list
        List of input_ports (Vistrails type IPort)
    """

    output_ports = []

    # now look at the return Returns section
    for (the_name, the_type, the_description) in docstring['Returns']:
        base_type, is_optional = _type_optional(the_type)
        if is_optional:
            continue

        type_base, is_enum, enum_list = _enum_type(the_type)
        normed_type = None
        # this is to deal with malformed docstrings like {array, scalar}
        if is_enum and type_base == 'str':
            try_norm = _normalize_type(' or '.join(enum_list))
            if try_norm is not None:
                is_enum = False
                enum_list = []
                logger.warning("abuse of enum %s | <%s>|",
                    docstring['Signature'], the_type)
                normed_type = try_norm

        # first try to parse
        if normed_type is None:
            normed_type = _normalize_type(type_base)

        # deal with if we fail to parse
        if normed_type is None:
            raise AutowrapError("Malformed output type |{}: <{}>|".format(
                the_name, the_type))

        for port_name in (_.strip() for _ in the_name.split(',')):
            if not port_name:
                raise AutowrapError("A Port with no name")
            pdict = {'name': port_name,
                     'signature': sig_map[normed_type]}

            output_ports.append(pdict)

    # some numpy functions lack a Returns section and have and 'output'
    # optional input (mostly for in-place operations)
    if len(output_ports) < 1:
        for (the_name, the_type, the_description) in docstring['Parameters']:
            if the_name.lower() in ['output', 'out']:
                the_type, _ = _type_optional(the_type)
                the_type = _normalize_type(the_type)
                if the_type is None:
                    # TODO dillify
                    raise AutowrapError("Malformed type")
                output_ports.append(dict(name=the_name,
                                          signature=sig_map[the_type]))

    return output_ports


def scrape_function(func_name, module_path):
    """Scrap function doc-string of a function for intput/output types

    Parameters
    ----------
    func_name : str
        Name of the function to wrap into VisTrails. Example 'grid3d'

    module_path : str
        Name of the module which contains the function. Example: 'skxray.core'

    Returns
    -------
    spec : dict
        A dictionary with enough information to construct a VT module.

       -----------  -----------------
       key          value
       ------------ -----------------
       input_ports  list of dicts
       output_ports list of dicts
       doc_string   doc string
       f_type       {func, ufunc}
       func_name    name of function
       module_path  location of function

    """
    # func_name, mod_name = imp
    mod = importlib.import_module(module_path)
    func = getattr(mod, func_name)

    # get the docstring of the function
    doc = docstring_func(func)

    # get the source of the function
    try:
        # if we can get the source, use the whole thing as the
        # docstring in vistrails
        doc_string = obj_src(func)
    except (IOError, TypeError):
        # if we can't, just use the docstring
        doc_string = func.__doc__
    # create the VisTrails input ports
    input_ports = define_input_ports(doc, func)
    # pprint.pprint(input_ports)
    # create the VisTrails output ports
    output_ports = define_output_ports(doc)
    if isinstance(func, numpy.ufunc):
        f_type = 'ufunc'
    else:
        f_type = 'func'
    return {'input_ports': input_ports,
            'output_ports': output_ports,
            'doc_string': doc_string,
            'f_type': f_type,
            'func_name': func_name,
            'module_path': module_path}


def scrape_module(module_path, black_list=None,
                  exclude_markers=None,
                  exclude_private=True):
    """
    Attempt to scrape all functions from a module.

    Parameters
    ----------
    module_path : str
        The module to scrape

    black_list : list or None, optional
        List of functions to not attempt to scrape

    exclude_markers : iterable or None
        iterable of strings.  If any of the string are
        contained in the function name, it is skipped

    exclude_private : bool
        If True, do not scrape private (prefixed by '_') functions


    Returns
    -------
    spec_dict : dict
        A dictionary keyed on function name of dictionaries
        specifying the input/output types of the functions
        suitable for passing to `wrap_lib.wrap_function`
    """
    # deal with defaults
    if black_list is None:
        black_list = []

    if exclude_markers is None:
        exclude_markers = []

    black_list = set(black_list)

    # grab the module from it's name
    mod = importlib.import_module(module_path)

    if hasattr(mod, '__all__'):
        trial_list = mod.__all__
    else:
        trial_list = dir(mod)

    funcs_to_wrap = []
    for atr_name in trial_list:
        # if a private member, continue
        if exclude_private and atr_name.startswith('_'):
            continue
        # if we know it is black listed, continue
        if atr_name in black_list:
            continue
        # grab the attribute so we can introspect
        atr = getattr(mod, atr_name)

        # check the exclude markers
        if any(k in atr_name for k in exclude_markers):
            continue

        # if the attribute is not a callable or it is of type 'type'
        # (meaning it is a class) continue
        if not callable(atr) or type(atr) in (type, abc.ABCMeta):
            continue

        funcs_to_wrap.append(atr_name)

    ret = dict()
    for ftw in funcs_to_wrap:
        try:
            spec_dict = scrape_function(ftw, module_path)
            ret[ftw] = spec_dict
        except Exception as e:
            logger.warn("%s failed scraping on %s.%s",
                        e, module_path, ftw)

    return ret
