# SRA downloader
Download fastqs from SRA easily.

## Installation
Besides python/pip, the only requirement is wget.
```
git clone https://github.com/WarrenLab/sra_downloader.git
cd sra_downloader
pip install .
```

## Usage
Download a single run:
```
sra_downloader SRR6364203
```

Download all runs from an experiment:
```
sra_downloader SRX4831284
```

## TODO
* Switch to requests API instead of urllib for RESTful stuff
* Prompt user to make sure request is correct before starting download
* Add ability to use NCBI key
* Add pauses between NCBI requests to prevent 429 errors
