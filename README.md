# Language documentation script collection
This is a collection of scripts for common language documentation workflows.
Download a [ZIP](https://github.com/fmatter/langdoc-script-collection/archive/refs/heads/main.zip) from or clone the repository:

```
git clone https://github.com/fmatter/langdoc-script-collection
```
(If you do not have Git installed, install it.)

See the documentation for individual scripts for usage instructions.
It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) to install necessary packages.

## Contribute a new script
To add a script to the collection, [fork the github repository](https://github.com/fmatter/langdoc-script-collection/fork), use a [virtual environment](https://docs.python.org/3/library/venv.html) to `pip install -r requirements.txt`, and add the following files to your fork:

1. a `my_script.py` (or other suffix) file, ideally with:
    * name and contact info
    * comments where necessary
    * a license
2. a `docs/scripts/my_script.md` file with least:
    * basic setup and usage instructions
    * tags (check mkdocs.yaml and add if necessary)
    * requirements

Look at existing scripts and their documentation to compare 
Run `mkdocs serve` and visit [`localhost:8000`](http://localhost:8000).
Finally, create a pull request.

## Other software
* [cldflex](https://github.com/fmatter/cldflex/)
* [flexpy](https://github.com/Kuhron/flexpy)
* ...