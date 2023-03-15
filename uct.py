import os.path
import re
import pdb
import datetime
from dataclasses import dataclass, field

class Sub:
    def __init__(self, **kwargs) -> None:
        for name, value in kwargs.items():
            setattr(self, name, value)
    def __repr__(self) -> str:
        return "Sub(%s)" %", ".join([f"{item}={getattr(self,item)!r}" for item in dir(self) if not item.startswith("__")])

class Grid:
    __slots__ = ["file","uct_text_original", "name_parts", "comments", "uct_version", "nodes", "lines", "transformers", "regulations", "parameters", "schedules", "areas", "version",
                "filename", "not_read"]
    
    
    def __init__(self, uct_file_path: str):
        self.file = uct_file_path
        # self.name_parts = self.__get_name_parts__()
        self.filename = Sub(**self.__get_name_parts__())
        # self.date = self.__date__()
        self.uct_text_original = open(self.file).read()
        self.uct_version = None #Filled by calling __get_comments__ method.
        self.comments = self.__get_comments__()
        self.areas = {}
        self.not_read = {}
        # self.nodes = __get_elements__(self,regex["area"],regex["node"],Node)
        self.nodes = self.__get_elements__(Node)
        self.lines = self.__get_elements__(Line)
        self.regulations = self.__get_elements__(Regulation)
        # pdb.set_trace()
        self.parameters = self.__get_elements__(Parameter)
        self.transformers = self.__get_elements__(Transformer)
        self.schedules = self.__get_elements__(Schedule)
        
        
        
        
    def __get_name_parts__(self):
        name_rgx_match = rgx["file"].match(os.path.basename(self.file).upper())
        if not name_rgx_match:
            raise Exception("File name does not match UCT standard")
        else:
            return name_rgx_match.groupdict()
    @property        
    def date(self) -> datetime.datetime:
        return datetime.datetime(int(self.filename.year),
                                 int(self.filename.month),
                                 int(self.filename.day),
                                 int(self.filename.hour),
                                 int(self.filename.minute),
                                 0)

    @property
    def slack(self) -> list:
        return [node for node in self.nodes.values() if node.node_type == 3]

    def __get_comments__(self):
        # comment_rgx = re.compile(regex["comment"], re.MULTILINE)
        # comment_rgx_match = comment_rgx.finditer(self.uct_text_original)
        comment_rgx_match = rgx["comment"].finditer(self.uct_text_original)
        comments_list = []
        for match in comment_rgx_match:
            if match.groupdict()["version"]:
                self.uct_version = match.groupdict()["version"]
            comments_list.append(match.groupdict()["text"])
        return comments_list

    def __get_elements__(self, element_class) -> dict:
        elements = {}
        class_name = element_class().__class__.__name__
        if class_name == "Node":
            # pdb.set_trace()
            node_area_codes = {country["node"]: cc for cc, country in countries.items() if country["node"]}
        for match in rgx[class_name + 's'].finditer(self.uct_text_original):
            # print(match)
            # try:
            # pdb.set_trace()
            if class_name == "Node":
                area_code = match.groupdict()["area"]
                if area_code: self.areas[area_code] = Area(area_code, self)
            # except:
            #     pdb.post_mortem()
            #     area_code = None
            
            # print(match.groupdict()["elements"])
            number_of_elements = len(re.findall("^\S+.*?$", match.groupdict()["elements"], re.MULTILINE))
            
            # pdb.set_trace()
            # print(class_name, number_of_elements)
            counter = 0
            for el_match in rgx[class_name].finditer(match.groupdict()["elements"]):
                element = element_class()
                element.load_from_regex_dictionary(el_match.groupdict())
                if class_name == "Node":
                    if area_code:
                        element.area = area_code
                    else:
                        element.area = node_area_codes[element.code[0]]
                        if element.area not in self.areas:
                            # print(f"adding area {element.area}")
                            self.areas[element.area] = Area(element.area, self)
                if class_name == "Transformer" and element.id in self.regulations:
                    element.regulation = self.regulations[element.id]
                    if element.id in [parameter.transformer_id for parameter in self.parameters.values()]: element.parameters.extend([parameter for parameter in self.parameters.values() if parameter.transformer_id == element.id])
                element.grid = self
                elements[element.id] = element
                counter += 1

            if counter != number_of_elements:
                notadd = [line for line in match.groupdict()["elements"].split("\n") if line and not rgx[class_name].match(line)]
                if notadd:
                    # pdb.set_trace()
                    if class_name not in self.not_read: self.not_read[class_name] = []
                    self.not_read[class_name] = [*self.not_read[class_name], *notadd]

                # print(notadd)
                # print("Not added:",class_name, number_of_elements-counter)
        return elements
    
    def __repr__(self) -> str:
        return "Grid(%s)" %"; ".join([f"{ky + 's'}: {len(getattr(self,ky.lower() + 's'))}" for ky in uct_export])
    
    def uct(self, trim: bool = False, C: bool = True, N: bool = True, L: bool = True, T: bool = True, E: bool = True) -> str:
        output = ""
        if C:
            output = f"##C {self.uct_version}\n" + "\n".join(self.comments)
        if N:
            output = output + "##N\n" + "".join([area.uct(trim) for area in self.areas.values()])
        if L:
            output = output + "##L\n" + "\n".join([item.uct(trim) for item in self.lines.values()]) + "\n"
        if T:
            output = output + "##T\n" + "\n".join([item.uct(trim) for item in self.transformers.values()]) + "\n"
            if self.regulations: output = output + "##R\n" + "\n".join([item.uct(trim) for item in self.regulations.values()]) + "\n"
            # pdb.set_trace()
            if self.parameters: output = output + "##TT\n" + "\n".join([item.uct(trim) for item in self.parameters.values()]) + "\n"
        if E and self.schedules:
            output = output = output + "##E\n" + "\n".join([item.uct(trim) for item in self.schedules.values()]) + "\n"

        return output

