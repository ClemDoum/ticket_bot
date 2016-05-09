# -*- coding: utf-8 -*-
import cPickle as pickle
import datetime
import os
import pprint
import sys

from colorama import Fore


class Struct(object):
    def __init__(self, kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        return "<Struct(%s)>" % pprint.pformat(self.__dict__)

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value

    @property
    def dict(self):
        return self.__dict__

    @dict.setter
    def dict(self, value):
        self.dict = value


def save(object, file_or_buff):
    try:
        try:
            pickle.dump(object, file_or_buff)
            file_or_buff.close()
        except (AttributeError, TypeError):
            with open(file_or_buff, 'w+') as f:
                pickle.dump(object, f)
    except RuntimeError as e:
        if "maximum recursion depth exceeded" in e.message:
            old_limit = sys.getrecursionlimit()
            ratio = 1000000
            sys.setrecursionlimit(old_limit * ratio)
            save(object, file_or_buff)
            sys.setrecursionlimit(old_limit)


def load(file_path):
    try:
        up = pickle.Unpickler(open(file_path, "rb"))
    except (AttributeError, TypeError):
        up = pickle.Unpickler(file_path)
    return up.load()


def in_color(color):
    def function(string):
        return getattr(Fore, color) + string + getattr(Fore, "RESET")

    return function


def in_red(string):
    return in_color("RED")(string)


def in_green(string):
    return in_color("GREEN")(string)


def alter_file_path(path, string, how):
    if how not in ["prefix", "suffix"]:
        raise ValueError("'how' argument must be 'prefix' or 'suffix' "
                         "not %s" % str(how))

    dir_name = os.path.dirname(path)
    basename = os.path.basename(path)

    split = basename.split(".")[:-1] if "." in basename else [basename]
    extension = "." + basename.split(".")[-1] if "." in basename else ""
    name = ".".join(split)
    if how == 'prefix':
        altered_name = "%s_%s" % (string, name)
    elif how == 'suffix':
        altered_name = "%s_%s" % (name, string)
    else:
        raise ValueError("how must be 'prefix' or 'suffix'")
    altered_name += extension
    return os.path.join(dir_name, altered_name)


def prefix_file_name(file_path, prefix):
    return alter_file_path(file_path, prefix, "prefix")


def suffix_file_name(file_path, suffix):
    return alter_file_path(file_path, suffix, "suffix")


def get_stamp(format="%Y%m%d_%H%M%S"):
    return datetime.datetime.now().strftime(format)


def replace_extension(file_path, new_extension):
    basename = os.path.basename(file_path)

    split = basename.split(".")[:-1] if "." in basename else [basename]

    basename = ".".join(split) + "." + new_extension
    return os.path.join(os.path.dirname(file_path), basename)
