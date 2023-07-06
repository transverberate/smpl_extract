meta:
  id: roland_s770
  file-extension: roland_s770
  endian: le

seq:

  # ID AREA: 0x200
  # RESERVED AREA: 0x600
  # PROGRAM AREA: 0x80000
  # FAT AREA: 0x20000

  - id: id_area
    type: id_area
    size: 0x200
    
  - id: reserved_area
    size: 0x600
    
  - id: program_text_area
    size: 0x80000
    
  - id: fat_area
    size: 0x20000

  - id: directory_area
    type: directory_area
    size: 0x6D000
  
  - id: parameter_area
    type: parameter_area
    size: 0x1A8000
  
  # - id: data_area
  #   type: u1
  #   repeat: eos

types:

  id_area:
    seq:
      - id: revision
        type: u4
        
      - id: s70_str       # 'S770 MR25A'
        size: 10
        type: str
        encoding: ascii
        
      - size: 2
      
      - id: empty_str       
        size: 15
        type: str
        encoding: ascii
      - size: 1
      
      - id: version_str       # 'S-770 Hard Disk  Ver. X.XX     '
        size: 31
        type: str  
        encoding: ascii
      - size: 1
      
      - id: copyright_str     # '    Copyright   Roland         '
        size: 31
        type: str  
        encoding: ascii
      - size: 1
      
      - size: 160
      
      - id: disk_name
        size: 16
        type: str
        encoding: ascii
        
      - id: disk_capacity
        type: u4
        
      - id: num_volumes
        type: u2
      - id: num_performances
        type: u2
      - id: num_patches
        type: u2
      - id: num_partials
        type: u2
      - id: num_samples
        type: u2
        
      - size: 226

  directory_entry:
    seq:
      - id: name 
        size: 16
        type: str
        encoding: ascii
      - id: file_type
        type: u1
        enum: file_type
      - id: file_attributes
        type: u1
      - id: forward_link_ptr
        type: u2
      - id: backward_link_ptr
        type: u2
      - id: link_id
        type: u2
      - id: reserved
        type: u4
      - id: fat_entry
        type: u2
      - id: num_clusters
        type: u2
        
  directory_list:
    params:
      - id: num_entries
        type: u4
    seq:
      - id: directories
        repeat: expr
        repeat-expr: num_entries
        type: directory_entry
        
  directory_area:
    seq:    
      - id: volume_directories
        size: 0x1000
        type: directory_list(0x80)
      - id: performance_directories
        size: 0x4000
        type: directory_list(0x200)
      - id: patch_directories
        size: 0x8000
        type: directory_list(0x400)
      - id: partial_directories
        size: 0x20000
        type: directory_list(0x1000)
      - id: sample_directories
        size: 0x40000
        type: directory_list(0x2000)
  
  part_level:
    meta:
      bit-endian: le
    seq:
      - id: level
        type: b7
      - id: is_on
        type: b1
      
        
  performance_parameter:
    seq:
      - id: performance_name
        size: 16
        type: str
        encoding: ascii
        
      - id: parts_patch_selection
        type: s1
        repeat: expr
        repeat-expr: 32
        
      - id: midi_channel_data
        type: u1
        repeat: expr
        repeat-expr: 16
        
      - id: parts_level
        type: part_level
        repeat: expr
        repeat-expr: 32
        
      - id: parts_zone_lower
        type: u1
        repeat: expr
        repeat-expr: 32
        
      - id: parts_zone_upper
        type: u1
        repeat: expr
        repeat-expr: 32
        
      - id: parts_fade_width_lower
        type: u1
        repeat: expr
        repeat-expr: 32
        
      - id: parts_fade_width_upper
        type: u1
        repeat: expr
        repeat-expr: 32
        
      - id: parts_program_change
        type: u2
      - id: parts_pitch_bend
        type: u2
      - id: parts_modulation
        type: u2
      - id: parts_hold_pedal
        type: u2
      - id: parts_bend_range
        type: u2
      - id: parts_midi_volume
        type: u2
      - id: parts_after_touch_switch
        type: u2
      - id: parts_after_touch_mode
        type: u2
      
      - id: velocity_curve_type_data
        type: u1
        repeat: expr
        repeat-expr: 16
        
    
  patch_parameter:
    seq:
      - id: patch_name
        size: 16
        type: str
        encoding: ascii

      - id: program_change_num
        type: u1
      - id: stereo_mix_level
        type: u1
      - id: total_pan
        type: u1
      - id: patch_level
        type: u1
      - id: output_assign_8
        type: u1  
      - id: priority
        type: u1
      - id: cutoff
        type: u1
      - id: velocity_sensitivity
        type: u1
      - id: octave_shift
        type: u1
      - id: coarse_tune
        type: u1
      - id: fine_tune
        type: u1
      - id: smt_ctrl_selection
        type: u1
      - id: smt_ctrl_sensitivity
        type: u1
      - id: out_assign
        type: u1
      - id: analog_feel
        type: u1
      - size: 1
      
      - id: keys_partial_selection
        type: u1
        repeat: expr
        repeat-expr: 88
      - size: 8
      
      - id: keys_assign_type
        type: u1
        repeat: expr
        repeat-expr: 88
      - size: 8
      
      - id: bender
        type: bender_section
      - id: after_touch
        type: after_touch_section
      - id: modulation
        type: modulation_section
      - size: 1
      - id: controller
        type: controller_section
        
      - size: 8
      
    types:
      bender_section:
        seq:
          - id: pitch_ctrl_up
            type: u1
          - id: pitch_ctrl_down
            type: u1
          - id: tva_ctrl
            type: u1
          - id: tvf_ctrl
            type: u1
    
    
      after_touch_section:
        seq:
          - id: pitch_ctrl
            type: u1
          - id: tva_ctrl
            type: u1
          - id: tvf_ctrl
            type: u1
          - id: lfo_rate_ctrl
            type: u1
          - id: lfo_pitch_ctrl
            type: u1
          - id: lfo_tva_depth
            type: u1
          - id: lfo_tvf_depth
            type: u1
            
      
      modulation_section:
        seq:
          - id: lfo_rate_ctrl
            type: u1
          - id: lfo_pitch_ctrl
            type: u1
          - id: lfo_tva_depth
            type: u1
          - id: lfo_tvf_depth
            type: u1
            
      
      controller_section:
        seq:
          - id: ctrl_num
            type: u1
          - id: pitch_ctrl
            type: u1
          - id: tva_ctrl
            type: u1
          - id: tvf_ctrl
            type: u1
          - id: lfo_rate_ctrl
            type: u1
          - id: lfo_pitch_ctrl
            type: u1
          - id: lfo_tva_depth
            type: u1
          - id: lfo_tvf_depth
            type: u1
            
  
  partial_parameter:
    seq:
      - id: partial_name
        size: 16
        type: str
        encoding: ascii
        
      - id: sample_1
        type: sample_section
      
      - size: 1
      - id: output_assign_8
        type: u1
      - id: stereo_mix_level
        type: u1 
      - id: partial_level
        type: u1 
      - id: output_assign_6
        type: u1 
        
      - id: sample_2
        type: sample_section
        
      - size: 1
      - id: pan
        type: u1
      - id: course_tune
        type: u1 
      - id: fine_tune
        type: u1 
      - id: breath_cntrl
        type: u1 
        
      - id: sample_3
        type: sample_section
      - size: 5
      - id: sample_4
        type: sample_section
        
      - id: tvf
        type: tvf_section
        
      - id: tva
        type: tva_section
        
      - id: lfo_generator
        type: lfo_section
        
      - size: 7
        

    types:

      tvf_section:
        seq:
          - id: filter_mode
            type: u1
          - id: cutoff
            type: u1
          - id: resonance
            type: u1        
          - id: velocity_curve_type
            type: u1
          - id: velocity_curve_ratio
            type: u1
          - id: time_velocity_sens
            type: u1
          - id: cutoff_velocity_sens
            type: u1
            
          - id: levels
            type: u1
            repeat: expr
            repeat-expr: 4
            
          - id: times
            type: u1
            repeat: expr
            repeat-expr: 4
            
          - id: env_tvf_depth
            type: u1
          - id: env_pitch_depth
            type: u1
          - id: tvf_kf_point
            type: u1
          - id: env_time_kf
            type: u1
          - id: env_depth_kf
            type: u1
          - id: cutoff_kf
            type: u1
  

      tva_section:
        seq:
          - id: velocity_curve_type
            type: u1
          - id: velocity_curve_ratio
            type: u1
          - id: time_velocity_sensitivity
            type: u1
            
          - id: levels
            type: u1
            repeat: expr
            repeat-expr: 4
            
          - id: times
            type: u1
            repeat: expr
            repeat-expr: 4
            
          - size: 1
          
          - id: tva_kf_point
            type: u1
          - id: env_time_kf
            type: u1
            
          - size: 1
  
          - id: level_kf
            type: u1        
        
      
      lfo_section:
        seq:
          - id: wave_form
            type: u1 
          - id: rate
            type: u1 
          - id: key_sync
            type: u1 
          - id: delay
            type: u1 
          - id: delay_kf
            type: u1 
          - id: detune
            type: u1 
          - id: pitch
            type: u1 
          - id: tvf_modulation_depth
            type: u1 
          - id: tva_modulation_depth
            type: u1 
            
      
      sample_section:
        seq:
          - id: sample_selection
            type: u2
          - id: pitch_kf
            type: u1
          - id: sample_level
            type: u1
          - id: pan
            type: u1
          - id: coarse_tune
            type: u1
          - id: fine_tune
            type: u1
          - id: smt_velocity_lower
            type: u1
          - id: smt_fade_with_lower
            type: u1
          - id: smt_velocity_upper
            type: u1
          - id: smt_fade_with_upper
            type: u1
          
   
  sample_parameter:
    seq:
      - id: sample_name
        size: 16
        type: str
        encoding: ascii
        
      - id: start_sample
        type: sample_point
      - id: sustain_loop_start
        type: sample_point
      - id: sustain_loop_end
        type: sample_point
      - id: release_loop_start
        type: sample_point
      - id: release_loop_end
        type: sample_point
        
      - id: loop_mode
        type: u1
      - id: sustain_loop_enable
        type: u1
      - id: sustain_loop_tune
        type: u1
      - id: release_loop_tune
        type: u1
      - id: seg_top
        type: u2
      - id: seg_length
        type: u2
      - id: sample_mode
        type: u1
      - id: original_key
        type: u1
        
      - size: 2
      
    types:
      sample_point:
        seq:
          - id: raw_value
            type: u4
        instances:
          fine: 
            value: raw_value & 0xff
          address:
            value: raw_value >> 8
  
  volume_entry:
    seq:
      - id: name
        size: 0x10
        type: str
        encoding: ascii
      - size: 16
      - id: performance_ptrs
        type: u2
        repeat: expr
        repeat-expr: 64
      - size: 0x60


  volume_entries:
    seq: 
      - id: volume_entries
        type: volume_entry
        repeat: expr
        repeat-expr: 128
        
  performance_entry:
    seq:
      - id: performance_parameter
        type: performance_parameter
        
      - id: patch_list
        type: s2
        repeat: expr
        repeat-expr: 32
        
      - size: 0xC0
    
    
  performance_entries:
    seq: 
      - id: performance_entries
        type: performance_entry
        repeat: expr
        repeat-expr: 512
        
        
  patch_entry:
    seq:
      - id: patch_parameter
        type: patch_parameter
        
      - id: partial_list
        type: s2
        repeat: expr
        repeat-expr: 88
        
      - size: 0x50
    
  
  patch_entries:
    seq:
      - id: patch_entries
        type: patch_entry
        repeat: expr
        repeat-expr: 1024
        
        
  partial_entry:
    seq:
      - id: partial_parameter
        type: partial_parameter
        

  partial_entries:
    seq:
      - id: partial_entries
        type: partial_entry
        repeat: expr
        repeat-expr: 4096
        

  sample_entry:
    seq:
      - id: sample_parameter
        type: sample_parameter
        

  sample_entries:
    seq:
      - id: sample_entries
        type: sample_entry
        repeat: expr
        repeat-expr: 8192
  
        
  parameter_area:
    seq:
      - id: volume_entries
        type: volume_entries
        size: 0x8000
      - id: performance_entries
        type: performance_entries
        size: 0x40000
      - id: patch_entries
        type: patch_entries
        size: 0x80000
      - id: partial_entries
        type: partial_entries
        size: 0x80000
      - id: sample_entries
        type: sample_entries
        size: 0x60000
            
        
enums:
  file_type:
    0x40: volume
    0x41: performance
    0x42: patch
    0x43: partial
    0x44: sample