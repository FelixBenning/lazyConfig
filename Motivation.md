
# How lazyConfig can help

## 1. Dealing with overlapping Configurations

A very nice pattern for overlapping configuration is the **`Default/Override
pattern`**. A real life example for this is the editor [Visual Studio
Code](https://code.visualstudio.com/docs/getstarted/settings), where you have
a small user configuration JSON which overrides the default JSON
configuration.

You might have this configuration in a certain location relative to your
program, but ideally you set the configuration directory with a environment
variable. 

If your app is developed for a docker container you can use .env files to set
default values for these environment variables. It becomes trivial to switch
between configurations by setting the environment variable to a different
location.

Now you could implement such an override pattern yourself. Or you could use
`lazyConfig`.

## 2. Dealing with multi-file configuration

There are multiple reasons why you might want to split up configuration into
multiple files. One reason is, that you have configuration for different 
components. You might, as an example, have an elasticsearch database with
multiple indices. Since the [index creation
API](https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-create-index.html)
accepts settings as a JSON body in a HTTP requests, it might make sense to
store the settings of different indices in different JSON files. Then you might
have [pipelines](https://www.elastic.co/guide/en/elasticsearch/reference/current/pipeline.html)
for these indices or custom [synonyms filter](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-tokenfilter.html). And suddenly you have a directory
full of configuration files. And this is just for the database!

In the worst case, you are feeding your database these configuration files
manually with `curl`, which means that every deployment of your database has a
considerable share of manual labor. In an improved scenario you hardcode the
file locations into a script which feeds your fresh database. In the best case
you put all the index files into an `indices` folder, all the pipelines into a
`pipelines` folder, etc. and loop over the files in these folders. 

So your directory structure now looks something like this

```
config
    elasticsearch
        indices
            index1.json
            index2.json
            ...
        pipelines
            ...
        filters
            ...
    app
        ...
```

Now you could just have a `index feeding script` which uses an environment
variable to find the index folder and feeds the database all the indices, and 
a `pipeline feeding script` with an environment variable which does the same
for pipelines, etc. Now you have a lot of environment variables all of which
you have to change if you move the entire folder. Okay so maybe it is better to
have relative paths and append them to a folder path. This is less birttle but
now you still have a ton of environment variables. 

Well, so what if you do away with all these relative paths completely and
simply recursively load your entire configuration into a nested dictionary? I
mean directories are basically just dictionaries right? Accessing the
configuration of a certain component is then simply dereferencing
its key in a nested dictionary where the key is the name of the folder.

This has the added benefit that it nudges the user to do proper [**dependency
injection**](https://en.wikipedia.org/wiki/Dependency_injection). Your
database configurator needs the database configuration? No problem, you just
pass this part of your nested `config` dictionary to the
configurator from the `main`/`entrypoint` function.

You could implement something like that. Or you could use this module.

## 3. That sounds nice, but...

...loading my entire configuration into a dictionary **wastes too much
memory.** Especially since much of that configuration is almost never used.
Like that
database configuration you mentioned? You only have to use that once when
starting or resetting the database. That happens almost never. My app should
not waste so much memory for nothing.

Now we could go back and load configuration for different components as needed.
This would make our dependency injection a little bit more murky but at least
we are saving memory, right? 

Or we could try to be clever and avoid loading the entire configuration into
memory but still pretend we did, and act like a config dictionary.

How so? [Magic Methods](https://www.tutorialsteacher.com/python/magic-methods-in-python).
In particular the `__getitem__()` method. This method allows us to define what
happens if I do `a[key]` on my object `a`. In particular this allows us to
emulate the behavior of a dict, without *being* a dict. In our case we would
read and return a particular file when accessed, instead of loading it into a
dictionary from the get go. This behavior is often called `lazy`.

Now you could implement something like this yourself. Or you could use this
module.

## 4. So many Strings!

Now this idea of yours is nice and all, but now I have to type long dictionary
access chains like this

```python
config['elasticsearch']['indices']['index1'][...]
```

this is really cumbersome, and my
[linter](https://en.wikipedia.org/wiki/Lint_(software)) also does not like
all the hard coded string literals. 

Well first of all you should pass
configuration components to your functions/modules dealing with that stuff.
And your main function should not reach so deep into the configuration either
and delegate details. For this reason long access chains might indicate a
problem with your architecture.

But yes, typing `['']` is annoying, and typing `.` is so much easier. And since
our access operation is a custom design anyway, we might as well go the extra
step and define `__getattr__`. Which is why you access your `lazyConfig`
configuration with

```python
config.elasticsearch.indices.index1...
```

## 5. Bonus Feature

`dir()` is one of the functions used by a lot of interactive terminals to
generate [intelligent code completion](https://en.wikipedia.org/wiki/Intelligent_code_completion).
And calling `dir(object)` is equivalent to calling `object.__dir__()`, which is
another magic method you can implement. So sometimes your configuration options
will be suggested to you. But as static code analysers want to avoid executing
code for [security
reasons](https://github.com/davidhalter/jedi/issues/997#issuecomment-405047831)
and method chaining does not seem to chain these calls to `dir()` (even in
interactive terminals), this does seem to be a relatively rare bonus luxury.