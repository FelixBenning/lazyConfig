#!/usr/bin/env python

from typing import Callable, Union, Dict, Optional, Tuple
from collections.abc import Sequence, Mapping, Iterator

import itertools
from enum import Enum

import os
import yaml, json, toml

DEFAULT_EXTENSION_MAP = {
    '.yml': yaml.unsafe_load,
    '.yaml': yaml.unsafe_load,
    '.json': json.load,
    '.toml': toml.load
}

KEYFILE = '__config__'


class LazyMode(Enum):
    EAGER = 0
    CACHED = 1
    LAZY = 2

class LazyList(Sequence):
    def __init__(
        self, path, length, extension, loader:Callable,
        laziness:LazyMode = LazyMode.CACHED
    ):
        # assert os.path.isdir(path), 'can only generate LazyList from valid directory'
        self.path=path
        self.length=length
        self.extension = extension
        self.loader = loader

    def __getitem__(self, key:[int, tuple, slice]):
        #TODO: allow for directories
        if isinstance(key, int):
            if 0>key>-self.length:
                key = self.length + key
            try:
                return load(
                    os.path.join(self.path, f"{key}" + self.extension), 
                    self.loader
                )
            except FileNotFoundError as err:
                raise IndexError('list index out of range') from err
        elif isinstance(key, tuple):
            return [self[x] for x in key] #TODO: performance?
        elif isinstance(key, slice):
            return [self[x] for x in range(self.length)[key]]
        raise TypeError(f'Index must be int, tuple or slice, not {type(key).__name__}')

    def __len__(self):
        return self.length

    def __repr__(self):
        return f"LazyList(path='{self.path}', length={self.length})"
    
    def as_list(self):
        return self[:]
    
    def as_primitive(self):
        """ alias for as_list """
        return self.as_list()


class LazyDict(Mapping):
    def __init__(self, path:str='', laziness:LazyMode = LazyMode.CACHED, extension_map:dict = DEFAULT_EXTENSION_MAP):
        # assert os.path.isdir(path), 'can only generate LazyDict from valid directory'

        self.path = path
        self._laziness = laziness
        self.extension_map = extension_map
        self._raw_dict = {}
        self._cache_dict = {}
        self._lazy_dict = files_in_dir_with_given_ext(
            dir_path= self.path, extensions= self.extension_map.keys())
        
        try:
            extension = self._lazy_dict.pop(KEYFILE)
        except KeyError: # no KEYFILE
            pass
        else:
            assert extension != None, "dictionary with name __config__ is not allowed"
            keyfile = os.path.join(self.path, KEYFILE + extension)
            self._raw_dict = load(keyfile, self.extension_map[extension])
            assert isinstance(self._raw_dict, dict), ("naked list in Keyfile not allowed: "
                "use list in a lower level or a LazyList in directory")

        assert not set(self._raw_dict.keys()).intersection(self._lazy_dict.keys()), 'duplicate keys not allowed'
        
        if self._laziness == LazyMode.EAGER:
            self.force_load()


    def __getitem__(self, key:str):
        try:
            return self._raw_dict[key]
        except KeyError:
            try:
                return self._cache_dict[key]
            except KeyError:
                pass
        if self._laziness in (LazyMode.CACHED, LazyMode.EAGER):
            try:
                extension = self._lazy_dict.pop(key)
            except KeyError as err:
                raise KeyError(key) from err
            self._cache_dict[key] = (cache := self._fetch(key, extension, self._laziness))
            return cache
        else: # LazyMode.LAZY
            try:
                extension = self._lazy_dict[key]
            except KeyError as err:
                raise KeyError(key) from err
            return self._fetch(key, extension, self._laziness)
    
    def force_load(self):
        """ recursively loading all keys into _raw_dict essentially converting
        to a normal dict
        """
        self._laziness = LazyMode.EAGER
        for key, ext in self._lazy_dict.items():
            self._cache_dict[key] = self._fetch(key, ext, LazyMode.EAGER)
        self._lazy_dict = {}
    
    def as_dict(self):
        if self._laziness in (LazyMode.CACHED, LazyMode.EAGER):
            self.force_load()
        result = {key: _as_primitive(value) for key, value in self._cache_dict.items()}
        for key, ext in self._lazy_dict.items():
            result[key] = _as_primitive(self._fetch(key, ext, LazyMode.EAGER))
        result.update(self._raw_dict)
        return result
    
    def as_primitive(self):
        """ alias for as_dict"""
        return self.as_dict()

    def _fetch(self, key, extension, laziness:LazyMode):
        if extension == None: # is dir
            path = os.path.join(self.path, key)
            #is LazyList?
            if result:= dir_is_lazyList(path, self.extension_map.keys()):
                extension, length = result
                return LazyList(path, length, extension, self.extension_map[extension], laziness)
            else:
                return LazyDict(path, laziness, self.extension_map)
        else: # is file
            path = os.path.join(self.path, key + extension)
            return load(path, loader= self.extension_map[extension])

    def __len__(self):
        return len(self._raw_dict) + len(self._lazy_dict) + len(self._cache_dict)

    def __iter__(self):
        return iter(
            list(self._raw_dict.keys())
            + list(self._cache_dict.keys())
            + list(self._lazy_dict.keys())
        )

    def __repr__(self):
        return f"LazyDict(path='{self.path}')"

    def __str__(self):
        return (f"LazyDict(path={self.path}):\n"
            + "    Loaded Dict: "
            + self._raw_dict.__str__() + "\n"
            + "    Cached: "
            + self._cache_dict.__str__() + "\n"
            + "    Lazy Keys: "
            + self._lazy_dict.__str__() + '\n'
        )

def _as_primitive(obj):
    if isinstance(obj, (list, dict)):
        return obj
    if isinstance(obj, (LazyDict, LazyList)):
        return obj.as_primitive()
    raise ValueError('Not a LazyData Type')

def files_in_dir_with_given_ext(dir_path:str, extensions:list) -> list:
    """ returns dictionary of filenames (stripped of their extension) of files in the
    given directory with extensions from the given `extensions` list. 

    Example:
    extensions: ['.txt']
    dir: file1.txt, file2.py
    -> Output: {'file1' : '.txt'}

    names of directories map to None to differentiate it from files with no
    extension i.e. ''.
    """
    result = {}
    for filename in os.listdir(dir_path):
        name, extension = os.path.splitext(filename)
        if extension == '' and os.path.isdir(os.path.join(dir_path, filename)):
            result[name] = None
        elif extension in extensions:
            result[name] = extension
    return result

def dir_is_lazyList(path:str, extension_list:list) -> Optional[Tuple[str, int]]:
    for ext in extension_list:
        if os.path.isfile(os.path.join(path, '0'+ext)):
            length = len(os.listdir(path))
            assert os.path.isfile(
                os.path.join(path, f'{length-1}'+ext)
            ), (f"the file {length-1}{ext} for {length} being the number of files in {path}"
                f"does not exist. Even though it is implied by the file 0{ext}")
            return (ext, length)
    return None

def load(path:str, loader:Callable[[], Union[dict, list]]) -> Union[dict, list]:
    """ load file from path with the provided loader """
    with open(path, 'r') as cfg_file:
        return loader(cfg_file)
