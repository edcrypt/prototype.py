# -*- coding: utf-8 -*-
#
# Copyright © 2011 Toby Ho
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# “Software”), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
from __future__ import print_function

import six

import types
import inspect


def _getattr(obj, name):
    try:
        return object.__getattribute__(obj, name)
    except AttributeError:
        return None

def _setattr(obj, name, val):
    object.__setattr__(obj, name, val)

def _proto_getattr(obj, name):
    val = _getattr(obj, name)
    while val is None and obj is not None:
        obj = _getattr(obj, '__proto__')
        val = _getattr(obj, name)
    return val

def _proto_clone(constructor):
    def clone(this, *args, **kwargs):
        new_obj = constructor(*args, **kwargs)
        new_obj.__proto__ = this
        return new_obj
    return clone

def _proto_method(obj):
    def _method(func):
        setattr(obj.prototype, func.__name__, func)
    return _method


class ObjectMetaClass(type):
    def __repr__(cls):
        return "<constructor '%s'>" % cls.__name__


@six.add_metaclass(ObjectMetaClass)
class Object(object):
    prototype = None

    def __init__(this):
        this.__proto__ = this.prototype
        this.constructor = this.__class__
        this.clone = _proto_clone(this.constructor)

    def __getattribute__(this, name):
        val = _proto_getattr(this, name)
        if isinstance(val, property) and val.fget:
            get = types.MethodType(val.fget, this)
            return get()
        elif inspect.isfunction(val):
            func = types.MethodType(val, this)
            return func
        else:
            return val

    def __setattr__(this, name, val):
        if not isinstance(val, property):
            _val = _proto_getattr(this, name)
            if isinstance(_val, property) and _val.fset:
                _val.fset(this, val)
                return
        _setattr(this, name, val)

    def __delattr__(this, name):
        val = _proto_getattr(this, name)
        if isinstance(val, property) and val.fdel:
            val.fdel(this)
        else:
            object.__delattr__(this, name)


Object.prototype = Object()

def constructor(func):
    ret = type(func.__name__, (Object,), dict())
    ret.prototype = ret()
    ret.method = _proto_method(ret)

    def init(this, *vargs, **kwargs):
        Object.__init__(this)
        func(this, *vargs, **kwargs)
    ret.__init__ = init
    return ret