class Area:
    __slots__ = ["code", "grid"]

    def __init__(self, area_code: str, grid_instance: Grid):
        self.code = area_code
        self.grid = grid_instance

    def nodes(self) -> dict:
        return {key: item for key, item in self.grid.nodes.items() if item.area == self.code}
    
    def xnodes(self) -> dict:
        lines = self.lines().values()
        nodes = []
        for line in lines:
            nodes.append(line.node1)
            nodes.append(line.node2)
        return {key: item for key, item in self.grid.areas["XX"].nodes().items() if key in nodes}

    def slack(self) -> list:
        return [node for node in self.nodes().values() if node.node_type == 3]
    
    def xnp(self) -> float:
        xnodes = self.xnodes().values()
        return -1*sum([node.pg for node in xnodes]) - sum([node.pl for node in xnodes])

    def lines(self) -> dict:
        return {key: item for key, item in self.grid.lines.items() if self.grid.nodes[item.node1].area == self.code or self.grid.nodes[item.node2].area == self.code}
    
    def transformers(self) -> dict:
        return {key: item for key, item in self.grid.transformers.items() if self.grid.nodes[item.node1].area == self.code or self.grid.nodes[item.node2].area == self.code}
    
    def schedules(self) -> dict:
        return {key: item for key, item in self.grid.schedules.items() if item.country1 == self.code or item.country2 == self.code}

    def __repr__(self) -> str:
        nodes = self.nodes()
        lines = self.lines()
        transf = self.transformers()
        return f"Area({self.code}, Nodes: {len(nodes) if nodes else 0}, Lines: {len(lines) if lines else 0}, Transformers: {len(transf) if transf else 0}, NP: {self.np():.2f}, XNP: {self.xnp():.2f})"

    def np(self) -> float:
        nodes = self.nodes().values()
        return -1*sum([node.pg for node in nodes]) - sum([node.pl for node in nodes])
    
    def uct(self, trim: bool = False) -> str:
        return f"##Z{self.code}\n" + "\n".join([node.uct(trim) for node in self.nodes.values()]) + "\n"

