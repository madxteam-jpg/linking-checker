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


# Streamlit UI Setup
st.set_page_config(page_title="HREF Link Checker", layout="wide")
st.title("🔗 HREF Link Alignment Checker")
st.write(
    "Enter line items below, one per line using comma separation: `Source URL, Anchor Text, Target URL`"
)

# Text area for multi-line input
raw_input = st.text_area(
    "Batch Input",
    height=200,
    placeholder=(
        "https://python.org, Downloads, https://www.python.org/downloads\n"
        "https://python.org, Documentation, https://www.google.com"
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
                parts = [p.strip() for p in line.split(",")]
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
                            "Result": "Invalid Format",
                        }
                    )

        # Display results in a table format
        st.dataframe(results, use_container_width=True)
