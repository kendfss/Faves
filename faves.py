import sublime_plugin, sublime, sublime_api

from itertools import chain
from collections import OrderedDict
from functools import lru_cache
import os, re, json



#####   DEBUG   #####
#####   DEBUG   #####
#####   DEBUG   #####
#####   DEBUG   #####
import inspect
show = lambda name, enum=True: ([print("%r \t %r" % (i, e) if enum else e) for i, e in enumerate(name)], None)[-1]
getsource = lambda name, enum=False: (show(inspect.getsource(name).splitlines(), enum), None)[-1]
scan = lambda term, object=sublime: (show(filter(lambda x: term in x.lower(), dir(object))), None)[-1]
#####   /DEBUG   #####
#####   /DEBUG   #####
#####   /DEBUG   #####
#####   /DEBUG   #####



"""
json snippets

open all
dynamic expansions (like the defaults below)


sections
    adherence
    path
"""


here, this = os.path.split(__file__)
log_file_path = os.path.join(here, 'locations.json')
max_length = 20
print(log_file_path)
print(os.path.exists(log_file_path))
def load():
    with open(log_file_path, 'r') as fob:
        return json.load(fob)

def save(parseling):
    with open(log_file_path, 'w') as fob:
        json.dump(parseling, fob, indent='    ', sort_keys=True, skipkeys=True)
    return parseling

def keybindings_path():
    if sys.platform == 'aix':
        platform = "AIX"
    elif sys.platform == 'linux':
        platform = "Linux"
    elif sys.platform == 'win32':
        platform = "Windows"
    elif sys.platform == 'cygwin':
        platform = "Cygwin"
    elif sys.platform == 'darwin':
        platform = "OSX"
    return "$packages/User/Default ({}).sublime-keymap".format(platform)


expansions = {
    "$locations": log_file_path,
    # "$data": "$user\\AppData\\Roaming\\Sublime Text 3",
    "$data": os.path.dirname(sublime.packages_path()),
    # "$packages": sublime.packages_path(),
    "$packages": "$data/Packages",
    # "$installs": sublime.installed_packages_path(),
    "$installs": "$data/Installed Packages",
    "$bin": os.path.dirname(sublime.executable_path()),
    # "$all": "*",
    # "*": "$all",
    "$user": os.path.expanduser('~'),
} if not os.path.exists(log_file_path) else load()['expansions']

if not os.path.exists(log_file_path):
    save({'expansions': expansions, "locations":{}})
print(os.path.exists(log_file_path))
print(expansions['$data'])
print(expansions['$bin'])

def scrape_locations():
    if not os.path.exists(log_file_path):
        log = {
            'expansions': expansions,
            'favourites': {i: key for i, key in enumerate(expansions.keys())},
        }
        save(log)
    return validate_cfg(load()['favourites'])

def is_relative(path):
    base = '../'
    mould = '^({})+(.)*$'
    posix = mould.format(re.escape(base))
    nt = mould.format(re.escape(base.replace('/', '\\')))
    pattern = '|'.join((posix, nt))
    scanner = re.compile(pattern)
    return scanner.match(path)

def count_levels(path):
    depth = 0
    while is_relative(path):
        depth += 1
        path = path[3:]
    return depth, path

def absolute_path(path):
    depth, path = count_levels(path)
    path = expand(path)
    while depth:
        path = os.path.dirname(path)
        depth -= 1
    return path

def splitall(splitters, target, empties=False):
    splitters = iter(splitters)
    result = target.split(next(splitters))
    for splitter in splitters:
        result = list(chain.from_iterable(i.split(splitter) for i in result))
    yield from (filter(None, result), result)[empties]


def is_source_code(location):
    # revisit with a try/except
    name = "(\w+((\.?)\w+))+"
    pattern = re.compile('^{}\(\)$'.format(name))
    return bool(pattern.match(location))