class Element():
    grid: Grid = None
    def load_uct(self, UctText: str):
        regex = regex[self.__class__.__name__.lower()]
        rgx = re.compile(regex)
        match = rgx.search(UctText)
        self.load_from_regex_dictionary(match.groupdict())
        
    def load_from_regex_dictionary(self, regex_dictionary: dict):
        for key, value in regex_dictionary.items():
            name, function = key.split("__")
            try:
                if function != "str":
                    setattr(self, name, functions[function](value.strip()))
                else:
                    setattr(self, name, value.strip())
            except:
                setattr(self, name, None)
    
    def uct(self, trim: bool = False) -> str:
        # if self.__class__.__name__ == "Node" and self.code == "XSK_KP51": pdb.set_trace()
        output = " ". join([f"{conv(getattr(self, att), length)}" for att, length in uct_export[self.__class__.__name__].items()]) + " "
        return output.strip() + " " if trim else output

@dataclass()
class Node(Element):
    code: str = None #Node (code)
    name: str = None #Node (geographical name)
    status: int = None #Status: 0 = real, 1 = equivalent
    node_type: int = None #Node type code (0 = P and Q constant (PQ node); 1 = Q and 9 constant, 2 = P and U constant (PU node), 3 = U and 0 constant (global slack node, only one in the whole network))
    reference_voltage: float = None #Voltage (reference value, 0 not allowed) (kV)
    pl: float = None #Active load (MW)
    ql: float = None #Reactive load (MVar)
    pg: float = None #Active power generation (MW)
    qg: float = None #Reactive power generation (MVar)
    pg_min: float = None #Minimum permissible generation (MW) *o
    pg_max: float = None #Maximum permissible generation (MW) *o
    qg_min: float = None #Minimum permissible generation (MVar) *o
    qg_max: float = None #Maximum permissible generation (MVar) *o
    static_of_primary_control: float = None #Static of primary control (%) *o
    primary_control_PN: float = None #Nominal power for primary control (MW) *o
    sk3: float = None #Three phase short circuit power (MVA) **o
    x_to_r: float = None #X/R ratio () **o
    plant_type: str = None #Power plant type *o (H: hydro, N: nuclear, L: lignite, C: hard coal, G: gas, O: oil, W: wind, F: further)
    area: str = None
    pslfId: int = None

    @property
    def voltage(self) -> int:
        return uct_voltage[int(self.code[6])]

    @property
    def id(self) -> str:
        return self.code
    
    @property
    def lines(self) -> list:
        return [
            line
            for line in self.grid.lines.values()
            if self.code in [line.node1, line.node2]
        ]

class Connecting_Element:
    @property
    def oNode1(self) -> Node:
        return self.grid.nodes[self.node1]
    
    @property
    def oNode2(self) -> Node:
        return self.grid.nodes[self.node2]


@dataclass
class Line(Element, Connecting_Element):
    node1: str = None #Node 1 (code)
    node2: str = None #Node 2 (code)
    order_code: str = None #Order code (1,2, 3 ... 9, A, B, C ... Z)
    status: int = None #Status (0, 1,2 or 7, 8, 9)
    r: float = None #Resistance R (Q)
    x: float = None #Reactance X (Q)
    b: float = None #Susceptance B (pS)
    i_max: int = None #Current limit I (A)
    name: str = None #Element name (optional) ***

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"
    
    @property
    def pslfId(self) ->str:
        if self.oNode1.pslfId and self.oNode2.pslfId:
            return f"{self.oNode1.pslfId} {self.oNode2.pslfId} {self.order_code} 1"
        else:
            return None

