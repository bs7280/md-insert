#!/usr/bin/env python

"""
Pandoc filter to convert all regular text to uppercase.
Code, link URLs, etc. are not affected.

taken from https://github.com/jgm/pandocfilters
"""
from readline import insert_text
import subprocess
from mdinsert.parser import Parser

from functools import reduce  # forward compatibility for Python 3
import operator

import json
import sys


import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Argparse TODO
    # allow passing of file name
    # insert hierarchy
    # TODO add schema command
    parser.add_argument('--schema')
    output_group = parser.add_argument_group('output arguments')
    output_group.add_argument('--ast', '-a', action='store_true', help='return pandoc json ast')
    output_group.add_argument('--markdown', '-m', action='store_true', help='return as markdown')
    output_group.add_argument('--tree', '-r', action='store_true', help='display tree of json')
   
    # TODO add -s / --source command instead of a pipe
    input_group = parser.add_argument_group('input args')
    input_group.add_argument('--pipe', '-p', action='store_true', help='get json from pipe')
    input_group.add_argument('--insert', '-i', dest='insert_schema', help="schema pattern of where to insert new content")
    input_group.add_argument('--type', '-t', dest='input_type', choices=['ast', 'md'], default='md')
    input_group.add_argument('--fname', '-f', dest='fname', help='filename to parse')

    args = parser.parse_args()

    if args.fname:
        source_file = json.loads(subprocess.check_output(
            ["pandoc", "-s", args.fname, "-t", "json", "-f", "gfm"]))
            
    # append sources
    if args.pipe:
        if args.input_type=='md':
            pandoc_ast = subprocess.check_output(
                ["pandoc", "-t", "json", "-f", "gfm"], stdin=sys.stdin)
            extra_str = json.loads(pandoc_ast)
            if len(extra_str.get('blocks', [])) == 0:
                raise ValueError("Piped data was empty or invalid markdown")
        elif args.input_type=='ast':
            lines = sys.stdin.readlines()
            extra_str = json.loads('\n'.join(lines))
        # needed for using pdb
        sys.stdin = open('/dev/tty')
    else:
        raise NotImplementedError("only pipes supported for append markdown")

    p = Parser()
    # Base Note
    tree = p.parse_ast(source_file)

    # Insert note
    new_note_tree = p.parse_ast(extra_str)

    if args.insert_schema:
        # reference nested dictionary via an array of keys
        # https://stackoverflow.com/a/14692747
        # split schema str to list of keys
        key_list = args.insert_schema.split('.')
        # Get a nested dict item via a list of keys
        schema_node = reduce(operator.getitem, key_list, tree.mapper)
        # p.insert_tree(tree.mapper['test-heading'], new_note_tree)
        p.insert_tree(schema_node, new_note_tree)

    blocks = p.flatten_tree(tree)
    if args.tree == True:
        print(p.tree_str(blocks))
    elif args.ast == True:
        # TODO fix this?? why do I need to pass the source file
        # Answer to above: for frontmatter / pandoc meta data
        print(json.dumps(p.pandoc_json(source_file, blocks)))
    elif args.markdown == True:
        ast = json.dumps(p.pandoc_json(source_file, blocks))
        s = subprocess.check_output(
            [ "pandoc", "-f", "json", "-t", "gfm", "-s"],
            universal_newlines=True,
            input=ast)

        print(s)