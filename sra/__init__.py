"""
Tools for navigating the SRA API and downloading fastqs
"""
import html
import json
from typing import Sequence
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests

EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
ENA_URL = "ftp://ftp.sra.ebi.ac.uk/vol1/fastq"
TIMEOUT = 2


class QueryError(Exception):
    """Error raised when an NCBI query does not work"""


def get_accession_id(accession: str, api_key: str = None) -> str:
    """
    Given an SRA search term, look up its SRA id.

    Given an SRA search term, such as a run, experiment, or project
    accession, look up its numerical SRA id.

    Args:
        accession (str): an SRA search term to look up
        api_key (str): an NCBI api key to use for the query

    Returns:
        str: the SRA numerical ID of the requested accession

    Raises:
        QueryError: when there is any problem with the HTTP lookup or
            subsequent parsing. For example, an HTTP return code other
            than 200 or a JSON result that doesn't contain the expected
            fields would cause this error.
    """
    query = {"db": "sra", "retmode": "json", "term": accession}
    if api_key is not None:
        query["api_key"] = api_key
    url = urljoin(EUTILS_URL, "esearch.fcgi")
    try:
        result = requests.get(url, params=query, timeout=TIMEOUT)
    except requests.RequestException as error:
        raise QueryError("Problem with request.") from error
    if result.status_code == requests.codes["✓"]:
        try:
            ids = result.json()["esearchresult"]["idlist"]
        except (ValueError, KeyError) as error:
            raise QueryError("bad JSON response") from error
        if len(ids) == 0:
            raise QueryError("no result for that search")
        if len(ids) > 1:
            raise QueryError("multiple results for that search")
        return ids[0]
    raise QueryError("HTTP error: {}".format(result.status_code))


def get_id_run_accessions(sra_id: str, api_key: str = None) -> Sequence[str]:
    """
    Given an SRA id, return a list associated runs.

    Args:
        sra_id: numerical SRA id to look up, from `get_accession_id()`
        api_key (str): an NCBI api key to use for the query

    Returns:
        list: a list of strings where each string is an SRA run
            accession for a run associated with this numerical
            SRA id

    Raises:
        QueryError: when there is a problem with the query result, such
            as an unparseable JSON response
    """
    # run the query
    query = {"db": "sra", "id": sra_id, "retmode": "json"}
    if api_key is not None:
        query["api_key"] = api_key
    url = urljoin(EUTILS_URL, "esummary.fcgi")
    try:
        result = requests.get(url, params=query, timeout=TIMEOUT)
    except requests.RequestException as error:
        raise QueryError("Problem with request.") from error

    if result.status_code != requests.codes["✓"]:
        raise QueryError("HTTP error: {}".format(result.status_code))

    try:
        # get a list of accessions associated with this library
        runs_xml = html.unescape(result.json()["result"][sra_id]["runs"])
        runs_xml = "<runs>" + runs_xml + "</runs>"
        accessions = [run.attrib["acc"] for run in ET.fromstring(runs_xml)]
    except (ValueError, KeyError, ET.ParseError) as error:
        raise QueryError("Could not process query result") from error

    return accessions


def get_fastq_url(sra_run_accession: str) -> str:
    """
    Get ftp url for downloading SRA fastqs.

    Given an SRA run accession (these start with 'SRR') and the library
    type (i.e., whether it's paired-end or not), return a url where the
    fastq file(s) for this accession can be found.

    Args:
        sra_run_accession: the SRA accession for a run. These begin
            with 'SRR'.
        paired: true if the run is paired-end, false otherwise.

    Returns:
        An ftp URL string where fastqs for this accession can be found.
        It will contain wildcards to account for the possibility of
        multiple files per run.
    """
    base_url = "/".join([ENA_URL, sra_run_accession[:6]])
    if len(sra_run_accession) > 9:
        base_url += "/{:03d}".format(int(sra_run_accession[9:]))
    base_url += "/" + sra_run_accession

    return base_url + "/*.fastq.gz"
