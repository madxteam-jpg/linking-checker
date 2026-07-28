from urllib.parse import urljoin, urlparse
import bs4
import requests
import streamlit as st


def normalize_url(url: str) -> str:
    """Normalizes URLs by removing trailing slashes and ensuring consistent formatting."""
    url = url.strip()
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def check_href_alignment(source_url: str, anchor_text: str, target_link: str) -> str:
    """Checks if the anchor text on the source page links directly to the target link."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(source_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception:
        return "Fail - Double check manually"

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    target_normalized = normalize_url(target_link)
    anchor_clean = anchor_text.strip().lower()

    for a_tag in soup.find_all("a", href=True):
        tag_text = a_tag.get_text(strip=True).lower()

        if anchor_clean in tag_text:
            resolved_href = urljoin(source_url, a_tag["href"])
            if normalize_url(resolved_href) == target_normalized:
                return "Good"

    return "Fail - Double check manually"


def parse_line_by_urls(line: str):
    """
    Parses a line by identifying the starting target URL and trailing source URL,
    treating everything in between as the anchor text.
    """
    tokens = line.strip().split()

    if len(tokens) < 3:
        return None, None, None, "Invalid Format (Requires target URL, anchor text, and source URL)"

    target = tokens[0]
    source = tokens[-1]
    
    # Check if both ends start with http:// or https://
    if not (target.startswith("http://") or target.startswith("https://")):
        return None, None, None, "Target URL must start with http:// or https://"

    if not (source.startswith("http://") or source.startswith("https://")):
        return None, None, None, "Source URL must start with http:// or https://"

    # Everything between the first and last element is the anchor text
    anchor = " ".join(tokens[1:-1])

    if not anchor:
        return None, None, None, "Missing Anchor Text"

    return target, anchor, source, None


# Streamlit UI Setup
st.set_page_config(page_title="HREF Link Checker", layout="wide")
st.title("🔗 HREF Link Alignment Checker")
st.write(
    "Enter line items separated by spaces: `Target_URL Anchor Text Source_URL`"
)
st.caption(
    "💡 No quotes needed! The app automatically detects URLs at the start and end of each line and treats everything in between as the anchor text."
)

# Text area for multi-line input
raw_input = st.text_area(
    "Batch Input",
    height=200,
    placeholder=(
        "https://www.python.org/downloads Downloads https://python.org\n"
        "https://pypi.org Official PyPI Package Index https://python.org"
    ),
)

if st.button("Check Links", type="primary"):
    lines = [line.strip() for line in raw_input.split("\n") if line.strip()]

    if not lines:
        st.warning("Please enter at least one line item to check.")
    else:
        results = []

        with st.spinner("Checking links..."):
            for line in lines:
                target, anchor, source, error = parse_line_by_urls(line)

                if error:
                    results.append(
                        {
                            "Target Link": tokens[0] if 'tokens' in locals() and tokens else "-",
                            "Anchor Text": "-",
                            "Source Page": line,
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

        # Display results in a table format
        st.dataframe(results, use_container_width=True)