@dataclass
class Transformer(Element, Connecting_Element):
    node1: str = None #Node 1 ( code) (non-regulated winding)
    node2: str = None #Node 2 ( code) (regulated winding)
    order_code: str = None #Order code (1,2, 3 ... 9, A,B,C ... Z)
    status: int = None #Status (0, 1 or 8, 9) **
    v1: float = None #Rated voltage 1: non-regulated winding (kV)
    v2: float = None #Rated voltage 2: regulated winding (kV)
    sn: float = None #Nominal power (MVA)
    r: float = None #Resistance R (Q) *
    x: float = None #Reactance X (Q) * ***
    b: float = None #Susceptance B (pS) *
    g: float = None #Conductance G (pS) *
    i_max: int = None #Current limit I (A) *
    name: str = None #Element name (optional) 
    regulation: any = None
    parameters: list = field(default_factory=lambda: [])

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Regulation(Element):
    node1: str = None #Node 1 (code) (non-regulated winding)
    node2: str = None #Node 2 (code) (regulated winding)
    order_code: str = None #Order code (1,2, 3 ... 9, A,B,C ... Z)
    phase_delta_u: float = None #8u (%)
    phase_taps: int = None #n
    phase_tap: int = None #n’
    phase_u: float = None #U (kV) (optional) ? 
    angle_delta_u: float = None #8u (%)* 
    angle_phi: float = None #0 (°)* 
    angle_taps: int = None #n* 
    angle_tap: int = None #n’* 
    angle_p: float = None #P (MW)* (optional) 
    angle_type: str = None #Type* (ASYM: asymmetrical, SYMM: symmetrical) 

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Parameter(Element):
    node1: str = None #Node 1 (code) (non-regulated winding)
    node2: str = None #Node 2 (code) (regulated winding)
    order_code: str = None #Order code (1,2, 3 ... 9, A,B,C ... Z)
    tap: int = None #Tap position (n’)
    r: float = None #Resistance R at tap n’ (Q)*
    x: float = None #Reactance X at tap n’ (Q)*
    delta_u: float = None #Au at tap n’ (%)
    alfa: float = None #Phase shift angle a at tap n’ (°) (0° for phase regulation)

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1} {self.tap:>3}"

    @property
    def transformer_id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Schedule(Element):
    country1: str = None #Country 1 (ISO code)
    country2: str = None #Country 2 (ISO code)
    schedule: float = None #P (MW) scheduled active power exchange
    comments: str = None #Comments (optional)
    
    @property
    def id(self):
        return f"{self.country1:<2} {self.country2:<2}"

def conv(property_value, width:int) -> str:
    if property_value in [None, ""]:
        return " " * width
    elif type(property_value) != str:
        if property_value>(10**width)-1:
            return f"{(10**width)-1}"
        elif property_value<-1*(10**(width-1))+1:
            return f"{-1*(10**(width-1))+1}"
        elif property_value > (10**(width-2))-1:
            # return f"{round(property_value,0):width.0f}"
            return "{num:{len}.0f}".format(num=property_value, len = width)
        elif property_value < -1*(10**(width-3))+1:
            return "{num:{len}.0f}".format(num=property_value, len = width-1)
        else:
            dec = width - len(f"{int(property_value)}")-1 if type(property_value)!=int else 0
            if str(property_value).startswith('-'): dec = max(dec - 1,0)
            if type(property_value) == float:
                return "{num:{len}.{dc}f}".format(num=round(property_value,dec), len = width, dc = dec)
            else:
                return "{num:{len}.{dc}f}".format(num=round(property_value,dec), len = width, dc = dec)
    else:
        return f"{(property_value+' '*width)[:width]}"

functions = {
    "float" : float,
    "str" : str,
    "int": int
}

uct_voltage = [750, 380, 220, 150, 120, 110, 70, 27, 330, 500]

