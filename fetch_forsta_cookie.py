# fetch_forsta_cookie.py
import os, sys, base64, json, time
from playwright.sync_api import sync_playwright

LOGIN_URL = os.environ.get("FORSTA_LOGIN_URL") or "https://sw2.decipherinc.com/login/"
USERNAME  = os.environ["FORSTA_USER"]
PASSWORD  = os.environ["FORSTA_PASS"]

def get_cookie_header(cookies, domain_suffix=".decipherinc.com"):
    """
    Build 'name=value; ...' only from cookies relevant to the Decipher/Forsta domains.
    """
    pairs = []
    now = time.time()
    for c in cookies:
        # skip expired
        if c.get("expires") and c["expires"] != -1 and c["expires"] < now:
            continue
        dom = c.get("domain","")
        if dom.endswith(domain_suffix):
            # conservative: include only cookies that are not HttpOnly-restricted from scripts? (Playwright provides all)
            pairs.append(f"{c['name']}={c['value']}")
    # Sorting is optional; keeps it stable
    return "; ".join(sorted(pairs))

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        ctx.add_cookies([{
            "name": "DECIPHER_POLICY", "value": "1",
            "domain": "sw2.decipherinc.com", "path": "/"
        }])
        page = ctx.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # Accept cookie banner if present
        try:
            page.get_by_role("button", name="Accept", exact=True).click(timeout=3000)
        except Exception:
            pass  # banner might not appear

        # Fill creds (selectors based on current page UI)
        # Try common names in order to be resilient
        filled = False
        for sel in ['input[name="email"]','input[name="username"]','input[type="email"]']:
            try:
                page.fill(sel, USERNAME, timeout=2000)
                filled = True
                break
            except Exception:
                continue
        if not filled:
            raise RuntimeError("Email input not found; update selector.")

        pwd_filled = False
        for sel in ['input[name="password"]','input[type="password"]']:
            try:
                page.fill(sel, PASSWORD, timeout=2000)
                pwd_filled = True
                break
            except Exception:
                continue
        if not pwd_filled:
            raise RuntimeError("Password input not found; update selector.")

        # Sign in
        try:
            page.get_by_role("button", name="Sign In").click()
        except Exception:
            # fallback to form submit
            page.press('input[name="password"]', "Enter")

        # Wait until network settles or a UI element indicates login
        page.wait_for_load_state("networkidle")

        # Grab cookies from the authenticated context
        cookies = ctx.cookies()
        header = get_cookie_header(cookies, ".decipherinc.com")

        if not header or "IRIS_SESSION=" not in header:
            # IRIS_SESSION is a typical session cookie; tweak if your site uses a different one
            raise RuntimeError("Login may have failed: expected session cookie missing.")

        # Output as both file and base64 (safe for env)
        with open("forsta_cookie.txt", "w", encoding="utf-8") as f:
            f.write(header)

        b64 = base64.b64encode(header.encode("utf-8")).decode("ascii")
        # Write to $GITHUB_OUTPUT so downstream steps can read it
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as fh:
                fh.write(f"FORSTA_COOKIE_B64={b64}\n")

        print("Fetched FORSTA cookie OK.")
        browser.close()

if __name__ == "__main__":
    main()
