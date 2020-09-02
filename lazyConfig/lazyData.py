#!/usr/bin/env python

from collections.abc import Sequence, Mapping, Iterator
from enum import Enum

import os
import yaml

EXTENSION_LIST = ['.yml', '.yaml', '.json']
KEYFILE = '__config__'


class LazyMode(Enum):
    eager = 0
    cached = 1
    lazy = 2

class LazyList(Sequence):
    def __init__(self, path, length):
        # assert os.path.isdir(path), 'can only generate LazyList from valid directory'
        self.path=path
        self.length=length

    def __getitem__(self, key:[int, tuple, slice]):
        #TODO: allow for directories
        if isinstance(key, int):
            if 0>key>-self.length:
                key = self.length + key
            try:
                return pyyaml_load(is_file_with_extension(os.path.join(self.path, f"{key}")))
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



class LazyDict(Mapping):
    def __init__(self, path:str=''):
        # assert os.path.isdir(path), 'can only generate LazyDict from valid directory'

        self._raw_dict = {}
        # does Keyfile exist?
        if keyfile:=is_file_with_extension(os.path.join(path, KEYFILE)):
            self._raw_dict = pyyaml_load(keyfile)
            assert isinstance(self._raw_dict, dict), ("naked list in Keyfile not allowed: "
                "use list in a lower level or a LazyList in directory")

        self.path = path
        self._lazy_keys = ls_directory_strip_extensions(self.path)
        assert not set(self._raw_dict.keys()).intersection(self._lazy_keys), 'duplicate keys not allowed'

    def __getitem__(self, key:str):
        if result :=self._raw_dict.get(key):
            return result
        path_candidate = os.path.join(self.path, key)
        if cfile:=is_file_with_extension(path_candidate):
            return pyyaml_load(cfile)
        if os.path.isdir(path_candidate):
            # is LazyList?
            if lfile:=is_file_with_extension(os.path.join(path_candidate, '0')):
                length = len(os.listdir(path_candidate))
                assert is_file_with_extension(os.path.join(
                    path_candidate,
                    f"{length-1}" # last element
                )), (f"{lfile} indicates LazyList, but the last element deduced"
                    "by the number of files does not exist")

                return LazyList(path_candidate, length)
            else:
                return LazyDict(path_candidate)
        raise KeyError(key)

    def __len__(self):
        return len(self._raw_dict) + len(self._lazy_keys)

    def __iter__(self):
        return LazyDictIterator(self)

    def __repr__(self):
        return f"LazyDict(path='{self.path}')"

    def __str__(self):
        return (f"LazyDict(path={self.path}):\n"
            + "    Loaded Dict: "
            + self._raw_dict.__str__() + "\n"
            + "    Lazy Keys: "
            + self._lazy_keys.__str__() + '\n'
        )

#TODO: the if check in every iteration should be surperflous (inefficient)
# check if you can get rid of it using generators with two yield statements
class LazyDictIterator(Iterator):
    def __init__(self, lazyDict:LazyDict):
        self.lazyDict = lazyDict
        self.dictIter = iter(lazyDict._raw_dict)
        self.lazyKeysIter = iter(lazyDict._lazy_keys)
        self.dict_in_progress = True

    def __next__(self):
        if self.dict_in_progress:
            try:
                return self.dictIter.__next__()
            except StopIteration:
                self.dict_in_progress = False
                return self.lazyKeysIter.__next__()
        else:
            return self.lazyKeysIter.__next__()


def ls_directory_strip_extensions(dir_path:str) -> list:
    return [name for p in os.listdir(dir_path) if (name:=os.path.splitext(os.path.basename(p))[0]) != KEYFILE]


def is_file_with_extension(candidate:str, extension_list:list=EXTENSION_LIST) -> str:
    for ext in extension_list:
        if os.path.isfile(tmp:=candidate+ext):
            return tmp
    return ''


def pyyaml_load(path:str)->[dict,list]:
    with open(path, 'r') as cfile:
        return yaml.unsafe_load(cfile)


if __name__ == "__main__":
    # %%
    class LazMode:
        eager = 0
        cached = 1
        lazy = 2
    
    print(LazMode.eager)
    # %%
    print(LazyMode.eager)
    print(type(LazyMode.eager))
    print(isinstance(LazyMode.eager, LazyMode))
