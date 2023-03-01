:raised_hands:
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
<br/>

## Initialization
To use the module import it to your script. The best way is to import just the ***Grid*** class:
```
from uct import Grid
```

To expose all classes, functions and variables in the module use:
```
from uct import *
```
*Note*: To import the module in form of ***uct.py*** file it has to be located in a folder included in the python's [sys.path](https://docs.python.org/3/library/sys.html).\
If your folder is not included, append the `sys.path` and then import the module:
```
import sys
sys.path.append(r"c:\My_Folder_With_Uct_Module")
from uct import Grid
```
To load uct model from a ****.uct*** file set a variable to a Grid class with a file path as an attribute:
```
model_object = Grid(r"c:\Folder_With_Uct_Files\Uct_file.uct")
```
If you want to check your grid, print the instance of the ***Grid*** object which will return number of loaded grid elements:
```
>>> print(model_object)
Grid(Nodes: 19600; Lines: 23868; Transformers: 3993; Regulations: 2845; Parameters: 2; Schedules: 3)
```
---
<br/>

## Classes
:notebook_with_decorative_cover:
### `Grid(uct_file_path)`
The main class that contains all grid elements read from the uct file.\
*uct_file_path* has to conform to the UCT naming or else an exception is raised.
#### Attributes:
- `Grid.file -> str` - uct file path passed during class initialization is stored here.
- `Grid.filename -> Sub` - object containing parsed uct file name parts as attributes

| Attribute | Description | Accepted format/values |
|:----------| ---------------|:-----|
| `.year -> str` | year of the scenario | YYYY |
| `.month -> str` | month of the scenario | MM |
| `.day -> str` | day of the scenario | DD |
| `.hour -> str` | hour of the scenario | HH |
| `.minute -> str` | minute of the scenario | MM |
| `.type -> str` | uct process type |FO, SN, RE, LR, 00 - 24 |
| `.week_day -> str` | week day index | 1 - 7
| `.area -> str`| area code from uct filename | keys of `countries` dictionary|
|`.version -> str` | uct file version | 0 - 9

:notebook_with_decorative_cover:
### `Sub(**kwargs)`
Helper class to create an arbitrary object based on passed keyword arguments.

Example:
```
>> object = Sub(name = "John", surname = "Wick")
>>> object
Sub(name='John', surname='Wick')
>>> object.name
'John'
>>> object.surname
'Wick'
```