mapping_Q1_CAN = {
    1: 'Alberta',
    2: 'British Columbia',
    3: 'Manitoba',
    4: 'New Brunswick',
    5: 'Newfoundland',
    6: 'Nova Scotia',
    7: 'Ontario',
    8: 'Prince Edward Island',
    9: 'Quebec',
    10: 'Saskatchewan',
    11: 'Northwest Territories',
    12: 'Nunavut',
    13: 'Yukon'
}

mapping_Q1_USA = {
    1: 'Alabama',
    2: 'Alaska',
    3: 'Arizona',
    4: 'Arkansas',
    5: 'California',
    6: 'Colorado',
    7: 'Connecticut',
    8: 'Delaware',
    9: 'District of Columbia',
    10: 'Florida',
    11: 'Georgia',
    12: 'Hawaii',
    13: 'Idaho',
    14: 'Illinois',
    15: 'Indiana',
    16: 'Iowa',
    17: 'Kansas',
    18: 'Kentucky',
    19: 'Louisiana',
    20: 'Maine',
    21: 'Maryland',
    22: 'Massachusetts',
    23: 'Michigan',
    24: 'Minnesota',
    25: 'Mississippi',
    26: 'Missouri',
    27: 'Montana',
    28: 'Nebraska',
    29: 'Nevada',
    30: 'New Hampshire',
    31: 'New Jersey',
    32: 'New Mexico',
    33: 'New York',
    34: 'North Carolina',
    35: 'North Dakota',
    36: 'Ohio',
    37: 'Oklahoma',
    38: 'Oregon',
    39: 'Pennsylvania',
    40: 'Rhode Island',
    41: 'South Carolina',
    42: 'South Dakota',
    43: 'Tennessee',
    44: 'Texas',
    45: 'Utah',
    46: 'Vermont',
    47: 'Virginia',
    48: 'Washington',
    49: 'West Virginia',
    50: 'Wisconsin',
    51: 'Wyoming'
}

mapping_Q2 = {
    1: "Food & Beverage",
    2: "Beauty",
    3: "Health & Personal Care",
    4: "Household",
    5: "Kids",
    6: "Pet",
    7: "Tech",
    8: "Delivery",
    9: "Financial",
    10: "QSR Menu Item",
    11: "Other:"   # temporary placeholder
}

base_url = "https://sw2.decipherinc.com/rep/selfserve/4475/250910:img/"
old_cols_can = [
    'Q1r1', 'Q1r2', 'Q1r3', 'Q1r4', 'Q1r5', 'Q1r6', 'Q1r7', 'Q1r8', 'Q1r9', 'QProvincer11', 'Q1_r11r10', 'Q2', 'Q3_1', 'Q3_2', 'Q3_3', 'Q3_4', 'Q3_6', 'Q3_7', 'Q3_8', 'Q3_10', 'Q5_1', 'Q3_5', 'Q3_9', 'Q4_2','Q3_image1'
]
old_cols_usa = [
    'Q1r1', 'Q1r2', 'Q1r3', 'Q1r4', 'Q1r5', 'Q1r6', 'Q1r7', 'Q1r8', 'Q1r9', 'qStater10', 'Q1_r11r11', 'Q2', 'Q3_1', 'Q3_2', 'Q3_3', 'Q3_4', 'Q3_6', 'Q3_7', 'Q3_8', 'Q3_10', 'Q5_1', 'Q3_5', 'Q3_9', 'Q4_2','Q3_image1'
]
old_cols_new = [
    'Q1r1', 'Q1r2', 'Q1r3', 'Q1r4', 'Q1r5', 'Q1r6', 'Q1r7', 'Q1r8', 'Q1r9', None, None, None, 'Q3_1', 'Q3_2', 'Q3_3', 'Q3_4', 'Q3_6', 'Q3_7', 'Q3_8', 'Q3_10', 'Q5_1', 'Q3_5', 'Q3_9', 'Q4_2','Q3_image1'
]

