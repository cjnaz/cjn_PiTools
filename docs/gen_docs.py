#!/usr/bin/env python3
"""Extract doc strings from source module(s) and build the module specific READMEs

Run this with cdw = docs directory
"""

#==========================================================
#
#  Chris Nelson, 2024 - 2026
#
#==========================================================

import pathlib
import re
import ast

MODULES_FILE = pathlib.Path('modules_list.txt')
# modules_list.txt file example
'''
[
    {'outfile':'../DS18B20.md',     'head':'./DS18B20_head.md',         'source':'../src/cjn_PiTools/DS18B20.py'},
    {'outfile':'../PCA9548.md',     'head':'./PCA9548_head.md',         'source':'../src/cjn_PiTools/PCA9548.py'},
]
'''

COMMENT_BLOCK = re.compile(r'"""\s+##\s([\s\S]+?)(?:""")')
# Doc string format example:
'''
def snd_notif(subj="Notification message", msg="", to="NotifList", log=False):
    """
## snd_notif (subj="Notification message, msg="", to="NotifList", log=False) - Send a text message using info from the config file
(...documentation...)
    """
'''


#----------------------------------------------------------------------------------------
def main():

    modules_list = MODULES_FILE.read_text()
    modules = ast.literal_eval(modules_list)

    for module in modules:
        print (f"Processing {module['outfile']}")
        links       = build_links_list(module['source'])
        docstrings  = extract_docstrings(module['source'])

        with pathlib.Path(module['outfile']).open('w') as ofile:
            ofile.write(pathlib.Path(module['head']).read_text())

            ofile.write(r"""

<a id="links"></a>
         
<br>

---

# Links to classes, methods, and functions

""")
            ofile.write(links)

            ofile.write(r"""

""")
            ofile.write(docstrings)


def build_links_list(source):

    all = pathlib.Path(source).read_text()
    # Build the links list
    links = ''
    for block in COMMENT_BLOCK.finditer(all):
        link_name = get_linkname(block)
        links += f"- [{link_name}](#{link_name})\n"
    return links

        # link = funcline.replace(" ", "-").lower()
        # deleted = ":()\n,.=\"\'"
        # for char in deleted:
        #     link = link.replace(char, "")
        # links += f"- [{link_name}](#{link})\n"


#----------------------------------------------------------------------------------------
def extract_docstrings(source):
    xx = ''
    all = pathlib.Path(source).read_text()

    for block in COMMENT_BLOCK.finditer(all):
        link_name = get_linkname(block)
        print (f"    Processing {link_name}")
        xx += "\n<br/>\n\n"
        xx += f'<a id="{link_name}"></a>\n\n'
        xx += "---\n\n"
        xx += "# " + block.group(1)

    return xx


#----------------------------------------------------------------------------------------
def get_linkname(block):
    funcline = block.group(1).split('\n')[0]
    return funcline.replace("Class ", "").split(maxsplit=1)[0] #.lower()



if __name__ == '__main__':
    main()


