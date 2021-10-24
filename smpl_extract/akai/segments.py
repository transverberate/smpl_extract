from typing import Dict, List, Tuple, Union


class RequestedInvalidSector(Exception):
    pass


class SegmentAllocationTable:


    RESERVED_FLAG_STD = 0x4000
    RESERVED_FLAG_V2  = 0x8000
    FREE_FLAG         = 0x0000
    EOF_FLAG          = 0xc000


    def __init__(
            self,
            size: int = 0,
            sector_links: List[Tuple[int, bool]] = None
    ) -> None:
        self.size = size
        self.sector_links = sector_links or []

    
    def get_path(
            self, 
            starting_sector: int
    )->Union[List[int], None]:

        path = []
        current_sector = starting_sector

        loop_cnt = 0
        while loop_cnt < self.size:
            if current_sector >= len(self.sector_links):
                raise RequestedInvalidSector

            path.append(current_sector)
            next_sector, is_path_end = self.sector_links[current_sector]

            if is_path_end:
                break
            current_sector = next_sector

        if loop_cnt >= self.size:
            raise Exception("Broken FAT. Loop? Sector path exceeds size?")

        return path


    @classmethod
    def from_raw_stream(
            cls, 
            block: List[int]
    )->'SegmentAllocationTable':
        size = len(block)
        sector_links: List[Tuple[int, bool]] = [(0, True)] * size
        dirty_flags = [False] * size

        def add_to_sector_links(path: List[int]):
            path_iter = iter(path)
            prev_link = next(path_iter)

            for link in path_iter:
                sector_links[prev_link] = (link, False)
                prev_link = link

            sector_links[prev_link] = (0, True)

        continue_flag = True
        previous_sector_was_directory = True
        for i in range(size):
            if not dirty_flags[i]:

                path = []
                subpath_index = i
                
                continue_flag = True 
                while continue_flag:
                    if subpath_index >= size:
                        continue_flag = False
                        break

                    value_current = block[subpath_index]
                    current_sector_is_directory = value_current in (
                            cls.RESERVED_FLAG_STD, 
                            cls.RESERVED_FLAG_V2
                    )

                    if not current_sector_is_directory and previous_sector_was_directory:
                        add_to_sector_links(path)
                        previous_sector_was_directory = False
                        continue_flag = False
                        break
                    elif value_current == cls.FREE_FLAG or \
                            (value_current < size and dirty_flags[value_current]):

                        continue_flag = False
                        dirty_flags[subpath_index] = True
                        previous_sector_was_directory = False
                        break 
                    elif value_current == cls.EOF_FLAG:
                        path.append(subpath_index)
                        add_to_sector_links(path)
                        dirty_flags[subpath_index] = True
                        previous_sector_was_directory = current_sector_is_directory
                        continue_flag = False
                        break
                    
                    dirty_flags[subpath_index] = True
                    path.append(subpath_index)
                    if not current_sector_is_directory:
                        subpath_index = value_current
                    else:
                        subpath_index += 1
                    previous_sector_was_directory = current_sector_is_directory
                    
            else:
                pass

        res = cls(size, sector_links)
        return res
        
