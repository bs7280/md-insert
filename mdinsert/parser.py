from email.header import Header
from logging import root
from multiprocessing.sharedctypes import Value
from tkinter.tix import Tree
from subprocess import Popen, PIPE, STDOUT
import json


class TreeNode:

    def __init__(self, block_type, contents, level, parent):
        self.t = block_type
        self.content = contents
        self.level = level
        self.parent = parent
        self.children = []

    @property
    def description(self):
        return "todo"

    @property
    def ast(self):
        return {
            't': self.t,
            'c': self.content
        }
    
    def update_tree_levels(self, new_level):
        """Mutator - update self.level based on a base level (0 for root node, 1 for h1)
        recursively updates children

        default should be 0, meaning this is its own tree
        if merging into a h1 node of a note, then this should be h2 and lower for children

        Args:
            base_level (int): level of tree node to be merged to 
        """

        #raise NotImplementedError("TODO") # Need to think of how to make this work both ways
        # update such that recursive calls do a base_level + 1, and the initial value is the
        # new level of the starting tree

        self.level = new_level

        if type(self) == HeaderNode:
            # Im not sure if this is the best place for this logic?
            if self.content[0] != self.level:
                self.content[0] = self.level

        for child in self.children:
            child.update_tree_levels(new_level=self.level + 1)

    def describe_as_str(self, top_level=0):
        out_str = "  " * (self.level - top_level) + f"{str(self)}\n"
        return out_str

    def print(self):
        print(self.describe_as_str(top_level=self.level))

    def __repr__(self):
        #if False:
        #    parent_str = None if self.parent is None else self.parent.describe_as_str()
        #    return f"TreeNode(t={self.t}, parent={parent_str})"
        
        return f"TreeNode(t={self.t} - l{self.level})"

class RootNode(TreeNode):
    def __init__(self):
        self.t = None
        self.content = None
        self.level = 0
        self.children = []
        self.mapper = {}
        self.parent = None

    def append(self, node):
        self.children.append(node)

        if type(node) == HeaderNode:
            self[node.identifier] = node

    def describe_as_str(self, top_level=0):
        out_str = super().describe_as_str(top_level=top_level) #"  "*self.level + f"{str(self)}\n"
        for child in self.children:
            out_str = out_str + child.describe_as_str(top_level=top_level)
        return out_str

    def __repr__(self):
        return "RootNode()"

    def __setitem__(self, key, node):
        if key not in self.mapper:
            self.mapper[key] = node
        else:
            raise KeyError(f"key {key} already exists in {self} node")

    def __getitem__(self, key):
        if type(key) == int:
            return self.children[key]
        else:
            return self.mapper[key]
        #if self.key in self.mapper.keys()
    
    def __contains__(self, key):
        return key in self.mapper

class HeaderNode(RootNode):
    def __init__(self, block_type, contents, level, parent):
        self.t = block_type
        self.content = contents
        self.level = level
        self.children = []
        self.mapper = {}
        self.parent = parent

    @property
    def identifier(self):
        return self.content[1][0]

    def __repr__(self):
        return f"HeaderNode({self.identifier} - H{self.content[0]} L{self.level})"

class ListNode(TreeNode):

    def __repr__(self):
        return f"ListNode(t={self.t} - l{self.level})"

    def describe_as_str(self, top_level=0):
        out_str = super().describe_as_str(top_level=top_level) #"  "*self.level + f"{str(self)}\n"
        for child in self.children:
            out_str = out_str + child.describe_as_str(top_level=top_level)
        return out_str

    @property
    def ast(self):
        response_ast = [super().ast]

        if len(self.children) > 0:
            response_ast = response_ast + [{
                't': "BulletList",
                'c': [x.ast for x in self.children]
            }]
        return response_ast


# TODO - special case of AST when this has a bulleted list as a child


