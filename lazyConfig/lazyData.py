#!/usr/bin/env python

import os
import yaml

from collections.abc import Sequence, Mapping, Iterator

EXTENSION_LIST = ['.yml', '.yaml', '.json']
KEYFILE = '__config__'

class LazyList(Sequence):
    def __init__(self, path, length):
        assert os.path.isdir(path), 'can only generate LazyList from valid directory'
        self.path=path
        self.length=length

    def __getitem__(self, key:[int, tuple, slice]):
        #TODO: allow for directories
        if isinstance(key, int):
            if 0>key>-self.length:
                key = self.length + key
            try:
                return pyyaml_load(is_file_with_extension(os.path.join(self.path, f"{key}")))
            except FileNotFoundError:
                raise IndexError('list index out of range')
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
        assert os.path.isdir(path), 'can only generate LazyDict from valid directory'

        self._raw_dict = {}
        # does Keyfile exist?
        if f:=is_file_with_extension(os.path.join(path, KEYFILE)):
            self._raw_dict = pyyaml_load(f)
            assert isinstance(self._raw_dict, dict), ("naked list in Keyfile not allowed: "
                "use list in a lower level or a LazyList in directory")
        
        self.path = path
        self._lazy_keys = ls_directory_strip_extensions(self.path)
        assert not set(self._raw_dict.keys()).intersection(self._lazy_keys), 'duplicate keys not allowed'

    def __getitem__(self, key:str):
        if result :=self._raw_dict.get(key):
            return result
        path_candidate = os.path.join(self.path, key)
        if f:=is_file_with_extension(path_candidate):
            return pyyaml_load(f)
        elif os.path.isdir(path_candidate):
            # is LazyList?
            if f:=is_file_with_extension(os.path.join(path_candidate, '0')):
                length = len(os.listdir(path_candidate))
                assert is_file_with_extension(os.path.join(
                    path_candidate, 
                    f"{length-1}" # last element
                )), f"{f} indicates LazyList, but the last element deduced by the number of files does not exist"

                return LazyList(path_candidate, length)
            else:
                return LazyDict(path_candidate)
        else:
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
        if(self.dict_in_progress):
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
    with open(path, 'r') as f:
        return yaml.unsafe_load(f)


if __name__ == "__main__":
    d=LazyDict('test_config_default')
    l = d['list']
    list(d.keys())