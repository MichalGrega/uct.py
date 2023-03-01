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
        for match in rgx[class_name + 's'].finditer(self.uct_text_original):
            
            if "area" in match.groupdict():
                area_code = match.groupdict()["area"]
                self.areas[area_code] = Area(area_code, self)
            
            # print(match.groupdict()["elements"])
            number_of_elements = len(re.findall("^\S+.*?$", match.groupdict()["elements"], re.MULTILINE))
            
            # pdb.set_trace()
            # print(class_name, number_of_elements)
            counter = 0
            for el_match in rgx[class_name].finditer(match.groupdict()["elements"]):
                element = element_class()
                element.load_from_regex_dictionary(el_match.groupdict())
                if element.__class__.__name__ == "Node": element.area = area_code
                if element.__class__.__name__ == "Transformer" and element.id in self.regulations:
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

    @property
    def nodes(self) -> dict:
        return {key: item for key, item in self.grid.nodes.items() if item.area == self.code}

    @property
    def lines(self) -> dict:
        return {key: item for key, item in self.grid.lines.items() if self.grid.nodes[item.node1].area == self.code or self.grid.nodes[item.node2].area == self.code}
    
    @property
    def transformers(self) -> dict:
        return {key: item for key, item in self.grid.transformers.items() if self.grid.nodes[item.node1].area == self.code or self.grid.nodes[item.node2].area == self.code}
    
    @property
    def schedules(self) -> dict:
        return {key: item for key, item in self.grid.schedules.items() if item.country1 == self.code or item.country2 == self.code}

    def __repr__(self) -> str:
        return f"Area({self.code}, Nodes: {len(self.nodes) if self.nodes else 0}, Lines: {len(self.lines) if self.lines else 0}, Transformers: {len(self.transformers) if self.transformers else 0}, NP: {self.np:.4f})"

    @property
    def np(self):
        return -1*sum([node.pg for node in self.nodes.values()]) - sum([node.p_load for node in self.nodes.values()])
    
    def uct(self, trim: bool = False):
        return f"##Z{self.code}\n" + "\n".join([node.uct(trim) for node in self.nodes.values()]) + "\n"

class Element():
    grid = None
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
    
    def uct(self, trim: bool = False):
        # if self.__class__.__name__ == "Node" and self.code == "XSK_KP51": pdb.set_trace()
        output = " ". join([f"{conv(getattr(self, att), length)}" for att, length in uct_export[self.__class__.__name__].items()]) + " "
        return output.strip() + " " if trim else output

class Connecting_Element:
    @property
    def oNode1(self):
        return self.grid.nodes[self.node1]
    
    @property
    def oNode2(self):
        return self.grid.nodes[self.node2]

@dataclass()
class Node(Element):
    code: str = None
    name: str = None
    status: int = None
    node_type: int = None
    reference_voltage: float = None
    p_load: float = None
    q_load: float = None
    pg: float = None
    qg: float = None
    pg_min: float = None
    pg_max: float = None
    qg_min: float = None
    qg_max: float = None
    static_of_primary_control: float = None
    primary_control_PN: float = None
    sk3: float = None
    x_to_r: float = None
    plant_type: str = field(repr=False, default=None)
    area: str = None
    pslfId: int = None

    @property
    def voltage(self):
        return uct_voltage[int(self.code[6])]

    @property
    def id(self):
        return self.code

@dataclass
class Line(Element, Connecting_Element):
    node1: str = None
    node2: str = None
    order_code: str = None
    status: int = None
    r: float = None
    x: float = None
    b: float = None
    i_max: int = None
    name: str = None

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Transformer(Element, Connecting_Element):
    node1: str = None
    node2: str = None
    order_code: str = None
    status: int = None
    v1: float = None
    v2: float = None
    sn: float = None
    r: float = None
    x: float = None
    b: float = None
    g: float = None
    i_max: int = None
    name: str = None
    regulation: any = None
    parameters: list = field(default_factory=lambda: [])

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Regulation(Element):
    node1: str = None
    node2: str = None
    order_code: str = None
    phase_delta_u: float = None
    phase_taps: int = None
    phase_tap: int = None
    phase_u: float = None
    angle_delta_u: float = None
    angle_phi: float = None
    angle_taps: int = None
    angle_tap: int = None
    angle_p: float = None
    angle_type: str = None

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Parameter(Element):
    node1: str = None
    node2: str = None
    order_code: str = None
    tap: int = None
    r: float = None
    x: float = None
    delta_u: float = None
    alfa: float = None

    @property
    def id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1} {self.tap:>3}"

    @property
    def transformer_id(self):
        return f"{self.node1:<8} {self.node2:<8} {self.order_code:<1}"

