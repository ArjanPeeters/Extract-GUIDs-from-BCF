import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import io

st.set_page_config(page_title="BCF GUID Extractor", layout="centered")
st.title("📂 BCF GUID Extractor")

uploaded_file = st.file_uploader("Upload een BCF-bestand (.bcfzip of .bcf)", type=["bcfzip", "bcf"])

def extract_issues_from_bcf(file_bytes):
    issues = []

    with zipfile.ZipFile(file_bytes, 'r') as bcf_zip:
        issue_dirs = set(f.split('/')[0] for f in bcf_zip.namelist() if '/' in f)

        for issue_dir in issue_dirs:
            markup_path = f"{issue_dir}/markup.bcf"
            viewpoint_path = f"{issue_dir}/viewpoint.bcfv"

            if markup_path not in bcf_zip.namelist() or viewpoint_path not in bcf_zip.namelist():
                continue

            title, index = "(geen titel)", "?"
            try:
                with bcf_zip.open(markup_path) as markup_file:
                    tree = ET.parse(markup_file)
                    topic = tree.getroot().find('Topic')
                    if topic is not None:
                        t = topic.find('Title')
                        i = topic.find('Index')
                        if t is not None: title = t.text
                        if i is not None: index = i.text
            except:
                pass

            guids = set()
            try:
                with bcf_zip.open(viewpoint_path) as bcfv_file:
                    tree = ET.parse(bcfv_file)
                    for component in tree.findall('.//Component'):
                        guid = component.attrib.get("IfcGuid")
                        if guid:
                            guids.add(guid)
            except:
                pass

            for guid in sorted(guids):
                issues.append({
                    "Titel": title,
                    "Index": index,
                    "IFC_GUID": guid
                })

    return issues

if uploaded_file:
    with st.spinner("Bezig met analyseren..."):
        try:
            issues = extract_issues_from_bcf(uploaded_file)
            if issues:
                df = pd.DataFrame(issues)
                st.success(f"Gevonden: {len(df)} GUIDs")
                st.dataframe(df, use_container_width=True)

                # CSV downloadknop
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="bcf_guids.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Geen GUIDs gevonden in dit bestand.")
        except Exception as e:
            st.error(f"Fout tijdens verwerking: {e}")
