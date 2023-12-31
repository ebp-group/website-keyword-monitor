# -*- coding: utf-8 -*-
import logging
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import subprocess


log = logging.getLogger(__name__)


def _download_request(url, verify=True):
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    headers = {
        "user-agent": "Mozilla Firefox Mozilla/5.0; ebp-group website-keyword-monitor at github",  # noqa
        "accept-language": "de-CH",
    }
    r = http.get(url, headers=headers, timeout=20, verify=verify)
    r.raise_for_status()
    return r


def download(url, encoding="utf-8", verify=True):
    r = _download_request(url, verify=verify)
    if encoding:
        r.encoding = encoding
    return r.text


def download_content(url, verify=True):
    r = _download_request(url, verify=verify)
    return r.content


def jsondownload(url, verify=True):
    r = _download_request(url, verify=verify)
    return r.json()


def download_file(url, path, verify=True):
    r = _download_request(url, verify=verify)
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)


def get_content_type(url, verify=True):
    r = _download_request(url, verify=verify)
    content_type = r.headers.get("content-type")
    log.debug(f"Content-Type: {content_type}")
    if not content_type:
        return ""
    return content_type


def download_with_selenium(url, timeout=3):
    chrome_options = Options()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1200,1200")
    chrome_options.add_argument("--lang=de-CH")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(20)

    # Use stealth to not trigger Cloudflare etc. bot detection
    stealth(
        driver,
        languages=["de-CH", "de"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.get(url)
    # wait for the page to load
    time.sleep(timeout)
    content = driver.page_source
    log.debug(f"Website source: {content}")
    driver.quit()

    return content


def pdfdownload(
    url,
    encoding="utf-8",
    raw=False,
    layout=False,
    silent=False,
    page=None,
    rect=None,
    fixed=None,
):
    """Download a PDF and convert it to text"""
    pdf = download_content(url)
    return pdftotext(
        pdf,
        encoding=encoding,
        raw=raw,
        layout=layout,
        page=page,
        rect=rect,
        fixed=fixed,
    )


def pdftotext(
    pdf, encoding="utf-8", raw=False, layout=False, page=None, rect=None, fixed=None
):
    pdf_command = ["pdftotext"]
    if raw:
        pdf_command += ["-raw"]
    if layout:
        pdf_command += ["-layout"]
    if page:
        pdf_command += ["-f", str(page), "-l", str(page)]
    if rect:
        pdf_command += [
            "-x",
            str(rect[0]),
            "-y",
            str(rect[1]),
            "-W",
            str(rect[2]),
            "-H",
            str(rect[3]),
        ]
    if fixed:
        pdf_command += ["-fixed", str(fixed)]
    pdf_command += ["-", "-"]
    p = subprocess.Popen(pdf_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = p.communicate(input=pdf)[0]
    return out.decode(encoding)
