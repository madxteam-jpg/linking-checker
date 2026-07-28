from urllib.parse import urljoin, urlparse, unquote
import bs4
import requests
import streamlit as st


def normalize_url(url: str) -> str:
    """Normalizes URLs for robust matching (strips protocol trailing slashes, WWW variations, and trailing slashes)."""
    if not url:
        return ""
    url = url.strip()
    parsed = urlparse(url)
    
    # Standardize hostname (remove 'www.')
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
        
    # Standardize path
    path = parsed.path.rstrip("/")
    
    # Reconstruct normalized string without trailing slash or protocol sensitivity
    return f"{netloc}{path}"


def fetch_page_content(url: str) -> str:
    """Fetches web page content with complete browser-like headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    response = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
    response.raise_for_status()
    return response.text


def check_href_alignment(source_url: str, anchor_text: str, target_link: str) -> str:
    """Checks if the anchor text on the source page links directly to the target link."""
    try:
        html_content = fetch_page_content(source_url)
    except Exception as e:
        return f"Fail - HTTP Error ({type(e).__name__})"

    soup = bs4.BeautifulSoup(html_content, "html.parser")
    target_norm = normalize_url(target_link)
    anchor_clean = " ".join(anchor_text.strip().lower().split())

    for a_tag in soup.find_all("a", href=True):
        # Extract text including nested tags (e.g. <a><span>Text</span></a>)
        tag_text = " ".join(a_tag.get_text(strip=True).lower().split())

        # Check for partial or exact anchor text match
        if anchor_clean in tag_text:
            raw_href = a_tag["href"].strip()
            
            # Resolve relative paths (/about -> https://domain.com/about)
            resolved_href = urljoin(source_url, raw_href)
            
            if normalize_url(resolved_href) == target_norm:
                return "Good"

    return "Fail - Double check manually"


def parse_line_by_urls(line: str):
    """Parses a line by extracting Target URL (first), Source URL (last), and Anchor Text (middle)."""
    tokens = line.strip().split()

    if len(tokens) < 3:
        return None, None, None, "Invalid Format (Needs Target URL, Anchor Text, and Source URL)"

    target = tokens[0]
    source = tokens[-1]

    if not (target.startswith("http://") or target.startswith("https://")):
        return None, None, None, "Target URL must start with http:// or https://"

    if not (source.startswith("http://") or source.startswith("https://")):
        return None, None, None, "Source URL must start with http:// or https://"

    anchor = " ".join(tokens[1:-1])

    if not anchor:
        return None, None, None, "Missing Anchor Text"

    return target, anchor, source, None


# Streamlit UI Setup
st.set_page_config(page_title="HREF Link Checker", layout="wide")
st.title("🔗 HREF Link Alignment Checker")
st.write("Enter line items separated by spaces: `Target_URL Anchor Text Source_URL`")

raw_input = st.text_area(
    "Batch Input",
    height=200,
    placeholder=(
        "https://www.python.org/downloads Downloads https://python.org\n"
        "https://pypi.org PyPI Packages https://python.org"
    ),
)

if st.button("Check Links", type="primary"):
    lines = [line.strip() for line in raw_input.split("\n") if line.strip()]

    if not lines:
        st.warning("Please enter at least one line item to check.")
    else:
        results = []
        progress_bar = st.progress(0)

        with st.spinner("Checking links..."):
            for idx, line in enumerate(lines):
                target, anchor, source, error = parse_line_by_urls(line)

                if error:
                    results.append(
                        {
                            "Target Link": target if target else "-",
                            "Anchor Text": anchor if anchor else "-",
                            "Source Page": source if source else line,
                            "Result": f"Error: {error}",
                        }
                    )
                else:
                    status = check_href_alignment(source, anchor, target)
                    results.append(
                        {
                            "Target Link": target,
                            "Anchor Text": anchor,
                            "Source Page": source,
                            "Result": status,
                        }
                    )

                progress_bar.progress((idx + 1) / len(lines))

        st.dataframe(results, use_container_width=True)