new_cols = [
    "First_Name",
    "Last_Name",
    "Email",
    "Company",
    "Title",
    "Phone",
    "Address",
    "Address2",
    "City",
    "Province",
    "Postal_Code",
    "Product_Type",
    "Product_Name",
    "Product_Category",
    "Product_Competitors",
    "Product_Description",
    "Product_Launch_Date",
    "Product_Retail_Price",
    "Product_SKUs",
    "Product_UPC",
    "PO",
    "Innovation_Description",
    "Product_Hero_SKU",
    "Product_link",
    "Product_Image"
]

import pandas as pd
import numpy as np
import requests
import os, textwrap

# ---------------- mappings, lists, etc. (from your file) ----------------
# mapping_Q1_CAN, mapping_Q1_USA, mapping_Q2, base_url (per survey), old_cols_can/usa/new, new_cols
# (kept as-is from your config)  # ← make sure these are defined as in your file

# ---------------- helpers ----------------
def clean_cast_column(series: pd.Series) -> pd.Series:
    series = series.replace(["<NA>", "nan", "NaN", "None", ""], pd.NA)
    numeric = pd.to_numeric(series, errors="coerce")
    non_numeric_mask = series.notna() & numeric.isna()
    if non_numeric_mask.any():
        return series.astype("string")
    if numeric.notna().any():
        is_all_whole = (numeric.dropna() == numeric.dropna().astype(int)).all()
        has_nulls = numeric.isna().any()
        return numeric.astype("int64" if is_all_whole and not has_nulls else "float64")
    return series.astype("string")

def fetch_survey_df(client_id: str, survey_id: str, api_key: str, fmt: str = "json") -> pd.DataFrame:
    url = f"https://sw2.decipherinc.com/api/v1/surveys/selfserve/{client_id}/{survey_id}/data?format={fmt}"
    headers = {"x-apikey": api_key, "Accept": "application/json"}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        msg = r.text.strip()
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {msg or 'No body'} for URL: {url}")

    data = r.json()
    df = pd.json_normalize(data)

    # 1) Cast first (matches your working script)
    df = df.apply(clean_cast_column)

    # 2) Then filter completes robustly
    if 'status' in df.columns:
        status_num = pd.to_numeric(df['status'], errors='coerce')
        df = df[status_num == 3].copy()
    else:
        # If there is genuinely no 'status' column, keep all rows (or choose to empty)
        # Your solo script would KeyError here; keeping rows is usually safer.
        pass

    # 3) Optional recast like your script
    df = df.apply(clean_cast_column)
    return df

# ---------------- main transform (v2, fixed) ----------------
def transform_survey_v2(
    df: pd.DataFrame,
    old_cols: list,
    new_cols: list,
    base_url: str,
    mapping_q1: dict | None = None,
    mapping_q2: dict | None = None,
    q1_col: str = "QProvincer11",   # source name
    q2_col: str = "Q2",             # source name
    q2_other_col: str = "Q2r11oe",  # source name for "Other" text
    q2_other_label: str = "Other:",
    blank_if_no_mapping: bool = False,
    force_all_new_cols: bool = True,
    reorder_final: bool = True
) -> pd.DataFrame:
    if df.empty:
        print("DataFrame is empty — skipping downstream steps")
        return df

    out = df.copy()

    # make sure "Other" helper exists if needed
    if q2_other_col and q2_other_col not in out.columns:
        out[q2_other_col] = np.nan

    # --------- MAPPING FIRST (before rename) ---------
    # Q2 mapping + passthrough from "Other" field
    if q2_col in out.columns:
        if mapping_q2:
            out[q2_col] = out[q2_col].map(mapping_q2)
            if q2_other_col in out.columns and q2_other_label:
                mask_other = out[q2_col] == q2_other_label
                if mask_other.any():
                    out.loc[mask_other, q2_col] = out.loc[mask_other, q2_other_col]
        elif blank_if_no_mapping:
            out[q2_col] = ""

    # Q1 (region/state) mapping
    if q1_col in out.columns:
        if mapping_q1:
            out[q1_col] = out[q1_col].map(mapping_q1)
        elif blank_if_no_mapping:
            out[q1_col] = ""

    # Q5 simple map (still source name pre-rename)
    if "Q5_1" in out.columns:
        out["Q5_1"] = out["Q5_1"].map({1: "Yes", 2: "No"})

    # --------- SELECT + RENAME ---------
    keep = (['uuid'] if 'uuid' in out.columns else []) + [c for c in old_cols if c and c in out.columns]
    if keep:
        out = out[keep]

    # build rename map only for existing, non-empty old cols
    kept_old = [c for c in old_cols if c and c in out.columns]
    rename_map = {c: new_cols[old_cols.index(c)] for c in kept_old}
    out = out.rename(columns=rename_map)

    # normalize NAs
    out = out.replace(["<NA>", "nan"], pd.NA).fillna("")

    # ensure full target schema columns exist (blank if missing)
    if force_all_new_cols:
        for i, tgt in enumerate(new_cols):
            if tgt not in out.columns:
                out[tgt] = ""

    # product image URL (post-rename; expects target 'Product_Image')
    if "Product_Image" in out.columns and base_url:
        base = base_url.rstrip("/") + "/"
        out["Product_Image"] = out["Product_Image"].apply(
            lambda x: (base + str(x).replace(" ", "/")) if isinstance(x, str) and x.strip() else ""
        )

    # final order
    if reorder_final:
        final_cols = (['uuid'] if 'uuid' in out.columns else []) + list(new_cols)
        out = out.reindex(columns=[c for c in final_cols if c in out.columns])

    return out