countries = {
    "AL" : {"number": 2 , "node": "A" , "code": "AL", "name": "Albania"    , "long_name": "Shqiperia (Albania)"                         , "code2": "AL" , "cgm": False, "pslf_code": 21  , "pslf_name": "Albansko"           },
    "AT" : {"number": 1 , "node": "O" , "code": "AT", "name": "Austria"    , "long_name": "Österreich (Austria)"                        , "code2": "A"  , "cgm": False, "pslf_code": 18  , "pslf_name": "Rakusko"            },
    "BA" : {"number": 5 , "node": "W" , "code": "BA", "name": "Bosna"      , "long_name": "Bosna i Hercegovina (Bosnia and Herzegovina)", "code2": "BiH", "cgm": False, "pslf_code": 8   , "pslf_name": "Bosna a Hercegovina"},
    "BE" : {"number": 3 , "node": "B" , "code": "BE", "name": "Belgium"    , "long_name": "Belgique (Belgium)"                          , "code2": "B"  , "cgm": False, "pslf_code": 30  , "pslf_name": "Belgicko"           },
    "BG" : {"number": 4 , "node": "V" , "code": "BG", "name": "Bulgaria"   , "long_name": "Bulgarija (Bulgaria)"                        , "code2": "BG" , "cgm": False, "pslf_code": 10  , "pslf_name": "Bulharsko"          },
    "BY" : {"number": 6 , "node": "3" , "code": "BY", "name": "Belarus"    , "long_name": "Belorussija (Belarus)"                       , "code2": "BY" , "cgm": False, "pslf_code": 24  , "pslf_name": "Bielorusko"         },
    "CZ" : {"number": 8 , "node": "C" , "code": "CZ", "name": "Czech"      , "long_name": "Ceska Republika (Czech Republic)"            , "code2": "CZ" , "cgm": False, "pslf_code": 2   , "pslf_name": "Cesko"              },
    "DE" : {"number": 9 , "node": "D" , "code": "DE", "name": "Germany"    , "long_name": "Deutschland (Germany)"                       , "code2": "D"  , "cgm": False, "pslf_code": 16  , "pslf_name": "Nemecko"            },
    "DK" : {"number": 10, "node": "K" , "code": "DK", "name": "Denmark"    , "long_name": "Danmark (Denmark)"                           , "code2": "DK" , "cgm": False, "pslf_code": 20  , "pslf_name": "Dansko"             },
    "ES" : {"number": 11, "node": "E" , "code": "ES", "name": "Spain"      , "long_name": "Espana (Spain)"                              , "code2": "E"  , "cgm": False, "pslf_code": 13  , "pslf_name": "Spanielsko"         },
    "FR" : {"number": 12, "node": "F" , "code": "FR", "name": "France"     , "long_name": "France (France)"                             , "code2": "F"  , "cgm": False, "pslf_code": 14  , "pslf_name": "Francuzsko"         },
    "GB" : {"number": 13, "node": "5" , "code": "GB", "name": "Britain"    , "long_name": "Great Britain (Great Britain)"               , "code2": "GB" , "cgm": False, "pslf_code": 26  , "pslf_name": "Velka Britania"     },
    "GR" : {"number": 14, "node": "G" , "code": "GR", "name": "Greece"     , "long_name": "Hellas (Greece)"                             , "code2": "GR" , "cgm": False, "pslf_code": 22  , "pslf_name": "Grecko"             },
    "HR" : {"number": 16, "node": "H" , "code": "HR", "name": "Croatia"    , "long_name": "Hrvatska (Croatia)"                          , "code2": "HR" , "cgm": False, "pslf_code": 11  , "pslf_name": "Chorvatsko"         },
    "HU" : {"number": 15, "node": "M" , "code": "HU", "name": "Hungary"    , "long_name": "Magyarorszag (Hungary)"                      , "code2": "H"  , "cgm": False, "pslf_code": 1   , "pslf_name": "Madarsko"           },
    "CH" : {"number": 7 , "node": "S" , "code": "CH", "name": "Switzerland", "long_name": "Schweiz (Switzerland)"                       , "code2": "CH" , "cgm": False, "pslf_code": 15  , "pslf_name": "Svajciarsko"        },
    "IT" : {"number": 17, "node": "I" , "code": "IT", "name": "Italy"      , "long_name": "Italia (Italy)"                              , "code2": "I"  , "cgm": False, "pslf_code": 19  , "pslf_name": "Taliansko"          },
    "KS" : {"number": 39, "node": "_" , "code": "KS", "name": "Kosovo"     , "long_name": "Kosovo"                                      , "code2": "KS" , "cgm": False, "pslf_code": 39  , "pslf_name": "Kosovo"             },
    "LT" : {"number": 19, "node": "6" , "code": "LT", "name": "Lithuania"  , "long_name": "Lietuva (Lithuania)"                         , "code2": "LT" , "cgm": False, "pslf_code": 37  , "pslf_name": "Litva"              },
    "LU" : {"number": 18, "node": "1" , "code": "LU", "name": "Luxemburg"  , "long_name": "Luxembourg (Luxemburg)"                      , "code2": "L"  , "cgm": False, "pslf_code": 31  , "pslf_name": "Luxembursko"        },
    "MA" : {"number": 20, "node": "2" , "code": "MA", "name": "Morocco"    , "long_name": "Maroc (Morocco)"                             , "code2": "MA" , "cgm": False, "pslf_code": 27  , "pslf_name": "Maroco"             },
    "MD" : {"number": 21, "node": "7" , "code": "MD", "name": "Moldavia"   , "long_name": "Moldava (Moldavia)"                          , "code2": "MD" , "cgm": False, "pslf_code": 38  , "pslf_name": "Moldavsko"          },
    "ME" : {"number": 34, "node": "0" , "code": "ME", "name": "Montenegro" , "long_name": "Crna Gora (Montenegro)"                      , "code2": "MNE", "cgm": False, "pslf_code": 34  , "pslf_name": "Cierna Hora"        },
    "MK" : {"number": 22, "node": "Y" , "code": "MK", "name": "Makedonija" , "long_name": "Makedonija (FYROM)"                          , "code2": "MK" , "cgm": False, "pslf_code": 23  , "pslf_name": "Macedonsko"         },
    "NL" : {"number": 24, "node": "N" , "code": "NL", "name": "Netherlands", "long_name": "Nederland (Netherlands)"                     , "code2": "NL" , "cgm": False, "pslf_code": 32  , "pslf_name": "Holandsko"          },
    "NO" : {"number": 23, "node": "9" , "code": "NO", "name": "Norway"     , "long_name": "Norge (Norway)"                              , "code2": "N"  , "cgm": False, "pslf_code": 36  , "pslf_name": "Norsko"             },
    "PL" : {"number": 26, "node": "Z" , "code": "PL", "name": "Poland"     , "long_name": "Polska (Poland)"                             , "code2": "PL" , "cgm": False, "pslf_code": 3   , "pslf_name": "Polsko"             },
    "PT" : {"number": 25, "node": "P" , "code": "PT", "name": "Portugal"   , "long_name": "Portugal (Portugal)"                         , "code2": "P"  , "cgm": False, "pslf_code": 5   , "pslf_name": "Portugalsko"        },
    "RO" : {"number": 27, "node": "R" , "code": "RO", "name": "Romania"    , "long_name": "Romania (Romania)"                           , "code2": "RO" , "cgm": False, "pslf_code": 9   , "pslf_name": "Rumunsko"           },
    "RS" : {"number": 35, "node": "J" , "code": "RS", "name": "Serbia"     , "long_name": "Srbija (Serbia)"                             , "code2": "SRB", "cgm": False, "pslf_code": 17  , "pslf_name": "Srbsko"             },
    "RU" : {"number": 28, "node": "4" , "code": "RU", "name": "Russia"     , "long_name": "Rossija (Russia)"                            , "code2": "RUS", "cgm": False, "pslf_code": 25  , "pslf_name": "Rusko"              },
    "SE" : {"number": 29, "node": "8" , "code": "SE", "name": "Sweden"     , "long_name": "Sverige (Sweden)"                            , "code2": "S"  , "cgm": False, "pslf_code": 35  , "pslf_name": "Svedsko"            },
    "SI" : {"number": 31, "node": "L" , "code": "SI", "name": "Slovenia"   , "long_name": "Slovenija (Slovenia)"                        , "code2": "SLO", "cgm": False, "pslf_code": 11  , "pslf_name": "Chorvatsko"         },
    "SK" : {"number": 30, "node": "Q" , "code": "SK", "name": "Slovakia"   , "long_name": "Slovensko (Slovakia)"                        , "code2": "SK" , "cgm": False, "pslf_code": 4   , "pslf_name": "Slovensko"          },
    "TR" : {"number": 32, "node": "T" , "code": "TR", "name": "Turkey"     , "long_name": "Türkiye (Turkey)"                            , "code2": "TR" , "cgm": False, "pslf_code": 33  , "pslf_name": "Turecko"            },
    "UA" : {"number": 33, "node": "U" , "code": "UA", "name": "Ukraine"    , "long_name": "Ukraina (Ukraine)"                           , "code2": "UA" , "cgm": False, "pslf_code": 7   , "pslf_name": "Ukrajina"           },
    "UC" : {"number": 37, "node": None, "code": "UC", "name": "Merged"     , "long_name": "UCTE-wide merged datasets without X nodes"   , "code2": "--" , "cgm": True , "pslf_code": None, "pslf_name": None                 },
    "UX" : {"number": 38, "node": None, "code": "UX", "name": "Merged_wX"  , "long_name": "UCTE-wide merged datasets with X nodes"      , "code2": "--" , "cgm": True , "pslf_code": None, "pslf_name": None                 },
    "XX" : {"number": 36, "node": "X" , "code": "XX", "name": "X_Nodes"    , "long_name": "Fictitious border node"                      , "code2": None , "cgm": False, "pslf_code": 40  , "pslf_name": "X-Nodes"            },
}

