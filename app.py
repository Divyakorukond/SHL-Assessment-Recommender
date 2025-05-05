import streamlit as st
import requests
from bs4 import BeautifulSoup
import torch

from search import search

# Patch for PyTorch bug
if hasattr(torch, "classes"):
    try:
        _ = torch.classes.__name__
    except Exception:
        pass

st.set_page_config(page_title="Talent Assessment Finder", layout="centered")

# Theme toggle
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def set_theme():
    if st.session_state.theme == "dark":
        st.markdown(
            """
            <style>
            .main {
                background-color: #121212 !important;
                color: #e0e0e0 !important;
            }
            a {
                color: #bb86fc !important;
            }
            .stButton>button {
                background-color: #bb86fc;
                color: #121212;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .main {
                background-color: white !important;
                color: black !important;
            }
            a {
                color: #2a9d8f !important;
            }
            .stButton>button {
                background-color: #2a9d8f;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

st.radio(
    "Select Theme:",
    options=["light", "dark"],
    index=0,
    key="theme",
)
st.markdown("<h1 style='color:#4B0082; font-family: Verdana, sans-serif; font-size: 48px;'>🔍 Talent Assessment Finder</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='color:#6A5ACD;'>🧩 Explore Assessment Types</h3>", unsafe_allow_html=True)
st.markdown("""
1 - Cognitive & Aptitude  
2 - Background & Situational Judgement  
3 - Skills & Competencies  
4 - Development & Feedback  
5 - Practical Exercises  
6 - Knowledge & Expertise  
7 - Personality & Behavioral Insights  
8 - Simulated Scenarios
""")

st.markdown("Enter a **job description** or paste a **URL**. The system will suggest the most suitable assessments.")

input_type = st.radio("Select input type:", ("Text", "URL"))
user_input = ""

if input_type == "Text":
    user_input = st.text_area("Paste your job description or requirement here:", height=200)

elif input_type == "URL":
    user_url = st.text_input("Enter a URL pointing to a job description:")
    if user_url:
        if not user_url.startswith(("http://", "https://")):
            st.warning("⚠️ Please enter a valid URL (starting with http:// or https://)")
        else:
            try:
                response = requests.get(user_url, timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                user_input = soup.get_text(separator=" ", strip=True)
                st.success("✅ Successfully extracted text from URL!")
            except Exception as e:
                st.error(f"❌ Unable to fetch text from URL: {e}")

# --- Options ---
st.markdown("<hr style='border: 1px solid #6A5ACD;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#6A5ACD;'>🧠 AI-Powered Features</h3>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    enable_rerank = st.checkbox("🔁 Enable Re-ranking", value=True)
    enable_fallback = st.checkbox("🧩 Enable Fallback Option", value=True)
with col2:
    show_explanations = st.checkbox("💬 Show AI Explanations", value=False)
    top_k = st.slider("🔝 Number of recommendations", min_value=5, max_value=15, value=10)

# --- Trigger Search ---
if st.button("🔍 Find Assessments", key="find_assessments", help="Click to find relevant assessments based on your input"):
    if not user_input.strip():
        sample_descriptions = [
            "Example 1: Software engineer with experience in Python, machine learning, and cloud computing.",
            "Example 2: Marketing manager skilled in digital campaigns, SEO, and content creation.",
            "Example 3: Project coordinator with expertise in Agile methodologies and team leadership."
        ]
        st.warning("⚠️ Please enter valid input before searching. Here are some sample descriptions you can copy and paste:")
        for desc in sample_descriptions:
            st.code(desc)
    else:
        with st.spinner("Processing your request..."):
            try:
                search_response = search(
                    query=user_input,
                    top_k=top_k,
                    debug=False,
                    include_explanations=show_explanations,
                    do_rerank=enable_rerank
                )

                rewritten_query = search_response.get("rewritten_query", "")
                results = search_response.get("results", [])
                fallback_msg = search_response.get("fallback", None)

            except Exception as e:
                st.error(f"❌ Search failed: {e}")
                results = []
                rewritten_query = ""
                fallback_msg = None

        if rewritten_query:
            st.info(f"📝 AI Rewritten Query:\n\n{rewritten_query}")

        if results:
            st.success(f"🎯 Top {len(results)} recommended assessments:")
            for idx, item in enumerate(results[:top_k], 1):
                name = item.get('Assessment Name', 'Untitled')
                url = item.get('URL', '#')

                from streamlit.components.v1 import html

                assessment_name = item.get('Assessment Name', 'Untitled')
                assessment_url = item.get('URL', '#')

                # Inline button that looks like a link
                html(f"""
                    <div style="margin-bottom: 0.5em">
                        <a href="{assessment_url}" target="_blank" style="
                        text-decoration: none;
                        color: #2a9d8f;
                        font-size: 20px;
                        font-weight: 600;
                        font-family: 'Arial, sans-serif';
                        ">{idx}. {assessment_name}</a>
                    </div>
                    """, height=30)


                st.markdown(f"- **Job Levels**: {item.get('Job Levels', 'N/A')}")

                test_type_raw = item.get('Test Type(s)', 'N/A')
                test_type_list = [t.strip() for t in test_type_raw.split(',')]
                unique_test_types = ', '.join(sorted(set(test_type_list)))
                st.markdown(f"- **Test Type(s)**: {unique_test_types}")

                st.markdown(f"- **Remote Testing Support**: {item.get('Remote Testing Support', 'N/A')}")
                st.markdown(f"- **Adaptive Support**: {item.get('Adaptive Support', 'N/A')}")
                st.markdown(f"- **IRT Support**: {item.get('IRT Support', 'N/A')}")
                st.markdown(f"- **Duration**: {item.get('Duration', 'N/A')}")
                st.markdown(f"- **Description**:\n> {item.get('Description', '')[:1000]}...\n")

                if show_explanations and "LLM Explanation" in item:
                    st.markdown(f"🧠 **AI Explanation:**\n> {item['LLM Explanation']}")
                st.markdown("<hr style='border: 1px solid #6A5ACD;'>", unsafe_allow_html=True)


        elif fallback_msg and enable_fallback:
            st.warning(f"🤖 {fallback_msg}")

        else:
            st.warning("😕 No relevant assessments found. Try rephrasing or simplifying your input.")