# ---------------- orchestrator (fixed arg order + per-survey q1_col + blank flag) ----------------
def run_all_surveys(client_id: str, api_key: str, surveys: list):
    raw, cleaned = {}, {}
    for s in surveys:
        name, sid = s["name"], s["id"]
        df_raw = fetch_survey_df(client_id, sid, api_key)
        raw[name] = df_raw

        base_url = f"https://sw2.decipherinc.com/rep/selfserve/{client_id}/{sid}:img/"

        df_clean = transform_survey_v2(
            df=df_raw,
            old_cols=s["old_cols"],
            new_cols=s["new_cols"],
            base_url=base_url,
            mapping_q1=s.get("map_q1"),
            mapping_q2=s.get("map_q2"),
            q1_col=s.get("q1_col", "QProvincer11"),   # allow per-survey override
            q2_col=s.get("q2_col", "Q2"),
            q2_other_col=s.get("q2_other_col", "Q2r11oe"),
            blank_if_no_mapping=s.get("blank_if_no_mapping", False),
            force_all_new_cols=True,
            reorder_final=True
        )
        cleaned[name] = df_clean
    return raw, cleaned

# ---------------- config ----------------
# One unified target schema (your `new_cols`), different source lists per survey
surveys = [
    {
        "name": "can",
        "id": "250910",
        "old_cols": old_cols_can,
        "new_cols": new_cols,
        "map_q1": mapping_Q1_CAN,
        "map_q2": mapping_Q2,
        "q1_col": "QProvincer11",    # source column name
        "blank_if_no_mapping": False
    },
    {
        "name": "usa",
        "id": "250914",
        "old_cols": old_cols_usa,
        "new_cols": new_cols,
        "map_q1": mapping_Q1_USA,
        "map_q2": mapping_Q2,
        "q1_col": "qStater10",       # USA source column name
        "blank_if_no_mapping": False
    },
    {
        "name": "new",
        "id": "250915",
        "old_cols": old_cols_new,    # contains None placeholders
        "new_cols": new_cols,
        "map_q1": None,              # skip Q1/Q2
        "map_q2": None,
        "blank_if_no_mapping": True  # blank them if present
    },
]

# ---------------- run ----------------
api_key   = "z8ajshbwdkzwb5qms48ty5w85p8h4wvn4e2mytrh258n7hwwe3a6bm5mcxg806nv"
client_id = "4475"
raw_dfs, clean_dfs = run_all_surveys(client_id, api_key, surveys)

df_can = clean_dfs["can"]
df_usa = clean_dfs["usa"]
df_new = clean_dfs["new"]

# --- 0) Auth + setup  ---
import os, re, json, pandas as pd, numpy as np, gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
if not raw:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is empty. Add it as a repo secret.")
sa_info = json.loads(raw) if raw.startswith("{") else json.loads(__import__("base64").b64decode(raw).decode("utf-8"))
creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
gc = gspread.authorize(creds)

