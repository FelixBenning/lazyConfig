#!/usr/bin/env python

import os
import yaml

from collections.abc import Sequence

EXTENSION_LIST = ['.yml', '.yaml', '.json']
KEYFILE = '__config__'

class LazyList(Sequence):
    def __init__(self, path, length):
        self.path=path
        self.length=length
    def __getitem__(self, key:int):
        #TODO: allow for directories
        return load(is_file_with_extension(os.path.join(self.path, f"{key}")))
    
    def __len__(self):
        return self.length



class LazyDict(dict):
    def __init__(self, true_dict:dict, path_pointer:str=''):
        super().__init__(true_dict)
        self.path = path_pointer
    
    def __missing__(self, key:str):
        path_candidate = os.path.join(self.path, key)
        if f:=is_file_with_extension(path_candidate):
            return load(f)
        elif os.path.isdir(path_candidate):
            # is LazyList?
            if f:=is_file_with_extension(os.path.join(path_candidate, '0')):
                length = len(os.listdir(path_candidate))
                assert is_file_with_extension(os.path.join(
                    path_candidate, 
                    f"{length-1}" # last element
                )), f"{f} indicates LazyList, but the last element deduced by the number of files does not exist"

                return LazyList(path_candidate, length)

            true_dict = {}
            # does Keyfile exist?
            if f:=is_file_with_extension(os.path.join(path_candidate, KEYFILE)):
                tru_dict = load(f)
                assert isinstance(tru_dict, dict), ("naked list in Keyfile not allowed: "
                    "use list in a lower level or a LazyList in directory")
            
            return LazyDict(true_dict, path_candidate)
        else:
            raise KeyError(key)          

            


def is_file_with_extension(candidate:str, extension_list:list=EXTENSION_LIST) -> str:
    for ext in extension_list:
        if os.path.isfile(tmp:=candidate+ext):
            return tmp
    return ''


def load(path:str)->[dict,list]:
    with open(path, 'r') as f:
        return yaml.load(f)