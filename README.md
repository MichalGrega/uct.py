:raised_hands:
# uct.py
Python module for parsing and working with UCT-DEF grid models. Contains classes for grid elements:
* [**Node** (##N)](#-node)
* [**Line** (##L)](#-line)
* [**Transformer** (##T)](#-transformer)
* [**Regulation** (##R)](#-regulation)
* [**Parameter** (##TT)](#-parameter)
* [**Schedule** (##E)](#-schedule)

Additional classes:
* **Grid** - main class to contain the whole grid
* **Area** - groups elements by their area defined by node area or node they connect to.  
* **Element** - basic class with methods common for all types of grid elements

For UCT-DEF directives (##) definition visit following link:\
[https://cimug.ucaiug.org/Groups/Model%20Exchange/UCTE-format.pdf](https://cimug.ucaiug.org/Groups/Model%20Exchange/UCTE-format.pdf)


<br/>

## Prerequisites
❗ Module needs [dataclasses](https://pypi.org/project/dataclasses/) installed for Python < 3.6


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
<br/>

## Classes
### 📚 `Grid(uct_file_path)`
The main class that contains all grid elements read from the uct file.\
Base name of the *uct_file_path* has to conform to the UCT naming or else an exception is raised.
#### Attributes: 
▶ `Grid.file -> str` - uct file path passed during class initialization is stored here.\
▶ `Grid.filename -> Sub` - object containing parsed uct file name parts as attributes (accepts only formats/values):
* `.year -> str` - year of the scenario (YYYY)
* `.month -> str`-  month of the scenario (MM)
* `.day -> str` - day of the scenario (DD)
* `.hour -> str` - hour of the scenario (HH)
* `.minute -> str` - minute of the scenario (MM)
* `.type -> str` - uct process type (FO, SN, RE, LR, 00 - 24)
* `.week_day -> str` - week day index (1 - 7)
* `.area -> str` - area code from uct filename (keys of `countries` dictionary)
* `.version -> str` - uct file version (0 - 9)
example:
```
>>> model_object = Grid(r"c:\Folder_With_Uct_Files\Uct_file.uct")
>>> model_object.filename
Sub(area='UX', day='06', hour='06', minute='30', month='02', type='FO', version='2', week_day='1', year='2019')
>>> model_object.filename.year
'2023'
```
▶ `Grid.uct_text_original -> str` - text of the uct file as a whole without any changes.\
▶ `Grid.uct_version -> str` - uct format version identification ( ❕ not file version ❕ )\
▶ `Grid.comments -> list` - list of all comment blocks from uct file. If uct file contain multiple comment blocks directives (##C), list will contain multiple items.\
▶ `Grid.areas -> dict` - dictionary of [Area](#-areaarea_code-str-grid_instance-grid) type objects with area code as key.
```
>>> md.areas
{'ME': Area(ME, Nodes: 52, Lines: 75, Transformers: 12, NP: 224.4877),
'AL': Area(AL, Nodes: 160, Lines: 192, Transformers: 29, NP: 270.2495), ... }
```
▶ `Grid.not_read -> dict` - dictionary of lines from uct file that were not recognized during parsing. Keys are object names corresponding to the element blocks (*Node, Line, Transformer, Regulation, Parameter, Schedule*). Values are lists of strings (text lines from the file). If everything was read correctly, the dictionary is empty. Only keys of not read elements are present.
```
>>> model_object.not_read.keys()
dict_keys(['Node', 'Line', 'Regulation', 'Transformer', 'Parameter', 'Schedule'])
```
▶ `Grid.nodes -> dict` - dictionary of [Node](#-node) type objects organized as *Node.id: Node*.\
▶ `Grid.lines -> dict` - dictionary of [Line](#-line) type objects organized as *Line.id: Line*.\
▶ `Grid.transformers -> dict` - dictionary of [Transformer](#-transformer) type objects organized as *Transformer.id: Transformer*.\
▶ `Grid.regulations -> dict` - dictionary of [Regulation](#-regulation) type objects organized as *Regulation.id: Regulation*.\
▶ `Grid.parameters -> dict` - dictionary of [Parameter](#-parameter) type objects organized as *Parameter.id: Parameter*.\
▶ `Grid.schedules -> dict` - dictionary of [Schedule](#-schedule) type objects organized as *schedule.id: schedule*.\

#### Properties
◼ `Grid.date -> datetime.datetime` - date timestamp created from Grid.filename attributes.\
◼ `Grid.file_basename -> str` - returns basename of the loaded uct file.\

#### Methods
♻ `Grid.uct(trim: bool = False, C: bool = True, N: bool = True, L: bool = True, T: bool = True, E: bool = True) -> str` - creates valid uct text of the Grid object.
* `trim` - if true, tracing spaces are stripped.
* `C`, `N`, `L`, `T`, `E` - if true, directive blocks are exported (C - comments, N - nodes, L - lines, T - transformers including regulations and special parameters, E - schedules).\

♻ `Grid.slack() -> list` - returns a list of all global slack nodes in the `Grid.nodes` i. e. nodes that have `Node.node_type == 3`.

### 📚 `Area(area_code: str, grid_instance: Grid)`
Class that holds several properties that group grid elements by their corresponding area.
* `area_code: str` has to be in the same format that is used in uct ##Z directive: ##Z(area_code).For example ##ZBE.
* `grid_instance: Grid` is a Grid object instance that holds elements to be sorted.

#### Attributes
▶ `Area.code -> str` - area 2 character ISO code of a country to which the area belongs. `area_code` parameter is passed to this attribute.\
▶ `Area.grid -> Grid` - Grid object instance containing elements to be sorted passed down from `grid_instance` parameter.

#### Methods
♻ `Area.nodes() -> dict` - returns dictionary of [Node](#-node) type objects *{Node.id: Node}* that have `Node.area` attribute equal to `Area.code` i. e. nodes belonging to the area.\
♻ `Area.xnodes() -> dict` - returns dictionary of [Node](#-node) type objects *{Node.id: Node}* that have `Node.area` attribute equal to *XX* i. e. X-nodes that are connected to the area by at least one line.\
♻ `Area.slack() -> list` - returns list of slack nodes in `Area.nodes` i. e. nodes that have `Node.note_type == 3`.\
♻ `Area.lines() -> dict` - returns dictionary of [Line](#-line) type objects *{Line.id: Line}* of which at least one node belongs to the area (`Area.code in [Line.node1, Line.node2]`)\
♻ `Area.transformers() -> dict` - returns dictionary of [Transformer](#-transformer) type objects *{Transformer.id: Line}* of which at least one node belongs to the area (`Area.code in [Transformer.node1, Transformer.node2]`)\
♻ `Area.schedules() -> dict` - returns dictionary of [Schedule](#-schedule) type objects *{Schedule.id: Line}* of which at least one country belongs to the area (`Area.code in [Schedule.country1, Schedule.country2]`)\
♻ `Area.np(exclude_isolated_nodes: bool = False) -> float` - returns a net position of the area calculated as sum of generation - sum of load. If *exclude_isolated_nodes* is *True*, np is calculated without isolated nodes, but this can take significantly longer since isolation of all nodes needs to be checked.\
♻ `Area.xnp(exclude_isolated_nodes: bool = False) -> float` - returns a net position of the `Area.xnodes` calculated as sum of generation - sum of load. If *exclude_isolated_nodes* is *True*, np is calculated without isolated nodes, but this can take significantly longer since isolation of all nodes needs to be checked.\
♻ `Area.uct(trim: bool = False) -> str` - returns uct string for ##Z block of the area.

### 📚 `Node()`
Dataclass for holding parameters of nodes (buses).
All arguments are optional which means you can create an empty instance of a node.
```
>>> bus = Node()
>>> print(bus)
Node(code=None, name=None, status=None, node_type=None, reference_voltage=None, pl=None, ql=None, pg=None, qg=None, pg_min=None, pg_max=None, qg_min=None, qg_max=None, static_of_primary_control=None, primary_control_PN=None, sk3=None, x_to_r=None, area=None, pslfId=None)
```
And asign attributes afterwards:
```
>>> bus = Node()
>>> bus.code = "bus uct code"
>>> bus
Node(code='bus uct code', name=None, status=None, node_type=None, reference_voltage=None, pl=None, ql=None, pg=None, qg=None, pg_min=None, pg_max=None, qg_min=None, qg_max=None, static_of_primary_control=None, primary_control_PN=None, sk3=None, x_to_r=None, plant_type=None, area=None, pslfId=None)
```
Or you can specify all or only some of them during initialization.

|Arguments/attributes|UCT parameter|
|:---|:---|
|`code: str = None`|Node (code)|
|`name: str = None`|Node (geographical name)|
|`status: int = None`|Status: 0 = real, 1 = equivalent|
|`node_type: int = None`|Node type code (0 = P and Q constant (PQ node); 1 = Q and 9 constant, 2 = P and U constant (PU node), 3 = U and 0 constant (global slack node, only one in the whole network))|
|`reference_voltage: float = None`|Voltage (reference value, 0 not allowed) (kV)|
|`pl: float = None`|Active load (MW)|
|`ql: float = None`|Reactive load (MVar)|
|`pg: float = None`|Active power generation (MW)|
|`qg: float = None`|Reactive power generation (MVar)|
|`pg_min: float = None`|Minimum permissible generation (MW)|
|`pg_max: float = None`|Maximum permissible generation (MW)|
|`qg_min: float = None`|Minimum permissible generation (MVar)|
|`qg_max: float = None`|Maximum permissible generation (MVar)|
|`static_of_primary_control: float = None`|Static of primary control (%)|
|`primary_control_PN: float = None`|Nominal power for primary control (MW)|
|`sk3: float = None`|Three phase short circuit power (MVA) **o|
|`x_to_r: float = None`|X/R ratio ()|
|`plant_type: str = None`|Power plant type (H: hydro, N: nuclear, L: lignite, C: hard coal, G: gas, O: oil, W: wind, F: further)|
|`area: str = None`|Area ISO code|
|`pslfId: int = None`|PSLF node id|

Other attributes:\
▶ `Node.grid -> Grid` reference to the Grid instance where the node belongs. Default value is *None*. If the grid is initialized, it is set to the same instance.

```
>>> md = Grid(r"c:\Folder_With_Uct_Files\Uct_file.uct")
>>> md
Grid(Nodes: 19600; Lines: 23868; Transformers: 3993; Regulations: 2845; Parameters: 2; Schedules: 3)
>>> nd = list(md.nodes.values())[0]
>>> nd.grid
Grid(Nodes: 19600; Lines: 23868; Transformers: 3993; Regulations: 2845; Parameters: 2; Schedules: 3)
>>> md == nd.grid
True
```
#### Properties
◼ `Node.voltage -> int` - returns voltage of the node based on the UCT voltage definition (according to 6th node code character).\
◼ `Node.id -> str` - returns id of the node which is basically equal to `Node.code`

#### Methods
♻ `Node.load_uct(UctText: str)` - loads Node parameters from uct text of the node.\
♻ `Node.load_from_regex_dictionary(regex_dictionary: dict)` - loads Node parameters from dictionary of parameters resulting from a regex search or other dictionary organized as {\<attribute name>__\<type>: value} where *type* is one of *str*, *int*, *float* and value is of *str* type. It is used by `Node.load_uct()` method.\
♻ `Node.uct(trim: bool = False) - str` - returns uct text of the node. If trim is true, tracing spaces are stripped.\
♻ `Node.lines() -> list` - returns list of `Grid.lines` connected to the Node.\
♻ `Node.transformers() -> list` - returns list of `Grid.transformers` connected to the Node.\
♻ `Node.isolated() -> bool` - returns `True` when none connecting element is connected to the node or in operation i.e. node is isolated from the rest of the grid.

### 📚 `Line()`
Dataclass for parameters of lines. All arguments are optional which means you can create an empty instance exactly the same as with [nodes](#-node).

|Arguments/attributes|UCT parameter|
|:---|:---|
|`node1: str = None`|Node 1 (code)|
|`node2: str = None`|Node 2 (code)|
|`order_code: str = None`|Order code (1,2, 3 ... 9, A, B, C ... Z)|
|`status: int = None`|Status (0, 1,2 or 7, 8, 9)|
|`r: float = None`|Resistance R (Q)|
|`x: float = None`|Reactance X (Q)|
|`b: float = None`|Susceptance B (pS)|
|`i_max: int = None`|Current limit I (A)|
|`name: str = None`|Element name (optional)|

Other attributes:\
▶ `Line.grid -> Grid` reference to the Grid instance where the line belongs. Exactly the same as with [nodes](#-node).

#### Properties
◼ `Line.id -> str` - returns id of the line which is equal to *"{node1} {node2} {order code}"* of the line.\
◼ `Line.pslfId -> str` - returns formatted string representing GE PSLF identification for the line equal to *"{node1.pslfId} {node2.pslfId} {order code} 1"*.
◼ `Line.oNode1 -> Node` - returns [Node](#-node) object for node1 of the line.
◼ `Line.oNode1 -> Node` - returns [Node](#-node) object for node2 of the line.

#### Methods
♻ `Line.load_uct(UctText: str)` - loads Line parameters from uct text of the line.\
♻ `Line.load_from_regex_dictionary(regex_dictionary: dict)` - loads Line parameters from dictionary of parameters resulting from a regex search or other dictionary organized as {\<attribute name>__\<type>: value} where *type* is one of *str*, *int*, *float* and value is of *str* type. It is used by `Line.load_uct()` method.\
♻ `Line.uct(trim: bool = False) - str` - returns uct text of the line. If trim is true, tracing spaces are stripped.

### 📚 `Transformer()`
Dataclass for parameters of transformers. All arguments are optional which means you can create an empty instance exactly the same as with [nodes](#-node).

|Arguments/attributes|UCT parameter|
|:---|:---|
|`node1: str = None`|Node 1 ( code) (non-regulated winding)|
|`node2: str = None`|Node 2 ( code) (regulated winding)|
|`order_code: str = None`|Order code (1,2, 3 ... 9, A,B,C ... Z)|
|`status: int = None`|Status (0, 1 or 8, 9) **|
|`v1: float = None`|Rated voltage 1: non-regulated winding (kV)|
|`v2: float = None`|Rated voltage 2: regulated winding (kV)|
|`sn: float = None`|Nominal power (MVA)|
|`r: float = None`|Resistance R (Q) *|
|`x: float = None`|Reactance X (Q) * ***|
|`b: float = None`|Susceptance B (pS) *|
|`g: float = None`|Conductance G (pS) *|
|`i_max: int = None`|Current limit I (A) *|
|`name: str = None`|Element name (optional) |
|`regulation: any = None`|[Regulation](#-regulation) object for the transformer|
|`parameters: list = []`|List of [special parameter objects](#-regulation) for the transformer|

Other attributes:\
▶ `Transformer.grid -> Grid` reference to the Grid instance where the transformer belongs. Exactly the same as with [nodes](#-node).

#### Properties
◼ `Transformer.id -> str` - returns id of the transformer which is equal to *"{node1} {node2} {order code}"* of the transformer.\
◼ `Transformer.oNode1 -> Node` - returns [Node](#-node) object for node1 of the transformer.\
◼ `Transformer.oNode2 -> Node` - returns [Node](#-node) object for node2 of the transformer.

#### Methods
♻ `Transformer.load_uct(UctText: str)` - loads Transformer parameters from uct text of the transformer.\
♻ `Transformer.load_from_regex_dictionary(regex_dictionary: dict)` - loads Transformer parameters from dictionary of parameters resulting from a regex search or other dictionary organized as {\<attribute name>__\<type>: value} where *type* is one of *str*, *int*, *float* and value is of *str* type. It is used by `Transformer.load_uct()` method.\
♻ `Transformer.uct(trim: bool = False) - str` - returns uct text of the transformer. If trim is true, tracing spaces are stripped.

### 📚 `Regulation()`
Dataclass for parameters of regulation of transformers. All arguments are optional which means you can create an empty instance exactly the same as with [nodes](#-node).

|Arguments/attributes|UCT parameter|
|:---|:---|
|`node1: str = None`|Node 1 (code) (non-regulated winding)|
|`node2: str = None`|Node 2 (code) (regulated winding)|
|`order_code: str = None`|Order code (1,2, 3 ... 9, A,B,C ... Z)|
|`phase_delta_u: float = None`|8u (%)|
|`phase_taps: int = None`|n|
|`phase_tap: int = None`|n’|
|`phase_u: float = None`|U (kV) (optional) ? |
|`angle_delta_u: float = None`|8u (%)* |
|`angle_phi: float = None`|0 (°)* |
|`angle_taps: int = None`|n* |
|`angle_tap: int = None`|n’* |
|`angle_p: float = None`|P (MW)* (optional) |
|`angle_type: str = None`|Type* (ASYM: asymmetrical, SYMM: symmetrical) |

Other attributes:\
▶ `Regulation.grid -> Grid` reference to the Grid instance where the regulation belongs. Exactly the same as with [nodes](#-node).

#### Properties
◼ `Regulation.id -> str` - returns id of the regulation which is equal to *"{node1} {node2} {order code}"* of the regulation. It is equal to the id of the corresponding transformer.\

#### Methods
♻ `Regulation.load_uct(UctText: str)` - loads Regulation parameters from uct text of the regulation.\
♻ `Regulation.load_from_regex_dictionary(regex_dictionary: dict)` - loads Regulation parameters from dictionary of parameters resulting from a regex search or other dictionary organized as {\<attribute name>__\<type>: value} where *type* is one of *str*, *int*, *float* and value is of *str* type. It is used by `Regulation.load_uct()` method.\
♻ `Regulation.uct(trim: bool = False) - str` - returns uct text of the regulation. If trim is true, tracing spaces are stripped.

### 📚 `Parameter()`
Dataclass for parameters of special Parameter of transformers. All arguments are optional which means you can create an empty instance exactly the same as with [nodes](#-node).

|Arguments/attributes|UCT parameter|
|:---|:---|
|`node1: str = None`|Node 1 (code) (non-regulated winding)|
|`node2: str = None`|Node 2 (code) (regulated winding)|
|`order_code: str = None`|Order code (1,2, 3 ... 9, A,B,C ... Z)|
|`tap: int = None`|Tap position (n’)|
|`r: float = None`|Resistance R at tap n’ (Q)*|
|`x: float = None`|Reactance X at tap n’ (Q)*|
|`delta_u: float = None`|Au at tap n’ (%)|
|`alfa: float = None`|Phase shift angle a at tap n’ (°) (0° for phase regulation)|

Other attributes:\
▶ `Parameter.grid -> Grid` reference to the Grid instance where the parameter belongs. Exactly the same as with [nodes](#-node).

#### Properties
◼ `Parameter.id -> str` - returns id of the parameter which is equal to *"{node1} {node2} {order code} {tap}"* of the parameter.\
◼ `Parameter.transformer_id -> str` - returns id of the corresponding trnasformer which is equal to *"{node1} {node2} {order code}"* of the parameter. It is equal to the id of the corresponding transformer.\

#### Methods
♻ `Parameter.load_uct(UctText: str)` - loads Parameter parameters from uct text of the parameter.\
♻ `Parameter.load_from_regex_dictionary(regex_dictionary: dict)` - loads Parameter parameters from dictionary of parameters resulting from a regex search or other dictionary organized as {\<attribute name>__\<type>: value} where *type* is one of *str*, *int*, *float* and value is of *str* type. It is used by `Parameter.load_uct()` method.\
♻ `Parameter.uct(trim: bool = False) - str` - returns uct text of the parameter. If trim is true, tracing spaces are stripped.

### 📚 `Schedule()`
Dataclass for parameters of a scheduled exchange. All arguments are optional which means you can create an empty instance exactly the same as with [nodes](#-node).

|Arguments/attributes|UCT parameter|
|:---|:---|
|`country1: str = None`|Country 1 (ISO code)|
|`country2: str = None`|Country 2 (ISO code)|
|`schedule: float = None`|P (MW) scheduled active power exchange|
|`comments: str = None`|Comments (optional)|

Other attributes:\
▶ `Schedule.grid -> Grid` reference to the Grid instance where the schedule belongs. Exactly the same as with [nodes](#-node).

#### Properties
◼ `Schedule.id -> str` - returns id of the schedule which is equal to *"{country1} {country2}"* of the schedule.\

#### Methods
♻ `Schedule.load_uct(UctText: str)` - loads Schedule parameters from uct text of the schedule.\
♻ `Schedule.load_from_regex_dictionary(regex_dictionary: dict)` - loads Schedule parameters from dictionary of parameters resulting from a regex search or other dictionary organized as {\<attribute name>__\<type>: value} where *type* is one of *str*, *int*, *float* and value is of *str* type. It is used by `Schedule.load_uct()` method.\
♻ `Schedule.uct(trim: bool = False) - str` - returns uct text of the schedule. If trim is true, tracing spaces are stripped.

### 📚 `Sub(**kwargs)` :notebook_with_decorative_cover:
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