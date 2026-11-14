"""Home overview: scope metrics and overall takeaways."""

import streamlit as st

from lib.content import OVERALL_TAKEAWAYS, SCOPE
from lib.ui import render_disclaimer

st.title(SCOPE["title"])
st.write(SCOPE["blurb"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Respondent rows", f"{SCOPE['respondent_rows']:,}")
m2.metric("Primary quantitative n", f"{SCOPE['primary_n']:,}")
m3.metric("Q15 responses", f"{SCOPE['q15_n']:,}")
m4.metric("Survey years", SCOPE["years"])

st.divider()
st.subheader("Overall takeaways")
for item in OVERALL_TAKEAWAYS:
    st.markdown(f"- {item}")

st.divider()
st.markdown(
    """
Use the sidebar to move through the report:

1. **Data and methods** — sample sizes, denominators, and limitations  
2. **Outcomes and skills** — Figures 1–2  
3. **Associations** — Figure 3  
4. **Predictor models** — Figures 4–7  
5. **Activities and themes** — Figures 8 and 10  
6. **Trends and quality** — Figures 9 and 11  
"""
)

render_disclaimer()