# --- Mirror Product_Image (Forsta/Decipher via API) → Google Drive -----------
import io, time, uuid as _uuidmod, mimetypes, requests, urllib.parse, re
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

DRIVE_FOLDER_ID = "1CPUdz5rx6R6WY8mqHAu2XbrbggoY-m5m"  # your test folder
FORSTA_COOKIE  = os.getenv("FORSTA_COOKIE", "").strip()  # decipher_session=...

def _drive_service(creds):
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def _origin_referer(img_url: str) -> str:
    # Build a same-survey referer; many :img endpoints require it
    try:
        part = img_url.split("/rep/selfserve/")[1].split(":img/")[0]  # "4475/250910"
        return f"https://sw2.decipherinc.com/rep/selfserve/{part}/"
    except Exception:
        p = urllib.parse.urlsplit(img_url)
        return f"{p.scheme}://{p.netloc}/"

def _img_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Accept": "image/*,application/json;q=0.9,*/*;q=0.8",
        "User-Agent": "DecipherImageMirror/1.0",
    })
    cookie = os.getenv("FORSTA_COOKIE", "").strip()
    if cookie:
        s.headers["Cookie"] = cookie  # send full string verbatim
    return s

def _img_session_for_diag() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Accept": "image/*,application/json;q=0.9,*/*;q=0.8",
        "User-Agent": "DecipherImageMirror/diag/1.0",
    })
    cookie = os.getenv("FORSTA_COOKIE", "").strip()
    if cookie:
        # IMPORTANT: send the full multi-pair Cookie header exactly as copied from the :img request
        s.headers["Cookie"] = cookie
    return s

def diag_mirror_single(df, creds, label: str, drive_folder_id: str):
    """Diagnose auth, fetch, and Drive write with a single row. Does NOT modify the DF."""
    try:
        # 0) Confirm there is a URL to test
        ser = df.loc[df["Product_Image"].astype(str).str.strip() != "", ["uuid","Product_Image"]].head(1)
        if ser.empty:
            print(f"[diag:{label}] No non-empty Product_Image to test.")
            return
        row = ser.iloc[0]
        u = str(row["uuid"])
        url = str(row["Product_Image"]).strip()
        print(f"[diag:{label}] Test uuid={u}")
        print(f"[diag:{label}] URL={url}")

        # 1) Try fetching the image with Cookie + Referer
        sess = _img_session_for_diag()
        ref  = _origin_referer(url)
        r = sess.get(url, headers={"Referer": ref}, timeout=30, allow_redirects=True)
        ctype = r.headers.get("Content-Type", "").split(";",1)[0].lower()
        print(f"[diag:{label}] fetch status={r.status_code}, ctype={ctype}, final_url={r.url}")

        # Heuristic: if we got HTML/login instead of image, show first bytes
        head_bytes = r.content[:256]
        if r.status_code != 200:
            print(f"[diag:{label}] FAIL: non-200 from :img fetch")
            return
        if not ctype.startswith("image/"):
            print(f"[diag:{label}] FAIL: not an image (likely login); first bytes={head_bytes[:80]!r}")
            return

        # 2) Try uploading a tiny dummy file to Drive to check folder permissions
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        dummy_meta = {"name": f"diag_{label}_{u}.txt", "parents": [drive_folder_id]}
        dummy_media = MediaIoBaseUpload(io.BytesIO(b"diag-ok"), mimetype="text/plain", resumable=False)
        dummy_file = drive.files().create(body=dummy_meta, media_body=dummy_media, fields="id").execute()
        print(f"[diag:{label}] drive dummy upload OK id={dummy_file['id']}")

        # 3) Try uploading the fetched image
        from mimetypes import guess_extension
        ext = guess_extension(ctype) or ".bin"
        img_meta = {"name": f"{u}{ext}", "parents": [drive_folder_id]}
        img_media = MediaIoBaseUpload(io.BytesIO(r.content), mimetype=ctype, resumable=False)
        img_file = drive.files().create(body=img_meta, media_body=img_media, fields="id,webViewLink").execute()
        # make link-viewable
        drive.permissions().create(fileId=img_file["id"], body={"role": "reader", "type": "anyone"}).execute()
        direct = f"https://drive.google.com/uc?id={img_file['id']}"
        print(f"[diag:{label}] drive image upload OK id={img_file['id']}, direct={direct}")
        print(f"[diag:{label}] ✅ End-to-end OK. If batch still blanks, the bug is in the loop/assignment.")
    except Exception as e:
        print(f"[diag:{label}] EXCEPTION: {e}")