@dataclass
class Schedule(Element):
    country1: str = None
    country2: str = None
    schedule: float = None
    comments: str = None
    
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
    "AL" : {
        "number" :  2,
        "node" :  "A",
        "code" :  "AL",
        "name" :  "Albania",
        "long_name" :  "Shqiperia (Albania)",
        "code2" :  "AL",
        "cgm" :  False,
        "pslf_code" :  21,
        "pslf_name" :  "Albansko",
    },
    "AT" : {
        "number" :  1,
        "node" :  "O",
        "code" :  "AT",
        "name" :  "Austria",
        "long_name" :  "Österreich (Austria)",
        "code2" :  "A",
        "cgm" :  False,
        "pslf_code" :  18,
        "pslf_name" :  "Rakusko",
    },
    "BA" : {
        "number" :  5,
        "node" :  "W",
        "code" :  "BA",
        "name" :  "Bosna",
        "long_name" :  "Bosna i Hercegovina (Bosnia and Herzegovina)",
        "code2" :  "BiH",
        "cgm" :  False,
        "pslf_code" :  8,
        "pslf_name" :  "Bosna a Hercegovina",
    },
    "BE" : {
        "number" :  3,
        "node" :  "B",
        "code" :  "BE",
        "name" :  "Belgium",
        "long_name" :  "Belgique (Belgium)",
        "code2" :  "B",
        "cgm" :  False,
        "pslf_code" :  30,
        "pslf_name" :  "Belgicko",
    },
    "BG" : {
        "number" :  4,
        "node" :  "V",
        "code" :  "BG",
        "name" :  "Bulgaria",
        "long_name" :  "Bulgarija (Bulgaria)",
        "code2" :  "BG",
        "cgm" :  False,
        "pslf_code" :  10,
        "pslf_name" :  "Bulharsko",
    },
    "BY" : {
        "number" :  6,
        "node" :  "3",
        "code" :  "BY",
        "name" :  "Belarus",
        "long_name" :  "Belorussija (Belarus)",
        "code2" :  "BY",
        "cgm" :  False,
        "pslf_code" :  24,
        "pslf_name" :  "Bielorusko",
    },
    "CZ" : {
        "number" :  8,
        "node" :  "C",
        "code" :  "CZ",
        "name" :  "Czech",
        "long_name" :  "Ceska Republika (Czech Republic)",
        "code2" :  "CZ",
        "cgm" :  False,
        "pslf_code" :  2,
        "pslf_name" :  "Cesko",
    },
    "DE" : {
        "number" :  9,
        "node" :  "D",
        "code" :  "DE",
        "name" :  "Germany",
        "long_name" :  "Deutschland (Germany)",
        "code2" :  "D",
        "cgm" :  False,
        "pslf_code" :  16,
        "pslf_name" :  "Nemecko",
    },
    "DK" : {
        "number" :  10,
        "node" :  "K",
        "code" :  "DK",
        "name" :  "Denmark",
        "long_name" :  "Danmark (Denmark)",
        "code2" :  "DK",
        "cgm" :  False,
        "pslf_code" :  20,
        "pslf_name" :  "Dansko",
    },
    "ES" : {
        "number" :  11,
        "node" :  "E",
        "code" :  "ES",
        "name" :  "Spain",
        "long_name" :  "Espana (Spain)",
        "code2" :  "E",
        "cgm" :  False,
        "pslf_code" :  13,
        "pslf_name" :  "Spanielsko",
    },
    "FR" : {
        "number" :  12,
        "node" :  "F",
        "code" :  "FR",
        "name" :  "France",
        "long_name" :  "France (France)",
        "code2" :  "F",
        "cgm" :  False,
        "pslf_code" :  14,
        "pslf_name" :  "Francuzsko",
    },
    "GB" : {
        "number" :  13,
        "node" :  "5",
        "code" :  "GB",
        "name" :  "Britain",
        "long_name" :  "Great Britain (Great Britain)",
        "code2" :  "GB",
        "cgm" :  False,
        "pslf_code" :  26,
        "pslf_name" :  "Velka Britania",
    },
    "GR" : {
        "number" :  14,
        "node" :  "G",
        "code" :  "GR",
        "name" :  "Greece",
        "long_name" :  "Hellas (Greece)",
        "code2" :  "GR",
        "cgm" :  False,
        "pslf_code" :  22,
        "pslf_name" :  "Grecko",
    },
    "HR" : {
        "number" :  16,
        "node" :  "H",
        "code" :  "HR",
        "name" :  "Croatia",
        "long_name" :  "Hrvatska (Croatia)",
        "code2" :  "HR",
        "cgm" :  False,
        "pslf_code" :  11,
        "pslf_name" :  "Chorvatsko",
    },
    "HU" : {
        "number" :  15,
        "node" :  "M",
        "code" :  "HU",
        "name" :  "Hungary",
        "long_name" :  "Magyarorszag (Hungary)",
        "code2" :  "H",
        "cgm" :  False,
        "pslf_code" :  1,
        "pslf_name" :  "Madarsko",
    },
    "CH" : {
        "number" :  7,
        "node" :  "S",
        "code" :  "CH",
        "name" :  "Switzerland",
        "long_name" :  "Schweiz (Switzerland)",
        "code2" :  "CH",
        "cgm" :  False,
        "pslf_code" :  15,
        "pslf_name" :  "Svajciarsko",
    },
    "IT" : {
        "number" :  17,
        "node" :  "I",
        "code" :  "IT",
        "name" :  "Italy",
        "long_name" :  "Italia (Italy)",
        "code2" :  "I",
        "cgm" :  False,
        "pslf_code" :  19,
        "pslf_name" :  "Taliansko",
    },
    "KS" : {
        "number" :  39,
        "node" :  "_",
        "code" :  "KS",
        "name" :  "Kosovo",
        "long_name" :  "Kosovo",
        "code2" :  "KS",
        "cgm" :  False,
        "pslf_code" :  39,
        "pslf_name" :  "Kosovo",
    },
    "LT" : {
        "number" :  19,
        "node" :  "6",
        "code" :  "LT",
        "name" :  "Lithuania",
        "long_name" :  "Lietuva (Lithuania)",
        "code2" :  "LT",
        "cgm" :  False,
        "pslf_code" :  37,
        "pslf_name" :  "Litva",
    },
    "LU" : {
        "number" :  18,
        "node" :  "1",
        "code" :  "LU",
        "name" :  "Luxemburg",
        "long_name" :  "Luxembourg (Luxemburg)",
        "code2" :  "L",
        "cgm" :  False,
        "pslf_code" :  31,
        "pslf_name" :  "Luxembursko",
    },
    "MA" : {
        "number" :  20,
        "node" :  "2",
        "code" :  "MA",
        "name" :  "Morocco",
        "long_name" :  "Maroc (Morocco)",
        "code2" :  "MA",
        "cgm" :  False,
        "pslf_code" :  27,
        "pslf_name" :  "Maroco",
    },
    "MD" : {
        "number" :  21,
        "node" :  "7",
        "code" :  "MD",
        "name" :  "Moldavia",
        "long_name" :  "Moldava (Moldavia)",
        "code2" :  "MD",
        "cgm" :  False,
        "pslf_code" :  38,
        "pslf_name" :  "Moldavsko",
    },
    "ME" : {
        "number" :  34,
        "node" :  "0",
        "code" :  "ME",
        "name" :  "Montenegro",
        "long_name" :  "Crna Gora (Montenegro)",
        "code2" :  "MNE",
        "cgm" :  False,
        "pslf_code" :  34,
        "pslf_name" :  "Cierna Hora",
    },
    "MK" : {
        "number" :  22,
        "node" :  "Y",
        "code" :  "MK",
        "name" :  "Makedonija",
        "long_name" :  "Makedonija (FYROM)",
        "code2" :  "MK",
        "cgm" :  False,
        "pslf_code" :  23,
        "pslf_name" :  "Macedonsko",
    },
    "NL" : {
        "number" :  24,
        "node" :  "N",
        "code" :  "NL",
        "name" :  "Netherlands",
        "long_name" :  "Nederland (Netherlands)",
        "code2" :  "NL",
        "cgm" :  False,
        "pslf_code" :  32,
        "pslf_name" :  "Holandsko",
    },
    "NO" : {
        "number" :  23,
        "node" :  "9",
        "code" :  "NO",
        "name" :  "Norway",
        "long_name" :  "Norge (Norway)",
        "code2" :  "N",
        "cgm" :  False,
        "pslf_code" :  36,
        "pslf_name" :  "Norsko",
    },
    "PL" : {
        "number" :  26,
        "node" :  "Z",
        "code" :  "PL",
        "name" :  "Poland",
        "long_name" :  "Polska (Poland)",
        "code2" :  "PL",
        "cgm" :  False,
        "pslf_code" :  3,
        "pslf_name" :  "Polsko",
    },
    "PT" : {
        "number" :  25,
        "node" :  "P",
        "code" :  "PT",
        "name" :  "Portugal",
        "long_name" :  "Portugal (Portugal)",
        "code2" :  "P",
        "cgm" :  False,
        "pslf_code" :  5,
        "pslf_name" :  "Portugalsko",
    },
    "RO" : {
        "number" :  27,
        "node" :  "R",
        "code" :  "RO",
        "name" :  "Romania",
        "long_name" :  "Romania (Romania)",
        "code2" :  "RO",
        "cgm" :  False,
        "pslf_code" :  9,
        "pslf_name" :  "Rumunsko",
    },
    "RS" : {
        "number" :  35,
        "node" :  "J",
        "code" :  "RS",
        "name" :  "Serbia",
        "long_name" :  "Srbija (Serbia)",
        "code2" :  "SRB",
        "cgm" :  False,
        "pslf_code" :  17,
        "pslf_name" :  "Srbsko",
    },
    "RU" : {
        "number" :  28,
        "node" :  "4",
        "code" :  "RU",
        "name" :  "Russia",
        "long_name" :  "Rossija (Russia)",
        "code2" :  "RUS",
        "cgm" :  False,
        "pslf_code" :  25,
        "pslf_name" :  "Rusko",
    },
    "SE" : {
        "number" :  29,
        "node" :  "8",
        "code" :  "SE",
        "name" :  "Sweden",
        "long_name" :  "Sverige (Sweden)",
        "code2" :  "S",
        "cgm" :  False,
        "pslf_code" :  35,
        "pslf_name" :  "Svedsko",
    },
    "SI" : {
        "number" :  31,
        "node" :  "L",
        "code" :  "SI",
        "name" :  "Slovenia",
        "long_name" :  "Slovenija (Slovenia)",
        "code2" :  "SLO",
        "cgm" :  False,
        "pslf_code" :  11,
        "pslf_name" :  "Chorvatsko",
    },
    "SK" : {
        "number" :  30,
        "node" :  "Q",
        "code" :  "SK",
        "name" :  "Slovakia",
        "long_name" :  "Slovensko (Slovakia)",
        "code2" :  "SK",
        "cgm" :  False,
        "pslf_code" :  4,
        "pslf_name" :  "Slovensko",
    },
    "TR" : {
        "number" :  32,
        "node" :  "T",
        "code" :  "TR",
        "name" :  "Turkey",
        "long_name" :  "Türkiye (Turkey)",
        "code2" :  "TR",
        "cgm" :  False,
        "pslf_code" :  33,
        "pslf_name" :  "Turecko",
    },
    "UA" : {
        "number" :  33,
        "node" :  "U",
        "code" :  "UA",
        "name" :  "Ukraine",
        "long_name" :  "Ukraina (Ukraine)",
        "code2" :  "UA",
        "cgm" :  False,
        "pslf_code" :  7,
        "pslf_name" :  "Ukrajina",
    },
    "UC" : {
        "number" :  37,
        "node" :  None,
        "code" :  "UC",
        "name" :  "Merged",
        "long_name" :  "UCTE-wide merged datasets without X nodes",
        "code2" :  "--",
        "cgm" :  True,
        "pslf_code" :  None,
        "pslf_name" :  None,
    },
    "UX" : {
        "number" :  38,
        "node" :  None,
        "code" :  "UX",
        "name" :  "Merged_wX",
        "long_name" :  "UCTE-wide merged datasets with X nodes",
        "code2" :  "--",
        "cgm" :  True,
        "pslf_code" :  None,
        "pslf_name" :  None,
    },
    "XX" : {
        "number" :  36,
        "node" :  "X",
        "code" :  "XX",
        "name" :  "X_Nodes",
        "long_name" :  "Fictitious border node",
        "code2" :  None,
        "cgm" :  False,
        "pslf_code" :  40,
        "pslf_name" :  "X-Nodes",
    },
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
  "comment": re.compile(r"##C\s*?(?P<version>\S.*?\S)?\s*?[\r\n]{1,2}(?P<text>(?:.*?[\r\n]{1,2})+?)(?=##|\Z)"),
  "Nodes": re.compile(r"##\s?Z\s?(?P<area>\w{2})[\r\n]{1,2}(?P<elements>(?:.*?[\r\n])+?)(?=##|\Z)"),
  "Node": re.compile(r"(?P<code__str>.{8}) (?P<name__str>.{12}) (?P<status__int>.{1}) (?P<node_type__int>.{1}) (?P<reference_voltage__float>.{6}) (?P<p_load__float>.{7}) (?P<q_load__float>.{7}) (?P<pg__float>.{7}) (?P<qg__float>.{7})(?: (?P<pg_min__float>.{7}))?(?: (?P<pg_max__float>.{7}))?(?: (?P<qg_min__float>.{7}))?(?: (?P<qg_max__float>.{7}))?(?: (?P<static_of_primary_control__float>.{5}))?(?: (?P<primary_control_PN__float>.{7}))?(?: (?P<sk3__float>.{7}))?(?: (?P<x_to_r__float>.{7}))?(?: (?P<plant_type__str>.{1}))?"),
  "Lines": re.compile(r"##L\s*?[\r\n]{1,2}(?P<elements>(?:.*?[\r\n])*?)(?=##|\Z)"),
  "Line": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<status__int>.{1}) (?P<r__float>.{6}) (?P<x__float>.{6}) (?P<b__float>.{8}) (?P<i_max__int>.{6})(?: (?P<name__str>.{12}))?"),
  "Transformers": re.compile(r"##T\s*?[\r\n]{1,2}(?P<elements>(?:.*?[\r\n])*?)(?=##|\Z)"),
  "Transformer": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<status__int>.{1}) (?P<v1__float>.{5}) (?P<v2__float>.{5}) (?P<sn__float>.{5}) (?P<r__float>.{6}) (?P<x__float>.{6}) (?P<b__float>.{8}) (?P<g__float>.{6}) (?P<i_max__int>.{6})(?: (?P<name__str>.{12}))?"),
  "Regulations": re.compile(r"##R\s*?[\r\n]{1,2}(?P<elements>(?:.*?[\r\n])*?)(?=##|\Z)"),
  "Regulation": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<phase_delta_u__float>.{5}) (?P<phase_taps__int>.{2}) (?P<phase_tap__int>.{3})(?: (?P<phase_u__float>.{5}))?(?: (?P<angle_delta_u__float>.{5}))?(?: (?P<angle_phi__float>.{5}))?(?: (?P<angle_taps__int>.{2}))?(?: (?P<angle_tap__int>.{3}))?(?: (?P<angle_p__float>.{5}))?(?: (?P<angle_type__str>.{4}))?"),
  "Parameters": re.compile(r"##TT\s*?[\r\n]{1,2}(?P<elements>(?:.*?[\r\n])*?)(?=##|\Z)"),
  "Parameter": re.compile(r"(?P<node1__str>.{8}) (?P<node2__str>.{8}) (?P<order_code__str>.{1}) (?P<tap__int>.{3}) (?P<r__float>.{6}) (?P<x__float>.{6}) (?P<delta_u__float>.{5}) (?P<alfa__float>.{5})"),
  "Schedules": re.compile(r"##E\s*?[\r\n]{1,2}(?P<elements>(?:.*?[\r\n]?)*?)(?=##|\Z)"),
  "Schedule": re.compile(r"(?P<country1__str>.{2}) (?P<country2__str>.{2}) (?P<schedule__float>.{7})(?: (?P<comments__str>.{12}))?")
}



uct_export = {
    "Node": {
        "code": 8, "name": 12, "status": 1, "node_type": 1, "reference_voltage": 6, "p_load": 7, "q_load": 7, "pg": 7, "qg": 7, "pg_min": 7, "pg_max": 7, "qg_min": 7, "qg_max": 7, "static_of_primary_control": 5, "primary_control_PN": 7, "sk3": 7, "x_to_r": 7, "plant_type": 1
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