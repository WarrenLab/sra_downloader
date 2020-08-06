"""
Tools for navigating the SRA API and downloading fastqs
"""
import html
import json
from urllib.parse import urlencode, urljoin
from urllib.request import urlopen
import xml.etree.ElementTree as ET

EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
ENA_URL = "ftp://ftp.sra.ebi.ac.uk/vol1/"


def get_accession_id(accession: str):
    """
    Given an SRA search term, look up its SRA id.

    Given an SRA search term, such as a run, experiment, or project
    accession, look up its numerical SRA id.

    Args:
        accession: an SRA search term to look up

    Returns:
        string containing the SRA numerical ID of the requested
        accession
    """
    query = urlencode({"db": "sra", "retmode": "json", "term": accession})
    with urlopen(urljoin(EUTILS_URL, "esearch.fcgi?" + query)) as result:
        if result.getcode() == 200:
            ids = json.loads(result.read())["esearchresult"]["idlist"]
            if len(ids) == 0:
                print("no result for that search")  # TODO make this an error
            if len(ids) > 1:
                print(
                    "multiple results for that search"
                )  # TODO make this an error
            else:
                return ids[0]
        else:
            print(result.getcode())  # TODO make this an error


def get_id_run_accessions(sra_id: str):
    """
    Given an SRA id, return a list associated runs.

    Args:
        sra_id: numerical SRA id to look up, from `get_accession_id()`

    Returns:
        a `list` of `tuple`s, one for each run, where `t[0]` is a
        string containing the SRA accession for that run and `t[1]` is
        a string containing the layout for that run (either 'SINGLE'
        or 'PAIRED')
    """
    # run the query
    query = urlencode({"db": "sra", "id": sra_id, "retmode": "json"})
    with urlopen(urljoin(EUTILS_URL, "esummary.fcgi?" + query)) as result:
        json_loaded = json.loads(result)

        # get the library layout (i.e., single or paired)
        experiment_xml = json_loaded["result"][sra_id]["expxml"]
        experiment_xml = "<experiment>" + experiment_xml + "</experiment>"
        layout = list(
            ET.fromstring(experiment_xml)
            .find("Library_descriptor")
            .find("LIBRARY_LAYOUT")
        )[0].tag

        # get a list of accessions associated with this library
        runs_xml = html.unescape(json_loaded["result"][sra_id]["runs"])
        runs_xml = "<runs>" + runs_xml + "</runs>"
        accessions = [run.attrib["acc"] for run in ET.fromstring(runs_xml)]

        # finally, associate the layout tag with each accession and return
        return [(accession, layout) for accession in accessions]


def get_fastq_urls(sra_run_accession: str, paired: bool):
    """
    Get ftp urls for downloading SRA fastqs.

    Given an SRA run accession (these start with 'SRR') and the library
    type (i.e., whether it's paired-end or not), return a list of
    url(s) where the fastq file(s) for this accession can be found.

    Args:
        sra_run_accession: the SRA accession for a run. These begin
            with 'SRR'.
        paired: true if the run is paired-end, false otherwise.

    Returns:
        A list of url strings for ftp locations of all fastq files for
        this run. For a single-end library, this list will have length
        1; for a paired-end library, it will have length 2.
    """
    if not sra_run_accession.starts_with("SRR"):
        print("nope!")  # TODO make this an error

    base_url = urljoin(ENA_URL, sra_run_accession[:6])
    if len(sra_run_accession) > 9:
        base_url = urljoin(base_url, "00" + sra_run_accession[-1])
    base_url = urljoin(base_url, sra_run_accession)

    if paired:
        urls = [
            urljoin(base_url, sra_run_accession + "_1.fastq.gz"),
            urljoin(base_url, sra_run_accession + "_2.fastq.gz"),
        ]
    else:
        urls = [urljoin(base_url, sra_run_accession + ".fastq.gz")]

    return urls