def get_index(path):
    cfg = load()['favourites']
    for k, v in cfg.items():
        if v == path:
            return k

def expand(path):
    passed = []
    root, *rest = splitall('\/', path)
    rest = list(rest)
    
    while root in expansions.keys():
        if root in passed:
            index = get_index(path)
            msg = 'Circular reference in locations file!\nindex:\t{}\npath:\t{}'.format(index, path)
            sublime.error_message(msg)
            raise CircularReferenceError(msg)
        else:
            passed.append(root)

        root, *r2 = splitall('\/', expansions[root])
        rest = list(r2) + rest 

    parts = list(splitall('\/', root)) + list(rest)
    parts[0] += (':', '')[parts[0].endswith(':')] if os.name=='nt' else ''
    return ('/', '')[os.name=='nt'] + os.sep.join(parts)

def posix_path(path):
    parts = splitall('\/:', expand(path))
    return '/' + '/'.join(parts)

def nt_path(path):
    parts = list(splitall('\/', expand(path)))
    parts[0] += (':', '')[parts[0].endswith(':')]
    return '\\'.join(parts)

def local_path(path):
    if os.name == 'nt':
        return nt_path(path)
    return posix_path(path)


def validate_cfg(parseling):
    assert all(isinstance(key, str) for key in parseling.keys()), 'Some shortcut keys could not be parsed'
    assert all(isinstance(value, (str, list, dict)) for value in parseling.values()), 'Some shortcut values could not be parsed'
    return parseling

def isfile(item):
    if (os.path.isdir(item) 
    or item in expansions.keys()): 
    # or is_source_code(item)):
        return False
    return True


def parse_item(item):
    if item in ('*', '$all'):
        return '*'
    if isinstance(item, str):
        return {
            "paths": [item],
        }
    elif isinstance(item, list):
        return {
            "paths": item,
        }
    elif isinstance(item, dict):
        return item

def validate_index(index, cfg):
    return any(int(index) <= i for i in map(int, cfg.keys()))



class CircularReferenceError(Exception):
    pass

class PathChoiceHandler(sublime_plugin.TextInputHandler):
    def __init__(self, view):
        self.view = view

    def name(self):
        return "text"

    def placeholder(self):
        return "indices"

    def preview(self, text):
        self.text = text
        return ("Characters: {}, Words: {},\nDepth: {}"
            .format(
                len(text), len(text.split()), len(tuple(splitall('\/', text)))
            )
        )


# 0,1 6, 13
class FavouritesCommand(sublime_plugin.TextCommand):
    @staticmethod
    def pop(path, window):
        kind = ("dir", "file")[isfile(path)]
        window.run_command("open_{}".format(kind), {kind: path})

    def get_window(self, new_window):
        window = int(new_window)
        if window == -1:
            return sublime.active_window()
        elif window == 0:
            return self.view.window()
            # return self.window
        elif window == 1:
            sublime.run_command('new_window')
            return sublime.active_window()

    def run(self, edit, text):
        print('\n' * 20)
        
        cfg = scrape_locations()
        if text:
            indices = list(map(str.strip, splitall(', ', text)))
            alls = '* $all all a'.split()
            do_all = any(bang in indices for bang in alls)
            [indices.remove(bang) for bang in alls if bang in indices]
            
            base = indices if not do_all else filter(lambda: i not in indices, cfg.keys())

            for index in base:
                if validate_index(index, cfg):
                    item = parse_item(cfg[index])
                    
                    new_window = item.get('new_window', False)
                    window = self.get_window(new_window)

                    for element in item['paths']:
                        try:
                            path = absolute_path(element)
                            print(
                                ("opening dir: {}", "opening file: {}")[isfile(path)].format(path)
                            )
                        except CircularReferenceError:
                            continue
                        self.pop(path, window)
        else:
            self.pop(expansions['$locations'])
    def input(self, args):
        return PathChoiceHandler(self.view)