file_regex_parts = [
    r"(?P<year>\d{4})",
    r"(?P<month>\d{2})",
    r"(?P<day>\d{2})",
    r"_",
    r"(?P<hour>\d{2})",
    r"(?P<minute>\d{2})",
    r"_",
    r"(?P<type>FO|SN|RE|LR|[0-1][0-9]|2[0-4])",
    r"(?P<week_day>[1-7])",
    r"_",
    r"(?P<area>" + "|".join(countries.keys()) + ")",
    r"(?P<version>[0-9])",
    r"(?:_CO)?",
    r"\.UCT"
]

rgx = {
  "file": re.compile("".join(file_regex_parts)),
  "comment": re.compile(r"##C\s*?(?P<version>\S.*?\S)?\s*?[\r\n]{1,2}(?P<text>(?:.*?[\r\n]?)+?)(?=##|\Z)"),
  "Nodes": re.compile(r"##\s*?(?:N|Z\s*?(?P<area>\w{2}))\s*?[\r\n](?!\s*?(?=##|\Z))(?P<elements>.*?)(?=##|\Z)", re.DOTALL),
  "Node": re.compile(r"(?P<code__str>.{8}) (?P<name__str>.{12}) (?P<status__int>.{1}) (?P<node_type__int>.{1}) (?P<reference_voltage__float>.{6}) (?P<pl__float>.{7}) (?P<ql__float>.{7}) (?P<pg__float>.{7}) (?P<qg__float>.{7})(?: (?P<pg_min__float>.{7}))?(?: (?P<pg_max__float>.{7}))?(?: (?P<qg_min__float>.{7}))?(?: (?P<qg_max__float>.{7}))?(?: (?P<static_of_primary_control__float>.{5}))?(?: (?P<primary_control_PN__float>.{7}))?(?: (?P<sk3__float>.{7}))?(?: (?P<x_to_r__float>.{7}))?(?: (?P<plant_type__str>.{1}))?"),
  "Lines": re.compile(r"##\s*?L\s*?[\r\n](?!\s*?(?=##|\Z))(?P<elements>.*?)(?=##|\Z)", re.DOTALL),
  "Line": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<status__int>.{1}) (?P<r__float>.{6}) (?P<x__float>.{6}) (?P<b__float>.{8}) (?P<i_max__int>.{6})(?: (?P<name__str>.{12}))?"),
  "Transformers": re.compile(r"##\s*?T\s*?[\r\n](?!\s*?(?=##|\Z))(?P<elements>.*?)(?=##|\Z)", re.DOTALL),
  "Transformer": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<status__int>.{1}) (?P<v1__float>.{5}) (?P<v2__float>.{5}) (?P<sn__float>.{5}) (?P<r__float>.{6}) (?P<x__float>.{6}) (?P<b__float>.{8}) (?P<g__float>.{6}) (?P<i_max__int>.{6})(?: (?P<name__str>.{12}))?"),
  "Regulations": re.compile(r"##\s*?R\s*?[\r\n](?!\s*?(?=##|\Z))(?P<elements>.*?)(?=##|\Z)", re.DOTALL),
  "Regulation": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<phase_delta_u__float>.{5}) (?P<phase_taps__int>.{2}) (?P<phase_tap__int>.{3})(?: (?P<phase_u__float>.{5}))?(?: (?P<angle_delta_u__float>.{5}))?(?: (?P<angle_phi__float>.{5}))?(?: (?P<angle_taps__int>.{2}))?(?: (?P<angle_tap__int>.{3}))?(?: (?P<angle_p__float>.{5}))?(?: (?P<angle_type__str>.{4}))?"),
  "Parameters": re.compile(r"##\s*?TT\s*?[\r\n](?!\s*?(?=##|\Z))(?P<elements>.*?)(?=##|\Z)", re.DOTALL),
  "Parameter": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<tap__int>.{3}) (?P<r__float>.{6}) (?P<x__float>.{6}) (?P<delta_u__float>.{5}) (?P<alfa__float>.{5})"),
  "Schedules": re.compile(r"##\s*?E\s*?[\r\n](?!\s*?(?=##|\Z))(?P<elements>.*?)(?=##|\Z)", re.DOTALL),
  "Schedule": re.compile(r"(?P<country1__str>.{2}) (?P<country2__str>.{2}) (?P<schedule__float>.{7})(?: (?P<comments__str>.{12}))?")
}



