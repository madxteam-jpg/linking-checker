import shlex
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


def parse_space_separated_line(line: str) -> list[str]:
    """Parses space-separated input, preserving quotes for multi-word anchor text."""
    try:
        # Handles quotes properly (e.g. "https://site.com" "Multi Word Anchor" "https://target.com")
        return shlex.split(line)
    except ValueError:
        # Fallback to simple split if quotes are unclosed
        return line.split()


# Streamlit UI Setup
st.set_page_config(page_title="HREF Link Checker", layout="wide")
st.title("🔗 HREF Link Alignment Checker")
st.write(
    "Enter line items separated by spaces: `Source_URL Anchor_Text Target_URL`"
)
st.caption(
    '💡 **Tip:** If your anchor text contains multiple words, wrap items in quotes: `"https://site.com" "Anchor Text" "https://target.com"`'
)

# Text area for multi-line input
raw_input = st.text_area(
    "Batch Input",
    height=200,
    placeholder=(
        "https://python.org Downloads https://www.python.org/downloads\n"
        'https://python.org "PyPI Packages" https://pypi.org'
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
                parts = parse_space_separated_line(line)

                if len(parts) >= 3:
                    source, anchor, target = parts[0], parts[1], parts[2]
                    status = check_href_alignment(source, anchor, target)
                    results.append(
                        {
                            "Source Page": source,
                            "Anchor Text": anchor,
                            "Target Link": target,
                            "Result": status,
                        }
                    )
                else:
                    results.append(
                        {
                            "Source Page": line,
                            "Anchor Text": "-",
                            "Target Link": "-",
                            "Result": "Invalid Format (Needs 3 space-separated values)",
                        }
                    )

        # Display results in a table format
        st.dataframe(results, use_container_width=True)
