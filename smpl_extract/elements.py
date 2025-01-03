from dataclasses import dataclass
from dataclasses import fields
from typing import ClassVar
from typing import List
from typing import Optional

from smpl_extract.base import Element
from smpl_extract.info import InfoTree
from smpl_extract.info import Printable
from smpl_extract.util.dataclass import itemize_general
from smpl_extract.util.dataclass import ItemT


@dataclass
class LeafElement(Element):
    _is_leaf: ClassVar[bool] = True


    def is_public_field(
            self, 
            item_name: str, 
            excluded_keys: Optional[List[str]] = None
    ) -> bool:
        if len(item_name) <= 0:
            return False
        if item_name[0] == "_":
            return False
        if excluded_keys is not None:
            if item_name in excluded_keys:
                return False
        return True


    def itemize(self) -> ItemT:
        DEFAULT_EXCLUDE = [
            "name",
            "path",
            "type_id",
            "type_name",
            "safe_name",
            "export_name"
        ]
        items_dict = {
            k.name: getattr(self, k.name) 
            for k in fields(self) 
            if self.is_public_field(k.name, DEFAULT_EXCLUDE)
        }
        result = itemize_general(items_dict)
        return result


    def get_info(self) -> Printable:
        header = (self.safe_name, " "*2, self.type_name)
        items = self.itemize()
        result = InfoTree(header, items)
        return result

