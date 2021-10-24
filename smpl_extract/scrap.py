def main():
    
    # loops = []
    # for i in range(4):
    #     loop = WavLoopStruct(
    #         cue_id=int.from_bytes(f"loo{chr(ord('1')+i)}".encode("ascii"), "little"),
    #         loop_type=WavLoopType.FORWARD,
    #         start_byte=0,
    #         end_byte=0x1200+0x20*i,
    #         fraction=0,
    #         play_cnt=0
    #     )
    #     loops.append(loop)
    # pass
    # dd = WavSampleChunkStruct(
    #         manufacturer=0, 
    #         product=0,
    #         sample_period=44800,
    #         midi_note=0,
    #         pitch_fraction=0,
    #         smpte_format=SmpteFormat.NONE,
    #         smpte_offset=0,
    #         sample_loops=loops,
    #         sampler_data=b""
    #     )
    # q = dd.build()
    # pass


    image = AkaiImage("C:\\Users\\17639\\Desktop\\VirtShared\\heart of asia\\Spectrasonics - Heart of Asia CD1.iso")
    image.partitions
    volumes = list(image.partitions.values())[0].volumes
    files = list(volumes.values())[0].files
    sample_files = list([files["CHNLG  1S  L"], files["CHNLG  1S  R"]]) # files.values())[0]
    # item = image.get_node_from_path("A/SPACE DOCK")
    # if hasattr(item, "children"):
    #     for child in item.children.values():
    #         print(child.name)
    # pass
    with open("test.wav", "wb") as f:
        write_wave_from_samples(image.file, f, sample_files)
    pass