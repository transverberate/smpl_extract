from dataclasses import dataclass
from io import StringIO
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Tuple

from smpl_extract.base import Printable
from smpl_extract.util.dataclass import ItemT


class InfoTable(Printable):


    def __init__(
            self,
            header: Tuple[str, ...],
            rows: List[Tuple[str, ...]],
            column_width = 20,
            column_delimiter = " "
    ) -> None:
        self.header = header
        self.rows = rows
        self.column_width = column_width
        self.column_delimiter = column_delimiter


    def print_table(self):

        # if empty
        if len(self.rows) <= 0:
            result = "(*empty*)"
            return result

        str_buffer = StringIO(newline="\n")

        # calc total number of columns and the widths of each
        num_columns = 0
        column_widths: Mapping[int, int] = {}
        rows = self.rows + [self.header]
        for row in rows:
            for i, column_value in enumerate(row):
                # total number of cols
                if i + 1 > num_columns:
                    num_columns = i + 1
                # width of ith column
                width = len(column_value)
                if i not in column_widths.keys():
                    column_widths[i] = max(width, self.column_width)
                elif width > column_widths[i]:
                    column_widths[i] = width
        
        # total width is sum of column widths and the number of delimiters
        total_width = sum(column_widths.values()) + num_columns - 1
        

        def make_line(
                row: Tuple[str, ...], 
                column_widths: Mapping[int, int] = column_widths
        )->str:
            result = self.column_delimiter.join(map(
                lambda i: row[i].ljust(column_widths[i]), 
                range(len(row))
            ))
            return result


        # print the table
        str_buffer.write(make_line(self.header) + "\n")  # header
        str_buffer.write(("-" * total_width) + "\n")  # divider
        for row in self.rows:
            str_buffer.write(make_line(row) + "\n")

        result = str_buffer.getvalue()
        return result


    def to_string(self) -> str:
        result = self.print_table()
        return result


class InfoTree(Printable):


    def __init__(
            self,
            header: Tuple[str, ...],
            items: ItemT,
            total_width = 80,
            delimiter = " ",
            max_rows = 300
    ) -> None:
        self.header = header
        self.items = items
        self.total_width = total_width
        self.delimiter = delimiter
        self.max_rows = max_rows


    def print_tree(self):
        
        
        @dataclass
        class RowEntry:
            content: Tuple[str, ...] = ("", )
            depth: int = 0
            is_divider: bool = False


        row_entries: Sequence[RowEntry] = []


        def build_inner(item, depth=0, prev_key="", row_entries=row_entries):

            if isinstance(item, Sequence) or isinstance(item, Mapping):

                if isinstance(item, Sequence):
                    kv_pair = (
                        ("".join((prev_key, f"[{str(i)}]")), value)
                        for i,value in enumerate(item)
                    )
                else:
                    kv_pair = item.items()

                for key, value in kv_pair:
                        content = [f"{key}:"]
                        if isinstance(value, str):
                            content.append(str(value))
                        elif len(value) == 0:
                            content.append("None")
                        row_entries.append(RowEntry(tuple(content), depth))
                        # expand value
                        if not isinstance(value, str):
                            build_inner(
                                value, 
                                depth=(depth + 1), 
                                prev_key=key, 
                                row_entries=row_entries
                            )


        row_entries.append(RowEntry(tuple(self.header)))
        row_entries.append(RowEntry(is_divider=True))  # divider
        build_inner(self.items)  # fill row_entries

        str_buffer = StringIO(newline="\n")
        # print tree
        for i, row in enumerate(row_entries):
            if i > self.max_rows:
                str_buffer.write("\n")
                str_buffer.write(f"(...) exceeded {self.max_rows} lines\n")
                break
            if row.is_divider:
                result = "-" * self.total_width
                str_buffer.write(result + "\n")
                continue
            
            column_values = ((" ", ) * row.depth) + row.content 
            result = self.delimiter.join(column_values)
            if len(result) > self.total_width:
                result = result[0:self.total_width-3] + "..." 
            str_buffer.write(result + "\n")
        
        result = str_buffer.getvalue()
        return result


    def to_string(self) -> str:
        result = self.print_tree()
        return result