def _ext_from_mime(ctype: str) -> str:
    ctype = (ctype or "").split(";", 1)[0].strip().lower()
    if ctype in ("image/jpeg", "image/jpg"): return ".jpg"
    if ctype == "image/png": return ".png"
    if ctype == "image/gif": return ".gif"
    if ctype == "image/webp": return ".webp"
    return mimetypes.guess_extension(ctype) or ".bin"

def _fetch_image(sess: requests.Session, url: str) -> tuple[bytes, str]:
    hdrs = {"Referer": _origin_referer(url)}
    r = sess.get(url, headers=hdrs, timeout=30, allow_redirects=True)
    ctype = r.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if r.status_code != 200:
        raise RuntimeError(f"GET {r.status_code} {ctype or ''} for {url}")
    # login pages often return 200 text/html; detect & fail
    if not ctype.startswith("image/"):
        raise RuntimeError(f"Got {ctype or 'unknown'} (likely login HTML) for {url}")
    return r.content, ctype or "application/octet-stream"

def _upload_image(drive, folder_id: str, name: str, blob: bytes, mime: str) -> dict:
    meta = {"name": name, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(blob), mimetype=(mime or "application/octet-stream"), resumable=True)
    f = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    drive.permissions().create(fileId=f["id"], body={"role": "reader", "type": "anyone"}).execute()
    f["directLink"] = f"https://drive.google.com/uc?id={f['id']}"
    return f

def mirror_df_product_images_with_uuid(df, creds, url_col="Product_Image", uuid_col="uuid", out_col="Product_Image"):
    if df is None or df.empty or url_col not in df.columns or uuid_col not in df.columns:
        print("[mirror] skip: df empty or missing columns")
        return df

    # quick visibility check
    sample = df[url_col].dropna().astype(str).str.strip()
    print("[mirror] sample URLs:", sample.head(3).tolist())
    if not sample.any():
        print("[mirror] all blank Product_Image; upstream is empty.")
        return df

    sess = _img_session()
    drive = _drive_service(creds)

    new_links = []
    for url, u in zip(df[url_col].astype(str).fillna(""), df[uuid_col].astype(str).fillna("")):
        url = url.strip()
        u   = (u.strip() or _uuidmod.uuid4().hex)
        if not url:
            new_links.append("")
            continue
        try:
            blob, ctype = _fetch_image(sess, url)
            name = f"{u}{_ext_from_mime(ctype)}"
            info = _upload_image(drive, DRIVE_FOLDER_ID, name, blob, ctype)
            new_links.append(info["directLink"])
            print(f"[mirror] ok {u}")
        except Exception as e:
            print(f"[mirror] FAIL {u} → {e}")
            new_links.append("")
        time.sleep(0.05)
    df[out_col] = new_links
    return df

SERVICE_ACCOUNT_EMAIL = getattr(creds, "service_account_email", None)
print("[diag] SA email:", SERVICE_ACCOUNT_EMAIL or "<unknown>")
print("[diag] DRIVE_FOLDER_ID:", os.getenv("DRIVE_FOLDER_ID", "1CPUdz5rx6R6WY8mqHAu2XbrbggoY-m5m"))

diag_mirror_single(df_can, creds, "can", "1CPUdz5rx6R6WY8mqHAu2XbrbggoY-m5m")
diag_mirror_single(df_usa, creds, "usa", "1CPUdz5rx6R6WY8mqHAu2XbrbggoY-m5m")
diag_mirror_single(df_new, creds, "new", "1CPUdz5rx6R6WY8mqHAu2XbrbggoY-m5m")
# Replace Decipher URLs with Drive links (named after df['uuid'])
df_can = mirror_df_product_images_with_uuid(df_can, creds, url_col="Product_Image", uuid_col="uuid", out_col="Product_Image")
df_usa = mirror_df_product_images_with_uuid(df_usa, creds, url_col="Product_Image", uuid_col="uuid", out_col="Product_Image")
df_new = mirror_df_product_images_with_uuid(df_new, creds, url_col="Product_Image", uuid_col="uuid", out_col="Product_Image")