class BulletedList(RootNode):
    """format of AST:
    ```
    {
        "t": "BulletList",
        "c": [# list of lists, each sublist is a list item
            [ # first list item
                {some text item}
            ],
            [ # second list item
                {other text item}
            ], 
            [# third item, bulleted list!!
                {text item for text before BL object},
                {'t': BulletList, "c": [...]}
            ]
        ]
    }
    ```     

    problems:
    1. No identifier for BulletLists
        * Solution: 
            * combine str types of first item with '-'
            * remove special chars
    1. AST object is nested unlike everything else implemented so far
        * unpack as part of Parer.parse_tree() 
        * *or* have ListNode constructor process entire list recusively?
    
    takeaways:
    * all list items contents (`'c': [...]`) are lists, 
        * but have to 
            * check for existance of BulletLlists 

    # What data structure to use for parsed bulleted lists?
    items = [TreeNode(block_type, contents), ..., ListNode()]

    """
    
    def __init__(self, block_type, contents, level, parent):
        # Same as header
        self.t = block_type
        self.content = None
        self.level = level
        self.mapper = {}
        self.parent = parent
        self.children = []

        # Set identifier by first item, used for overall list (not per item)
        # TODO - make this use first n words (Currently just takes the first item)
        # may be worth not doing (positional only!)
        #self.identifier = '-'.join([x.get('c') for x in contents[0][0]['c'] if x.get('t') == 'Str'])


        self.children = self.parse_bulleted_list(contents, level)

    def parse_bulleted_list(self, contents, level):
        # go through self.contents to populate self.children
        out = []
        for c in contents:
            if len(c) == 2:
                # nested list
                item_node = c[0]
                item_bl = c[1]

                list_node = ListNode(
                    block_type=item_node['t'],
                    contents=item_node['c'],
                    level=level + 1,
                    parent=self)

                #bl_node = BulletedList(
                #    block_type=item_bl['t'],
                #    contents=item_bl['c'],
                #    level=list_node.level + 1, 
                #    parent=list_node)

                
                children = self.parse_bulleted_list(item_bl['c'], level + 1)
                list_node.children = children
                out.append(list_node)
            elif len(c) == 1:
                item = c[0]
                node = ListNode(
                    block_type=item['t'],
                    contents=item['c'],
                    level=level + 1,
                    parent=self)
                out.append(node)
            else:
                raise ValueError("Unexpected Parse situation")
    
        return out

    def insert_new_list_node(self, source_str):
        """Create / Append a new list node from raw str

        I may split this logic later, but this doc str serves as a place
        to organize notes and info related to this

        ListNode(
            block_type=item_node['t'],
            contents=item_node['c'],
            level=level + 1,
            parent=self)

        Args:
            source_str (str): raw string to be converted to md and inserted as a list ndoe
        """

        # TODO validate that this isn't too complicated (e.g. a list is treated different than raw str)
        ast = Parser.parse_markdown(source_str)['blocks']

        if len(ast) > 1:
            raise NotImplementedError("Markdown too complicated")
        else:
            ast = ast[0]

        # HACK (?) otherwise output is weird
        # default parse of raw text is a paragraph
        if ast['t'] == 'Para':
            ast['t'] = 'Plain'

        new_node = ListNode(
            block_type=ast['t'],
            contents=ast['c'],
            level=self.level + 1,
            parent=self)

        self.children.append(new_node) 

    def __repr__(self):
        return f"BulletedList(L{self.level})"

    
    @property
    def ast(self):
        return {
            't': self.t,
            'c': [x.ast for x in self.children]
        }

