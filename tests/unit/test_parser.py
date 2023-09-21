import pytest
import parser
import pandoc
from subprocess import Popen, PIPE, STDOUT
import json
import subprocess


test_stub = """
# Lightgbm dask
allow multi node training
"""

test_list = """
# some list

-   item-one asdasdasdads asd asd ads
-   item-foo
-   item2:
    -   sub1
    -   sub2
    -   baz
        -   one
        -   two
-   item-bar
"""


class TestParser:

    def test_parser(self):
        ast = parser.Parser.parse_markdown(test_stub)
        p = parser.Parser()
        tree = p.parse_ast(ast)

        assert type(tree) == parser.RootNode
        assert len(tree.children) == 1
        assert type(tree.children[0]) == parser.HeaderNode
        assert tree.children[0].level == 1
        assert len(tree.children[0].children) == 1
        assert type(tree.children[0].children[0]) == parser.TreeNode
        assert tree.children[0].children[0].level == 2

    def test_lists(self):
        ast = parser.Parser.parse_markdown(test_list)
        p = parser.Parser()
        tree = p.parse_ast(ast)

        # print(json.dumps(tree.children[0].children[0].ast, indent=1))
        print(tree.describe_as_str())

        print("-------")

        # Convert back to markdown via pandoc
        blocks = p.flatten_tree(tree)
        ast_new = json.dumps(p.pandoc_json(ast, blocks))
        s = subprocess.check_output(
            [ "pandoc", "-f", "json", "-t", "gfm", "-s"],
            universal_newlines=True,
            input=ast_new)
        print(s)

        # TODO fix once I can encode between str / bytes
        # Test if input matches output
        # assert s.strip() == test_list.strip()

        # Another idea for better testing - preproces source 
        # markdown to / from AST to get perfect output matching
        
        # p tree[0][0][0]
        tree[0][0].insert_new_list_node("test extra str")

        blocks = p.flatten_tree(tree)
        ast_new = json.dumps(p.pandoc_json(ast, blocks))
        s_new = subprocess.check_output(
            [ "pandoc", "-f", "json", "-t", "gfm", "-s"],
            universal_newlines=True,
            input=ast_new)

        print(s_new)

        breakpoint()