uct_export = {
    "Node": {
        "code": 8, "name": 12, "status": 1, "node_type": 1, "reference_voltage": 6, "pl": 7, "ql": 7, "pg": 7, "qg": 7, "pg_min": 7, "pg_max": 7, "qg_min": 7, "qg_max": 7, "static_of_primary_control": 5, "primary_control_PN": 7, "sk3": 7, "x_to_r": 7, "plant_type": 1
    },
    "Line": {
        "node1": 8, "node2": 8, "order_code": 1, "status": 1, "r": 6, "x": 6, "b": 8, "i_max": 6, "name": 12
    },
    "Transformer": {
        "node1": 8, "node2": 8, "order_code": 1, "status": 1, "v1": 5, "v2": 5, "sn": 5, "r": 6, "x": 6, "b": 8, "g": 6, "i_max": 6, "name": 12
    },
    "Regulation": {
        "node1": 8, "node2": 8, "order_code": 1, "phase_delta_u": 5, "phase_taps": 2, "phase_tap": 3, "phase_u": 5, "angle_delta_u": 5, "angle_phi": 5, "angle_taps": 2, "angle_tap": 3, "angle_p": 5, "angle_type": 4
    },
    "Parameter": {
        "node1": 8, "node2": 8, "order_code": 1, "tap": 3, "r": 6, "x": 6, "delta_u": 5, "alfa": 5
    },
    "Schedule": {
        "country1": 2, "country2": 2, "schedule": 7, "comments": 12
    }
}