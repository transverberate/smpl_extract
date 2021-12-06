# smpl_extract

A python library/tool for extracting programs and samples from AKAI S3000 images.

## Installation
### Prerequisites
This toolset requires [Python 3](https://www.python.org/download/releases/3.0/)
to be installed and added to the user's `PATH`. 
Often times, installing python will not automatically add these programs to the system `PATH`. 
Searching Google for questions like 'how to add python to my PATH' etc. usually yields good explanations 
on this process.

To confirm `python` is in your system's PATH, open an instance of command prompt and type `python --version` 
(sometimes it will be installed as `python3`, in which case - every time `python` is encountered in this 
document, it should be replaced with python3). If present, python should respond with its version number.

### Installing
Download the contents of this repo and extract them to a convenient place on your machine. 
Open an instance of command prompt and navigate to the location you extracted the repo. 
You should now be in the folder with `setup.py` and the sample `smpl_extract` directory. Enter the command,

```
python -m pip install cython
```

to install the [Cython](https://cython.org/) to your python package library. 
This is needed to compile the [numpy](https://numpy.org/) library that this library/tool makes use of.

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

## Importing as a library 

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


### Exploring the contents of an AKAI Image


AKAI images are organized into three nested layers: *partitions*, *volumes*, and *files*. 
At the top level, an image is broken into *partitions*. These partitions are assigned 
letters (e.g., `A` `B` `C` `D` etc.). Each partition contains a variable number of 
*volumes*. Each volume has a *name* (typically these names categorize the contents of the volume.
Each volume contains a variable number of *files*. Files can contain *sample data*, 
*program data*, or other *metadata* the sampler uses to synthesize output. Each file has a 
*name* and a *type*. For more information on the structure of an AKAI image see the 
[corresponding section](#akia-s3000-format).

The `ls` command of this toolset lists the contents of a given path within an AKAI image. 
This command has the following form

```
python -m smpl_extract ls [image_file] [internal_path]
```

- `image_file`: The path to the file containing the AKAI image on your operating system - either 
                absolute or relative to the current working directory. 
                (e.g., `"./my images/akai_s300_1.iso"` or `"/home/foo/media/akai_img"`, etc.).
- `internal_path`: The path *within* the AKAI image containing the contents to be listed. 
                   This path has the form `"<partition>/<volume>/<file>"`. If this path is empty, 
                   the `ls` command will list the partitions in the AKAI image.

#### Listing the partitions in an image

Consider a disk image `cool_samples.iso` located in the folder `imgs` (relative to the working directory). 
This image contains four partitions. Listing the partitions of the image is accomplished by calling the 
command

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
sample files. Listing the files within this volume is accomplished by calling the command

```
python -m smpl_extract ls "./imgs/cool_samples.iso" "A/SAWTOOTH SET"
```

which prints the result

```
Item                Type
----------------------------------------
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

#### Listing properties of a sample file
Continuing with the `cool_samples.iso` example, listing the properties of the `A/SAWTOOTH 
SET/SAWSML 1S  L` is accomplished by calling the command (take care to include the proper number of 
spaces in the file/volume names)

```
python -m smpl_extract ls "./imgs/cool_samples.iso" "A/SAWTOOTH SET/SAWSML 1S  L"
```

which prints the result

```
Sample
----------------------------------------
Name                SAWSML 1S  L
Type                S1000 Sample
Sample rate         48000 Hz
Duration            3.595 sec
Num. samples        172557
Start sample        0
End sample          172557
Note                A3
Pitch semitones     0
Pitch cents         47
Loop type           No loop
```

### Extracting AKAI samples as wav files

The `export` command of this toolset extracts samples of an AKAI image to `.wav` files
following the 'directory' structure of the AKAI image.
This command has the following form

```
python -m smpl_extract export [image_file] [-f export_format] [-d destination]
```

- `image_file`: The path to the file containing the AKAI image on your operating system - either 
                absolute or relative to the current working directory. 
                (e.g., `"./my images/akai_s300_1.iso"` or `"/home/foo/media/akai_img"`, etc.).
- `export_format`: The output format of the extracted samples. Currently only accepts `wav`. 
                   The default output format is `wav`.
- `destination`: The destination directory for the exported samples. The samples will be exported in
                 a directory structure which mirrors the structure of the AKAI image. The default 
                 destination is the current working directory.

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
python -m smpl_extract export "./imgs/example.iso" "./output/"
```

will produce the following file structure

```
/output/A/SAW/SAMPL1.wav
/output/A/SAW/SAMPL2.wav
/output/A/SQUARE/LEAD2.wav
/output/B/SYNTH/BRASS1.wav
/output/B/SYNTH/BRASS2.wav
```

**Note**: The `LEAD2L` and `LEAD2R` mono samples have been merged into a 
stereo file `LEAD2.wav`. This is because samples whose names differ
by only a terminal `L` or `R` indicate the left and right (respectively)
channels of a single stereo sample. 

## Project Structure

This project relies heavily on the [construct](https://github.com/construct/construct) library,
which supports declarative parsing and building of binary data. There is a bit of a learning
curve for this library, but its [readthedocs page](https://construct.readthedocs.io/en/latest/)
offers a good overview of the API and addresses some common use-cases.


## AKAI S3000 Format
### Background

Most AKAI image files are given the extension `.iso`. Typically, `.iso`s are thought of as a "raw binary dump" 
(or image) of an entire compact disk - agnostic of specific formatting. While this is technically true, most 
programs which read/mount/create ISOs expect the image to conform to a known formatting (usually 
[ISO 9660](https://en.wikipedia.org/wiki/ISO_9660) - the origin of the `.iso` extension), and indeed, most 
`.iso`s conform to such a format. AKAI disk images do not conform to ISO 9960 (or related formats) and are 
unreadable by disk image libraries or applications. 

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
On a granular level, an AKAI image is read and addressed in `8-bit` *bytes*. Multibyte integers (`16-bit` and 
`32-bit`) are encoded *little-endian*. On a macro level (sector-level), an AKAI image is read and addressed in 
8192-byte chunks called *sectors*. The concept of partitioning disks into sectors is common across disk 
formats and is usually leveraged as a unit of addressing across different filesystem specifications. As such, 
a proper AKAI image should be evenly divisible into an integer number of sectors. The main take-away 
from this section should be that there are two methods of addressing: addressing by byte, and 
addressing by sector.

#### Image Layers and Terminology
An AKAI image is divided in to three nested layers. At the topmost layer, the image is divided into 
*partitions*; each partition is divided into *volumes*; and each volume is divided into *files*.  Note: the 
preceding names for each layer are just that - names. They *do not* indicate any particular formatting 
implied by similar names in other disk format specifications. For instance, in the context of other disk 
formats, what is called a *volume* can span multiple *partitions* - this is not the case (to my knowledge) for 
an AKAI image.

Another potential point of confusion is the use of the term *file*. I believe this term best describes this 
third layer of nesting. Trouble arises from the potential confusion around what are traditionally called a 
*filesystem* and a *file allocation table* (FAT). Analogous entities do exist for AKAI images; however, 
because of the layer at which these are specified (at each partition) and some additional nuances, the 
alternative terms *segment-map* and *segment allocation table*, respectively, are used. This will be 
explained in more detail shortly, but it is worth introducing now.

#### Partitions
Partitions consist of a fixed-length *header* section, and a variable-length *data* section. All sector-level 
addressing contained within a partition is done with respect to the current partition's starting address. 
The total partition size (in sectors) is specified in the partition's header, in addition to a list of 
*volume entries* which indicate the *name*, *type*, and *starting offset* (in sectors) of each volume 
contained within the partition. 

#### Segments and the Segment Allocation Table
Perhaps the most important portion of a partition's header is the  *segment allocation table (SAT)*. This 
table describes how sectors within the partition "flow" into one another. Suppose a large chunk of data 
(whose size exceeds the length of a sector) needs to be read somewhere within the current partition. 
Since at least two sectors of data are needed, the locations of this data will span across multiple sectors. 
However, the sectors containing the desired data are not necessarily placed consecutively in the AKAI 
image. 

As the stream-pointer approaches the boundary of a given sector it must know in advance which sector 
contains the rest of the data. This can be accomplished by specifying an ordered list of *sector addresses* 
which link sectors containing contiguous data. An ordered collection of sectors containing a contiguous 
stream of data is called a *segment*. Segments are addressed by the address of their first sector.
The *segment allocation table* (SAT) gives lists of sector addresses that specify individual segments. The 
entire collection of segments is called a *segment map*. For additional clarification on this layout, search 
for information regarding *file allocation tables*.

Note that the SAT specifies the "flow" of all data within the partition. This data includes the contents of 
volumes and their constituent files. Therefore, whenever the stream pointer reaches the boundary of a 
sector with a partition's data, it will jump to the beginning of the next sector in the current segment, 
wherever that may be. 

#### Volumes
Each volume consists of a fixed length *header* section and a variable-length *data* section. The header 
consists of a list of file entries which specify the *name*, *type*, *size* and *segment address* of each 
file in the volume. There is no "directory" system for files; each file listed is simply a sub-element of 
the current volume. In this way, volumes of AKAI images function more or less as folders for files within 
a partition.

#### Files
At the lowest level of nesting are files which typically contain either *sample* or *program data*. Of note is 
that the AKAI sample format does not inherently support stereo encoding within a single file. Rather, 
when stereo audio is required, two similarly named sample files will separately contain the *left* and *right* 
channel data.

## Development and contributing
This tool-set is in active development and has only been rigorously tested in Windows 10. 
If a bug is found, please report it as an issue. Feature requests are welcome, but there is no 
guarantee I will be able to implement it.