# ---- Sheet ref: ENV > hardcoded fallback ----
SHEET_REF = (os.environ.get("SHEET_URL") or "1U9g_BdnuCtxJar1bcbgOXsgpWpyuxqXeVM7kLnRw23I").strip().strip('"').strip("'")

def open_sheet_by_ref(gc, ref: str):
    m = re.search(r"/d/([A-Za-z0-9-_]+)", ref)
    key = m.group(1) if m else ref
    return gc.open_by_key(key)

sh = open_sheet_by_ref(gc, SHEET_REF)  # open once

# ---------- helper(s) ----------
def to_sheet_values(df: pd.DataFrame):
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_integer_dtype(out[c]):
            out[c] = out[c].astype("Float64")
        elif pd.api.types.is_string_dtype(out[c]):
            out[c] = out[c].astype("object")
    out = out.where(pd.notna(out), None).replace(
        {"<NA>": None, "nan": None, "NaN": None, "None": None}
    )
    values = []
    for _, row in out.iterrows():
        cleaned = []
        for x in row.tolist():
            if x is None or x is pd.NA:
                cleaned.append(None)
            elif isinstance(x, float) and np.isnan(x):
                cleaned.append(None)
            elif isinstance(x, str) and x.strip().lower() in ("<na>", "nan", "none"):
                cleaned.append(None)
            else:
                cleaned.append(x)
        values.append(cleaned)
    return values

def write_new_rows_by_key(sh, tab_name: str, df: pd.DataFrame, key_col="uuid", column_mapping=None) -> int:
    """
    Create tab if missing. If tab is blank: write headers + all rows.
    Else: align to existing headers and append only new rows by key_col.
    Returns number of rows written/appended. Skips if df is empty.
    """
    if df is None or df.empty:
        return 0

    if column_mapping:
        df = df.rename(columns=column_mapping).copy()

    if key_col not in df.columns:
        raise ValueError(f"DataFrame must include key column '{key_col}'")

    # normalize key to string (and strip whitespace just in case)
    df[key_col] = df[key_col].astype(str).str.strip()

    try:
        ws = sh.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=26)

    headers = ws.row_values(1)

    if not headers:
        # blank tab: put key first, then the rest
        ordered = [key_col] + [c for c in df.columns if c != key_col]
        df_to_write = df[ordered]
        ws.clear()
        ws.update("A1", [df_to_write.columns.tolist()] + to_sheet_values(df_to_write),
                  value_input_option="USER_ENTERED")
        return len(df_to_write)

    # align df to existing headers (add missing as blank; drop extras)
    for col in headers:
        if col not in df.columns:
            df[col] = None
    df = df[headers]

    # existing keys (assumes key is in column A)
    existing_keys = set(v.strip() for v in ws.col_values(1)[1:])  # skip header + trim
    new_rows = df[~df[key_col].astype(str).str.strip().isin(existing_keys)]
    if new_rows.empty:
        return 0

    values = to_sheet_values(new_rows)
    CHUNK = 500
    for i in range(0, len(values), CHUNK):
        ws.append_rows(values[i:i+CHUNK], value_input_option="USER_ENTERED")
    return len(new_rows)

# ---------- calls for your three datasets ----------
# Assumes df_can, df_usa, df_new are built above and include 'uuid'
results = []

try:
    n_can = write_new_rows_by_key(sh, "Canada", df_can, key_col="uuid")
    results.append(f"Canada: +{n_can} rows")
except Exception as e:
    results.append(f"Canada: ERROR {e}")

try:
    n_usa = write_new_rows_by_key(sh, "USA", df_usa, key_col="uuid")
    results.append(f"USA: +{n_usa} rows")
except Exception as e:
    results.append(f"USA: ERROR {e}")

try:
    n_new = write_new_rows_by_key(sh, "New & Noteworthy", df_new, key_col="uuid")
    results.append(f"New & Noteworthy: +{n_new} rows")
except Exception as e:
    results.append(f"New & Noteworthy: ERROR {e}")

print(" | ".join(results))
