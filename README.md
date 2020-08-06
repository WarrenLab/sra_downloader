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
* Add pauses between NCBI requests to prevent 429 errors
* Implement unit and integration tests
* Allow retries on HTTP errors
