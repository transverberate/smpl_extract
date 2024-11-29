# smpl_extract

A python library/tool for extracting patches and samples from various 
sampler/audio disc image formats.

## Supported Formats
### Source Types
- AKAI SX000 Disk Images
- Roland S-7xx Disk Images
- CDDA Data (Compact Disc Digital Audio) (requires `.cue`)

### Destination Types
- `.wav` samples

### Recognized Container Formats
| Format              	|                  Typical Extension(s)          	|
|---------------------	|:---------------------------------------------:	|
| Raw Data            	| `.img`, `.bin`, and `.iso` (not a *true* iso) 	|
| MODE1/2352 Raw Data 	|               *same as* `Raw Data`              |
| Cue sheet           	|               `.bin`/`.cue` pair              	|
| Alcohol 120         	|               `.mdf` and `.mds`               	|


## Installation
### Prerequisites
This toolset requires [Python 3](https://www.python.org/download/releases/3.0/)
to be installed and added to the user's `PATH`. 
Often times, installing python will not automatically add these programs to the system `PATH`. 
Searching Google for questions like 'how to add python to my PATH' etc. usually yields good
explanations on this process.

To confirm `python` is in your system's PATH, open an instance of command prompt and 
type `python --version` (sometimes it will be installed as `python3`, in which case - 
every time `python` is encountered in this document, it should be replaced with python3). 
If present, python should respond with its version number.

### Installing
Download the contents of this repo and extract them to a convenient place on your machine. 
Open an instance of command prompt and navigate to the location you extracted the repo. 
You should now be in the folder with `setup.py` and the sample `smpl_extract` directory. 
Enter the command,

```
python -m pip install cython
```

to install Cython to your python package library. 

[Cython](https://cython.org/) is needed to compile the (cpu intensive) filtering algorithms (see `smpl_extract/filters/*.pyx`)
as well as the [numpy](https://numpy.org/) library used by this tool.

Cython (and other `setuptools` extensions) requires a `c compiler`.
This is *usually* not an issue, but you may be prompted to download one
if none are found on your system.
The [GNU Compiler Collection (GCC)](https://gcc.gnu.org/) is generally a good choice for an 
out-of-the-box `c compiler`.

Next, enter the command the command

```
python -m pip install numpy
```

to install numpy to your python package library.

Next, enter the command (note the period!),

```
python -m pip install .
```

to install `smpl_extract` to your python package library.

Finally, confirm that `smpl_extract` has been installed properly by entering the command,

```
python -m smpl_extract --help
```

If successfully installed, `smpl_extract` should respond with an explanation of its command usage.


### Updating
To update these scripts having already previously installed an older version, 
download the latest version from the github repo, open a command prompt/shell window in the directory 
in which you downloaded the repo and run the command (note the period!),

```
python -m pip install .
```

## Usage as a toolset

The smpl_extract toolset is provided as a command-line utility
capable of executing a series of predefined commands.
The basic structure for calling a `smpl_extract` command is

```
python -m smpl_extract [command] [args …]
```



- `command`: The command/action for `smpl_extract` to execute. 
             The current commands provided are `ls` and `export_wav`.
- `args`: A *list* of one or more arguments that will be supplied 
          to the preceding command.

To display *help* for a particular command, call the command followed 
by the `-h` (help) flag.

```
python -m smpl_extract [command] -h
```

## The `ls` command
The `ls` (list) command lists the contents/info of a given path/file 
within an disc image. This command has the following form

```
python -m smpl_extract ls [image_file] [internal_path]
```

- `image_file`: The path to the file containing the disc image on your operating system -
                either absolute or relative to the current working directory. 
                (e.g., `"./my images/akai_s300_1.iso"` or `"/home/foo/media/trk5001.cue"`, etc.).
- `internal_path`: The path *within* the disc image. 
                   This path has the form `"<dir1>/<dir2>/<file>"`.
                   If this path is a `file` (i.e., a `sample`, `patch`, etc.), the information
                   available for that file will be displayed as plain-text.
                   If this path is a `directory` (e.g., partitions/volumes in an AKAI image, etc.), 
                   the contents of that directory will be listed.
                   If this path is empty, the root entries of the disk (e.g., the `tracks` of a 
                   CDDA bin/cue) will be listed.


## The `export` command
The `export` command of this toolset exports all the samples of a disc image to `.wav` files
following the 'directory' structure of the disc image.
This command has the following form

```
python -m smpl_extract export [image_file] [-f export_format] [-d destination]
```

- `image_file`: The path to the file containing the disc image on your operating system -
                either absolute or relative to the current working directory. 
                (e.g., `"./my images/akai_s300_1.iso"` or `"/home/foo/media/cd_img"`, etc.).
- `export_format`: The output format of the extracted samples. Currently only accepts `wav`.
- `destination`: The destination directory for the exported samples. The samples will be exported in
                 a directory structure which mirrors the structure of the disc image. The default 
                 destination is the current working directory.


## Examples
### Exploring the contents of a CDDA image
CDDA (Compact Disk Digital Audio) images are typically distributed as a set of files:
a disc image `.bin` and a *cue sheet* `.cue`.
The *cue sheet* specifies the type and location of *tracks* in the `.bin` disc image.
These *tracks* can encode raw data streams, but in CDDA, they encode stereo audio 
(and occasionally various meta-data).  


#### Listing the tracks in a CDDA image
Consider a disc image `trk5005.bin` with the corresponding `trk5005.cue` both located in the 
working directory. This CDDA image contains 6 tracks. Listing the tracks of the CDDA image is
accomplished by calling the following command

```
python -m smpl_extract ls "./trk5005.cue"
```

which prints the result

```
Item                 Type
-----------------------------------------
Example Track 1      CD Audio Track      
Example Track 2      CD Audio Track      
Example Track 3      CD Audio Track
Example Track 4      CD Audio Track
Example Track 5      CD Audio Track
Example Track 6      CD Audio Track
```

**Note**: that this command was called on `trk5005.cue`, not `trk5005.bin`. This is because
the cue sheet defines the locations of track data within the `.bin`. This is critical
for CDDA formats (and potentially others) - so when a bin/cue pair is provided it is generally
good practice to reference the `.cue` file when executing commands.


### Exploring the contents of an AKAI Image
AKAI images are organized into three nested layers: *partitions*, *volumes*, and *files*. 
At the top level, an image is broken into *partitions*. These partitions are assigned 
letters (e.g., `A` `B` `C` `D` etc.). Each partition contains a variable number of 
*volumes*. Each volume has a *name* (typically these names categorize the contents of the volume.
Each volume contains a variable number of *files*. Files can contain *sample data*, 
*program data*, or other *metadata* the sampler uses to synthesize output. Each file has a 
*name* and a *type*. For more information on the structure of an AKAI image see the 
corresponding section.


#### Listing the partitions in an image
Consider a disc image `cool_samples.iso` located in the folder `imgs` (relative to the 
working directory). This image contains four partitions. Listing the partitions of the 
image is accomplished by calling the command

```
python -m smpl_extract ls "./imgs/cool_samples.iso"
```

which prints the result

```
Item                Type
----------------------------------------
A:                  AKAI Partition
B:                  AKAI Partition
C:                  AKAI Partition
D:                  AKAI Partition

```

#### Listing the volumes in a partition
Continuing with the `cool_samples.iso` example, suppose that partition `A` of the image has three 
volumes. Listing the volumes within this partition is accomplished by calling the command

```
python -m smpl_extract ls "./imgs/cool_samples.iso" "A"
```

which prints the result

```
Item                Type
----------------------------------------
INSTANT INST        S1000 Volume
SAWTOOTH SET        S1000 Volume
BASS SET            S1000 Volume

```

#### Listing the files in a volume
Continuing with the `cool_samples.iso` example, suppose that the volume `A/SAWTOOTH SET` has nine 
sample files and one program patch. Listing the files within this volume is accomplished by 
calling the command

```
python -m smpl_extract ls "./imgs/cool_samples.iso" "A/SAWTOOTH SET"
```

which prints the result

```
Item                Type
----------------------------------------
SAWSML -V  A        S1000 Program
SAWSML 1S  L        S1000 Sample
SAWSML 1S  R        S1000 Sample
PHASE   14M         S1000 Sample
PHASE   24M         S1000 Sample
DISTR PH 1M         S1000 Sample
144 CMB A  L        S1000 Sample
144 CMB A  R        S1000 Sample
CHSAW  1S  L        S1000 Sample
CHSAW  1S  R        S1000 Sample

```

#### Listing properties of a sample/program file
Continuing with the `cool_samples.iso` example, listing the properties of the `A/SAWTOOTH 
SET/SAWSML 1S  L` is accomplished by calling the command (take care to include the proper number of 
spaces in the file/volume names)

```
python -m smpl_extract ls "./imgs/cool_samples.iso" "A/SAWTOOTH SET/SAWSML 1S  L"
```

which prints the result

```
SAWSML 1S  L  S1000 Sample
--------------------------------------------------------------------------------
name: SAWSML 1S  L
sample_type: S1000 Sample
sample_rate: 48000
bytes_per_sample: 2
start_sample: 0
end_sample: 143943
note_pitch: B5
pitch_cents: 19.01960784313725
pitch_semi: 1
loop_type: Loop in release
loop_entries:
  loop_entries[0]:
    loop_start: 107991
    loop_end: 143943
    loop_duration: 9999
    repeat_forever: True

```

### Exploring the contents of a Roland S-7xx image
Roland S-7xx images are organized into 5 nested layers: `volumes`, `performances`,
`patches`, `partials`, and `samples`. This toolset abstracts the 3 most granular layers
(`patches`, `partials`, and `samples`) into the `program` and `sample` abstractions. 
The `program` abstraction encodes the program/patch settings contained at the `patch`
and `partial` levels while the `sample` abstraction encodes the sample/wave data.


#### Listing the volumes in an image
Consider a Roland S-770 disc image `s770example.bin` located in the folder `imgs` (relative to the 
working directory). This image contains four volumes. Listing the volumes of the 
image is accomplished by calling the command

```
python -m smpl_extract ls "./imgs/s770example.bin"
```

which prints the result

```
Item                 Type
-----------------------------------------
BTS:Basic Grooves    Roland S-7xx Volume
BTS:Fluid Beats      Roland S-7xx Volume
PRC:Standard Set     Roland S-7xx Volume
DEM:Latest Release   Roland S-7xx Volume
```

#### Listing the performances in a volume
Continuing with the `s770example.bin` example, suppose that the volume
`BTS:Basic Grooves` has 3 performances.
Listing the performances within this volume is accomplished by 
calling the command

```
python -m smpl_extract ls "./imgs/s770example.bin" "BTS:Basic Grooves"
```

which prints the result

```
Item                 Type
---------------------------------------------
80:Breakout          Roland S-7xx Performance
100:Swing            Roland S-7xx Performance
112:Classic          Roland S-7xx Performance
```


#### Listing the programs and samples in a performance
Continuing with the `s770example.bin` example, suppose that performance
`80:Breakout` has 1 program and 2 samples.
Listing the program and samples within this performance is accomplished by 
calling the command

```
python -m smpl_extract ls "./imgs/s770example.bin" "BTS:Basic Grooves/80:Breakout"
```

which prints the result

```
Item                 Type
---------------------------------------------
80:-Breakout         Roland S-7xx Program
80:-Breakout L       Roland S-7xx Sample
80:-Breakout R       Roland S-7xx Sample
```

#### Listing properties of a sample/program file
Continuing with the `s770example.bin` example, listing the properties of the
sample `80:-Breakout L` is accomplished by calling the command

```
python -m smpl_extract ls "./imgs/s770example.bin" "BTS:Basic Grooves/80:Breakout/80:-Breakout L"
```

which prints the result

```
80:-Breakout L   Roland S-7xx Sample
--------------------------------------------------------------------------------
sample_mode: Mono
sampling_frequency: 44100
sustain_loop_enable: 0
sustain_loop_tune: 0
release_loop_tune: 0
original_key: C3
loop_mode: Forward End
start_sample:
  fine: 0
  address: 0
sustain_loop_start:
  fine: 0
  address: 0
sustain_loop_end:
  fine: 0
  address: 228667
release_loop_start:
  fine: 0
  address: 230412
release_loop_end:
  fine: 0
  address: 230424
```

### Extracting CDDA tracks as wav files
Consider a CDDA bin/cue pair `backup.bin` and `backup.cue`, located in the
folder `backups` (relative to the current working directory).
This CDDA image has 4 tracks

```
Best of times
All in a days work
Attack at dawn
Losing it all 
```

Extracting these tracks (as `.wav` files) to the folder `output`
(relative to the current working directory) is accomplished by calling the 
command

```
python -m smpl_extract export "./backups/backup.cue" -d "./output/"
```

which produces the following files

```
output/Best of times.wav
output/All in a days work.wav
output/Attack at dawn.wav
output/Losing it all.wav
```

**Note**: Be sure to reference the disk image by the `.cue` file when
calling commands. This is crucial for CDDA images provided as a
bin/cue pair and is a good practice generally. 


### Extracting AKAI samples as wav files
Consider an AKAI image, `example.iso`, located in the folder 
`imgs` (relative to the working directory). 
This image has the following structure (following the 
`<partition>/<volume>/<file>` notation introduced earlier)

```
A/SAW/SAMPL1
A/SAW/SAMPL2
A/SQUARE/LEAD2L
A/SQUARE/LEAD2R
B/SYNTH/BRASS1
B/SYNTH/BRASS2
```

Calling the command

```
python -m smpl_extract export "./imgs/example.iso" -d "./output/"
```

will produce the following file structure

```
output/A/SAW/SAMPL1.wav
output/A/SAW/SAMPL2.wav
output/A/SQUARE/LEAD2.wav
output/B/SYNTH/BRASS1.wav
output/B/SYNTH/BRASS2.wav
```

**Note**: The `LEAD2L` and `LEAD2R` mono samples have been merged into a 
stereo file `LEAD2.wav`. This is because samples whose names differ
by only a terminal `L` or `R` indicate the left and right (respectively)
channels of a single stereo sample. 


### Extracting Roland S-7xx samples as wav files
Extracting Roland S-7xx samples as `.wav`s can be accomplished 
following the same command syntax in the preceding AKAI section.
The directory structure of the exported `.wav`s has the form
`<volume>/<performance>/<sample>`.


## Project Structure

This project relies heavily on the [construct](https://github.com/construct/construct) library,
which supports declarative parsing and building of binary data. There is a bit of a learning
curve for this library, but its [readthedocs page](https://construct.readthedocs.io/en/latest/)
offers a good overview of the API and addresses some common use-cases.


## AKAI S3000 Format
### Background
Most AKAI image files are given the extension `.iso`. Typically, `.iso`s are thought of as a 
"raw binary dump" (or image) of an entire compact disc - agnostic of specific formatting. 
While this is technically true, most programs which read/mount/create ISOs expect the image 
to conform to a known formatting(usually [ISO 9660](https://en.wikipedia.org/wiki/ISO_9660) - 
the origin of the `.iso` extension), and indeed, most `.iso`s conform to such a format. 
AKAI disc images do not conform to ISO 9960 (or related formats) and are unreadable by disc image
libraries or applications. 

There are several commercial applications that are able to read and extract AKAI images, however, there 
were (at the time of initial development) few open-source alternatives. This python utility was 
developed to address this.
While the AKAI format was never publicly disclosed, it was reverse-engineered by 
[Paul Kellett](http://mda.smartelectronix.com/akai/akaiinfo.htm) and 
[Dr. Hiroyuki Ohsaki](https://lsnl.jp/~ohsaki/software/akaitools/S3000-format.html) - who 
both did so independent of one another. This utility was developed based off 
both their descriptions of the format.

### Format Overview
#### Units/Encoding 
On a granular level, an AKAI image is read and addressed in `8-bit` *bytes*. 
Multi-byte integers (`16-bit` and `32-bit`) are encoded *little-endian*. 
On a macro level (sector-level), an AKAI image is read and addressed in 8192-byte chunks called
*sectors*. The concept of partitioning discs into sectors is common across disc formats and is
usually leveraged as a unit of addressing across different filesystem specifications. As such, 
a proper AKAI image should be evenly divisible into an integer number of sectors. The main take-away 
from this section should be that there are two methods of addressing: addressing by byte, and 
addressing by sector.

#### Image Layers and Terminology
An AKAI image is divided in to three nested layers. At the topmost layer, the image is divided into 
*partitions*; each partition is divided into *volumes*; and each volume is divided into *files*.  
Note: the preceding names for each layer are just that - names. They *do not* indicate any 
particular formatting implied by similar names in other disc format specifications. For instance, 
in the context of other disc formats, what is called a *volume* can span multiple *partitions* - 
this is not the case (to my knowledge) for an AKAI image.

Another potential point of confusion is the use of the term *file*. I believe this term best 
describes this third layer of nesting. Trouble arises from the potential confusion around what 
are traditionally called a *filesystem* and a *file allocation table* (FAT). Analogous entities 
do exist for AKAI images; however, because of the layer at which these are specified 
(at each partition) and some additional nuances, the alternative terms *segment-map* and 
*segment allocation table*, respectively, are used. This will be explained in more detail shortly,
but it is worth introducing now.

#### Partitions
Partitions consist of a fixed-length *header* section, and a variable-length *data* section. 
All sector-level addressing contained within a partition is done with respect to the current
partition's starting address. The total partition size (in sectors) is specified in the 
partition's header, in addition to a list of *volume entries* which indicate the 
*name*, *type*, and *starting offset* (in sectors) of each volume contained within the partition. 

#### Segments and the Segment Allocation Table
Perhaps the most important portion of a partition's header is the *segment allocation table (SAT)*.
This table describes how sectors within the partition "flow" into one another. Suppose a large 
chunk of data (whose size exceeds the length of a sector) needs to be read somewhere within 
the current partition. Since at least two sectors of data are needed, the locations of this data 
will span across multiple sectors. However, the sectors containing the desired data are not 
necessarily placed consecutively in the AKAI image. 

As the stream-pointer approaches the boundary of a given sector it must know in advance which 
sector contains the rest of the data. This can be accomplished by specifying an ordered list of
*sector addresses* which link sectors containing contiguous data. An ordered collection of sectors
containing a contiguous stream of data is called a *segment*. Segments are addressed by the address 
of their first sector. The *segment allocation table* (SAT) gives lists of sector addresses that 
specify individual segments. The entire collection of segments is called a *segment map*. 
For additional clarification on this layout, search for information regarding 
*file allocation tables*.

Note that the SAT specifies the "flow" of all data within the partition. This data includes
the contents of volumes and their constituent files. Therefore, whenever the stream pointer 
reaches the boundary of a sector with a partition's data, it will jump to the beginning of the 
next sector in the current segment, wherever that may be. 

#### Volumes
Each volume consists of a fixed length *header* section and a variable-length *data* section.
The header consists of a list of file entries which specify the *name*, *type*, *size* and 
*segment address* of each file in the volume. There is no "directory" system for files; 
each file listed is simply a sub-element of the current volume. In this way, 
volumes of AKAI images function more or less as folders for files within a partition.

#### Files
At the lowest level of nesting are files which typically contain either *sample* or *program data*.
Of note is that the AKAI sample format does not inherently support stereo encoding within a 
single file. Rather, when stereo audio is required, two similarly named sample files will separately
contain the *left* and *right* channel data.

## Development and contributing
This tool-set is in active development and has only been rigorously tested in Windows 10. 
If a bug is found, please report it as an issue. Feature requests are welcome, but there is no 
guarantee I will be able to implement it.

## Support Me
`smpl_extract` is an open-source alternative for extracting audio samples from disc images.
If you like the work I've contributed to this project, you can support me by buying me a coffee!


[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/counselor.chip)

## License
Copyright (c) 2021-present Counselor Chip.
`smpl_extract` is free and open-source software licensed under the [MIT License](/LICENSE).

### Third Party Licenses
 - [numpy](https://github.com/numpy/numpy/blob/main/LICENSE.txt)
 - [construct](https://github.com/construct/construct/blob/master/LICENSE)
