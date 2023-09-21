# Markdown inserter

## TODO
* change header level when inserting trees
* start making some unit tests
* allow passing of fname and just calling `sys.POpen([args])`
  * how to grab stdout? need internet

## Usage

### via pipe to filter back to markdown
`pandoc -s test_data/test.md -t json -f gfm | python main.py -p -a | pandoc -f json -t gfm -s`

### Append to file via pipe and output as markdown
`pandoc -s test_data/test_stub_todo_item.md -t json -f gfm | python main.py --fname test_data/test_todo.md -m -i title.todo -p`

### Display tree
`pandoc -s test_data/test.md -t json -f gfm | python main.py -p -t`

### Pipe markdown into new file
`cat test_data/test_stub_todo_item.md | python main.py --fname test_data/test_todo.md -m -i title.todo -p`
details:
* `-i title.todo` is the destination identifier to inject new markdown
* `--fname test_data/test_todo.md` is the path to the existing / destination note to modify (an empty todo list in this case)
* `-m` specifies output format as markdown

Before: 
```md
---
title: test
---

# Title
description

## TODO 

foobar
```

Input:
```md
# Lightgbm dask
allow multi node training
```

After: 
```md
---
title: test
---

# Title

description

## TODO

foobar

### Lightgbm dask

allow multi node training
```

note - use this to pipe
`pandoc -s test_data/test_stub_todo_item.md -t json -f gfm | python main.py --fname test_data/test_todo.md -m -i title.todo -p`

## Tests / edge cases todo
* gitlab style markdown, with text leading bulleted list
    * should the text before be part the title of the list?

### CLI design

`cat new_markdown.md | python main.py -f dest_fname.md -i schema_identifier -s`
* `-s` for stdin / pipe for NEW content
* `-f <fname>` for existing file

## Identifer / lookup 
currently using `-i <term>` arg you can use a term like `title.todo` to access the second level

Hopefully something exists, if not...

Ideas:
* `foo.*.bar` means any number of levels to get from foo to bar
* `Htodo+` means any chars after header starting with todo
* use `H` or `L` for header or list

## TODO
* Finish bulleted lists? Or Finish a basic useable tool