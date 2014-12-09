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
import sys
from skxray.fitting.api import (QuadraticModel, GaussianModel,
                                LorentzianModel, Lorentzian2Model,
                                ExpressionModel)

import logging
logger = logging.getLogger(__name__)

def quadratic_model(prefix,
                    a, a_vary, a_range,
                    b, b_vary, b_range,
                    c, c_vary, c_range):
    """
    Quadratic Model for fitting.

    f(x) = a * x**2 + b * x + c

    Parameters
    ----------
    prefix : str
        prefix name
    a : float
        x -> a * x**2 + b * x + c
    a_vary : str
        variance method
        Options:
            fixed,
            free,
            bounded
    a_range : list
        bounded range
    b : float
        x -> a * x**2 + b * x + c
    b_vary : str
        variance method
        Options:
            fixed,
            free,
            bounded
    b_range : list
        bounded range
    c : float
        x -> a * x**2 + b * x + c
    c_vary : str
        variance method
        Options:
            fixed,
            free,
            bounded
    c_range : list
        bounded range

    Returns
    -------
    g : array_like
        fitting object
    """

    g = QuadraticModel(prefix=prefix)
    set_range(g, 'a', a, a_vary, a_range)
    set_range(g, 'b', b, b_vary, b_range)
    set_range(g, 'c', c, c_vary, c_range)

    return g

quadratic_model.a_vary = ['fixed', 'free', 'bounded']
quadratic_model.b_vary = ['fixed', 'free', 'bounded']
quadratic_model.c_vary = ['fixed', 'free', 'bounded']


def fit_engine(g, x, y):
    """
    This function is to do fitting based on given x and y values.

    Parameters
    ----------
    g : array_like
        fitting object
    x : array
        independent variable
    y : array
        dependent variable

    Returns
    -------
    result : array_like
        object of fitting results
    y_fit : array
        fitted y
    """
    result = g.fit(y, x=x)
    y_fit = result.best_fit

    return result, y_fit


def fit_engine_list(g, data):
    """
    This function is to do fitting on a list of x and y values.

    Parameters
    ----------
    g : array_like
        fitting object
    data : array
        list of (x,y)

    Returns
    -------
    result : array_like
        list of object saving fit results
    """
    result_list = []
    for v in data:
        result = g.fit(v[1], x=v[0])
        result_list.append(result)
    return result_list


def expression_model(model_exp):
    """
    This function creates a Model from a user-supplied expression.

    Parameters
    ----------
    model_exp : str
        expression of the model

    Returns
    -------
    mod : array_like
        object of fitting results
    """
    mod = ExpressionModel(model_exp)
    return mod


def set_range(model_name,
              parameter_name, parameter_value,
              parameter_vary, parameter_range):
    """
    set up fitting parameters in lmfit model

    Parameters
    ----------
    model_name : class object
        Model class object from lmfit
    parameter_name : str
    parameter_value : value
    parameter_vary : str
        fixed, free or bounded
    parameter_range : list
        [min, max]
    """
    if parameter_vary == 'fixed':
        model_name.set_param_hint(parameter_name, value=parameter_value, vary=False)
    elif parameter_vary == 'free':
        model_name.set_param_hint(parameter_name, value=parameter_value)
    elif parameter_vary == 'bounded':
        model_name.set_param_hint(parameter_name, value=parameter_value,
                                  min=parameter_range[0], max=parameter_range[1])
    else:
        raise ValueError("unrecognized value {0}".format(parameter_vary))


doc_template = """
    wrapper of {0} fitting model for vistrails.

    Parameters
    ----------
    prefix : str
        prefix name
    amplitude : float
        area under peak profile
    amplitude_vary : str
        variance method
        Options:
            fixed,
            free,
            bounded
    amplitude_range : list
        bounded range
    center : float
        center position
    center_vary : str
        variance method
        Options:
            fixed,
            free,
            bounded
    center_range : list
        bounded range
    sigma : float
        standard deviation
    sigma_vary : str
        variance method
        Options:
            fixed,
            free,
            bounded
    sigma_range : list
        bounded range

    Returns
    -------
    g : array_like
        fitting object
    """


def _three_param_fit_factory(model):
    """
    Fit factory is used to include three functions, gauss, lorentzian
    and lorentzian, which have similar arguments and outputs.

    Parameters
    ----------
    model : class object
        A model object defined in lmfit

    Returns
    -------
    function
        The main task of th function is to do the fitting.
    """
    def inner(prefix, amplitude, amplitude_vary, amplitude_range,
              center, center_vary, center_range,
              sigma, sigma_vary, sigma_range):

        g = model(prefix=prefix)
        set_range(g, 'amplitude', amplitude, amplitude_vary, amplitude_range)
        set_range(g, 'center', center, center_vary, center_range)
        set_range(g, 'sigma', sigma, sigma_vary, sigma_range)

        return g

    inner.__doc__ = doc_template.format(model.__name__)
    inner.__name__ = model.__name__.lower()[:-5] + str("_model")
    return inner

ModelList = [GaussianModel, LorentzianModel, Lorentzian2Model]

mod = sys.modules[__name__]
for m in ModelList:
    func = _three_param_fit_factory(m)
    setattr(mod, func.__name__, func)


for func_name in [gaussian_model, lorentzian2_model, lorentzian_model]:
    func_name.amplitude_vary = ['fixed', 'free', 'bounded']
    func_name.center_vary = ['fixed', 'free', 'bounded']
    func_name.sigma_vary = ['fixed', 'free', 'bounded']