class Parser:

    @classmethod
    def parse_markdown(cls, md_str):
        """Wrapper around self.parse_markdown, will call pandoc to 
        convert raw markdown to pandoc ast

        Args:
            md_str (str): raw markdown str to turn to ast tree
        """

        # Passing to pipe STDIN requires str -> bytes
        bytes_str = md_str.encode('utf-8')

        p = Popen(
            ["pandoc", "-t", "json", "-f", "gfm"],
            stdout=PIPE,
            stdin=PIPE,
            stderr=STDOUT)
        grep_stdout = p.communicate(input=bytes_str)[0]
        return json.loads(grep_stdout.decode())

    @classmethod
    def convert_ast_to_markdown(cls):
        pass # TODO

    def parse_ast(self, ast_str):
        tree_root = RootNode()

        tree_level = 0
        target_node = tree_root


        def find_new_parent(parent_node, header_level):
            # traverse up recursively until level==header_level
            # return parent of that node
            # TODO - think through the edge case in the else block
            #   I think its when you go from # to ### to ##, need to rework tree
            if parent_node is None:
                return parent_node
            elif parent_node.level > header_level:
                # Go higher
                return find_new_parent(parent_node.parent, header_level)
            elif parent_node.level == header_level:
                return parent_node.parent
            else:
                raise ValueError("Unexpected control flow when finding new parent")

        for obj in ast_str['blocks']:
            block_type = obj['t']
            block_contents = obj['c']

            if block_type == 'Header':
                header_level = block_contents[0]
                if tree_level < header_level: 
                    # deeper into tree
                    # add this object to target_node.children
                    # set parent of this object to target_node
                    # change tree_level 
                    new_obj = HeaderNode(
                        block_type=block_type,
                        contents=block_contents,
                        level=header_level,
                        parent=target_node
                        )

                    # target_node['children'].append(new_obj)
                    target_node.append(new_obj)
                    target_node = new_obj
                    tree_level = header_level

                elif tree_level == header_level:

                    new_obj = HeaderNode(
                        block_type=block_type,
                        contents=block_contents,
                        level=header_level,
                        parent=target_node # TODO do target_node.parent, I think there was/is a bug but its self correcting for now
                        )  

                    target_node.parent.append(new_obj)
                    target_node = new_obj
                    tree_level = header_level
                else:
                    # this block is higher up the tree than where we are now
                    target_node = find_new_parent(target_node, header_level)

                    new_obj = HeaderNode(
                        block_type=block_type,
                        contents=block_contents,
                        level=header_level,
                        parent=target_node
                        )


                    target_node.append(new_obj)
                    target_node = new_obj
                    tree_level = header_level
            elif block_type == 'BulletList':
                new_obj = BulletedList(
                        block_type=block_type,
                        contents=block_contents,
                        level=tree_level + 1,
                        parent=target_node)
                target_node.append(new_obj)
            else:
                # No hierarchy change, append to target's children list

                new_obj = TreeNode(
                    block_type=block_type,
                    contents=block_contents,
                    level=header_level + 1,
                    parent=target_node
                )
                target_node.append(new_obj)

        return tree_root

    def flatten_tree(self, tree_root):
        """ Takes a parsed tree and flattens as a list of blocks
        each list item is a dict with 
            * 'json-ast' being the pandoc type json object
            * 'str' wich is the str representation with tabs according to tree depth
        """
        def walk(tree):
            blocks = []

            if type(tree) != RootNode:
                blocks.append({
                    'json-ast': tree.ast,
                    'str': f"{'  '*(tree.level - 1)}{str(tree)}\n"
                })

            if type(tree) != BulletedList and type(tree) != ListNode:
                for node in tree.children:
                    blocks = blocks + walk(node)

            return blocks

        blocks = walk(tree_root)
        return blocks

    def tree_str(self, blocks):
        return "".join([x['str'] for x in blocks])

    def pandoc_json(self, input_ast, blocks):
        out = input_ast.copy()
        out['blocks'] = [x['json-ast'] for x in blocks]
        return out

    def insert_tree(self, parent_node, child_tree):
        child_tree.update_tree_levels(new_level=parent_node.level)

        if type(child_tree) == RootNode:
            for node in child_tree.children:
                node.parent = parent_node
                parent_node.children.append(node)
        else:
            raise NotImplementedError("Have not encountered this yet")

        #return parent_node