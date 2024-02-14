import re
from bleach import clean
from bleach import clean


def sanitize_html(text):
    return clean(text, tags=[], attributes={}, strip=True)


def sanitize_html(text):
    return clean(text, tags=[], attributes={}, strip=True)


def sanitize_html(text):
    # Allow only a limited set of tags and attributes
    allowed_tags = ["p", "b", "i", "br"]
    allowed_attrs = {"href": True}

    # Remove all other tags and attributes
    cleaned_text = re.sub(r"<(?!/*(?:" + "|".join(allowed_tags) + "))[^>]*>", "", text)

    # Remove attributes not in the whitelist
    for tag in allowed_tags:
        cleaned_text = re.sub(
            rf"<{tag}[^>]*>",
            lambda match: "".join(
                attr
                for attr in match.group(0).split()
                if attr.split("=")[0] in allowed_attrs
            ),
            cleaned_text,
        )

    return cleaned_text
