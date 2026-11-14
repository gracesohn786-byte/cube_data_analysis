"""Post-survey home overview: scope metrics and overall takeaways."""

import streamlit as st

from lib.post_content import OVERALL_TAKEAWAYS, SCOPE
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
Use the sidebar Post-survey pages to move through the report:

1. **Data and methods** — sample sizes, denominators, and limitations  
2. **Outcomes and skills** — Figures 1–2  
3. **Associations** — Figure 3  
4. **Enjoyment and benefit** — Figure 4  
5. **Activities and themes** — Figures 5 and 7  
6. **Trends and quality** — Figures 6 and 8  
"""
)

render_disclaimer(survey="post")
