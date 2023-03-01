# uct.py
Python module for parsing and working with UCT-DEF grid models. Contains classes for grid elements:
* **Node** (##N)
* **Line** (##L)
* **Transformer** (##T)
* **Regulation** (##R)
* **Parameter** (##TT)
* **Schedule** (##E)

Additional classes:
* **Grid** - main class to contain the whole grid
* **Area** - groups elements by their area defined by node area or node they connect to.  
* **Element** - basic class with methods common for all types of grid elements

For UCT-DEF directives (##) definition visit following link:\
[https://cimug.ucaiug.org/Groups/Model%20Exchange/UCTE-format.pdf](https://cimug.ucaiug.org/Groups/Model%20Exchange/UCTE-format.pdf)

---
## Initialization
To use the module import it to your script. The best way is to import just the *Grid* class:
```
from uct import Grid
```

To expose all classes, functions and variables in the module use:
```
from uct import *
```
Note: To import the module in form of **uct.py** file must be located in a folder included in the pythons [sys.path](https://docs.python.org/3/library/sys.html).\
If your folder is not included, append the `sys.path` and then import the module:
```
import sys
sys.path.append(r"c:\My_Folder_With_Uct_Module")
from uct import Grid
```