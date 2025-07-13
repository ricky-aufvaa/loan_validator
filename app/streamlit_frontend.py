import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(
    page_title="DSCR Loan Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .status-pass {
        color: #28a745;
        font-weight: bold;
    }
    .status-fail {
        color: #dc3545;
        font-weight: bold;
    }
    .json-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# API endpoint
API_URL = "http://localhost:8000/agent"

# Sidebar Navigation
st.markdown('<h1 class="main-header">🏠 DSCR Loan Assistant</h1>', unsafe_allow_html=True)
feature = st.sidebar.selectbox("Select Feature", ["Finance Q&A", "Loan Validation"])

# Tab: Finance Q&A
if feature == "Finance Q&A":
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 💬 Finance Q&A")
    st.markdown("Ask any questions about DSCR loans, eligibility criteria, or loan guidelines.")
    st.markdown('</div>', unsafe_allow_html=True)

    question = st.text_area("Enter your question:", placeholder="e.g., What are the FICO score requirements?", height=150)
    if st.button("🔍 Ask Question", type="primary") and question.strip():
        with st.spinner("Getting response from backend..."):
            try:
                response = requests.post(API_URL, json={"query": question})
                data = response.json()
                print("result is-------",data)
                if "response" in data:
                    st.markdown("### 📝 Answer")
                    st.markdown(data["response"])
                elif "validation_result" in data:
                    st.markdown("### 📝 Answer")
                    result = data.get("validation_result", {})

                    if result.get("is_eligible"):
                            st.success("✅ **ELIGIBLE** - The loan application meets all requirements!")
                    else:
                            st.error("❌ **NOT ELIGIBLE** - Some requirements were not met.")

                    if "validation_summary" in result:
                            for item in result["validation_summary"]:
                                status = item.get("status", "N/A")
                                rule_name = item.get("rule_checked", "N/A")

                                with st.expander(f"{rule_name} - {status}"):
                                    if status == "PASS":
                                        st.markdown(f"**Status:** <span style='color:#28a745; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"**Status:** <span style='color:#dc3545; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)

                                    st.markdown(f"**Applicant Value:** {item.get('applicant_value', 'N/A')}")
                                    st.markdown(f"**Required Value:** {item.get('required_value', 'N/A')}")
                                    st.markdown(f"**Reasoning:** {item.get('reasoning', 'N/A')}")

                    with st.expander("🔍 Raw JSON Response"):
                            st.markdown('<div class="json-container">', unsafe_allow_html=True)
                            st.json(result)
                            st.markdown('</div>', unsafe_allow_html=True) 
                else:
                    st.error("Unexpected response format:")
                    st.json(data)
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")

# Tab: Loan Validation
elif feature == "Loan Validation":
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### ✅ Loan Application Validator")
    st.markdown("Validate a loan application against DSCR loan guidelines.")
    st.markdown('</div>', unsafe_allow_html=True)

    input_method = st.radio("Choose input method:", ["Form Input", "JSON Input"])

    if input_method == "Form Input":
        with st.form("loan_form"):
            col1, col2 = st.columns(2)
            with col1:
                loan_type = st.selectbox("Loan Type", ["Purchase", "Rate/Term", "Cash-Out Refinance"])
                property_type = st.selectbox("Property Type", ["Single-Family", "Multi-Family", "Condo", "Townhouse"])
                units = st.number_input("Number of Units", min_value=1, max_value=4, value=1)
                occupancy = st.selectbox("Occupancy", ["Non-Owner-Occupied", "Owner-Occupied"])
                borrower_type = st.selectbox("Borrower Type", ["U.S. Citizen", "Permanent Resident", "LLC", "Trust"])
            with col2:
                loan_amount = st.number_input("Loan Amount ($)", min_value=0, value=500000)
                appraised_value = st.number_input("Appraised Value ($)", min_value=0, value=750000)
                borrower_fico_score = st.number_input("FICO Score", min_value=300, max_value=850, value=720)
                dscr_calculated = st.number_input("DSCR Calculated", min_value=0.0, max_value=3.0, value=1.2, step=0.1)
                liquid_reserves_months = st.number_input("Liquid Reserves (months)", min_value=0, value=6)
            property_location_state = st.selectbox("Property State", 
                ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", 
                 "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", 
                 "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"])
            col3, col4 = st.columns(2)
            with col3:
                is_interest_only = st.checkbox("Interest Only")
                using_short_term_rental_income = st.checkbox("Using Short-term Rental Income")
            with col4:
                cash_out_amount = st.number_input("Cash Out Amount ($)", min_value=0, value=0)
            submitted = st.form_submit_button("🔍 Validate Application", type="primary")

            if submitted:
                payload = {
                    "query": {
                        "loan_type": loan_type,
                        "property_type": property_type,
                        "units": units,
                        "occupancy": occupancy,
                        "loan_amount": loan_amount,
                        "appraised_value": appraised_value,
                        "borrower_fico_score": borrower_fico_score,
                        "dscr_calculated": dscr_calculated,
                        "liquid_reserves_months": liquid_reserves_months,
                        "borrower_type": borrower_type,
                        "property_location_state": property_location_state,
                        "is_interest_only": is_interest_only,
                        "using_short_term_rental_income": using_short_term_rental_income,
                        "cash_out_amount": cash_out_amount
                    }
                }

                with st.spinner("Validating loan application..."):
                    try:
                        response = requests.post(API_URL, json=payload)
                        data = response.json()
                        result = data.get("validation_result", {})

                        if result.get("is_eligible"):
                            st.success("✅ **ELIGIBLE** - The loan application meets all requirements!")
                        else:
                            st.error("❌ **NOT ELIGIBLE** - Some requirements were not met.")

                        if "validation_summary" in result:
                            for item in result["validation_summary"]:
                                status = item.get("status", "N/A")
                                rule_name = item.get("rule_checked", "N/A")

                                with st.expander(f"{rule_name} - {status}"):
                                    if status == "PASS":
                                        st.markdown(f"**Status:** <span style='color:#28a745; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"**Status:** <span style='color:#dc3545; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)

                                    st.markdown(f"**Applicant Value:** {item.get('applicant_value', 'N/A')}")
                                    st.markdown(f"**Required Value:** {item.get('required_value', 'N/A')}")
                                    st.markdown(f"**Reasoning:** {item.get('reasoning', 'N/A')}")

                        with st.expander("🔍 Raw JSON Response"):
                            st.markdown('<div class="json-container">', unsafe_allow_html=True)
                            st.json(result)
                            st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Error validating application: {e}")

    elif input_method == "JSON Input":
        sample_json = {
            "loan_type": "Purchase",
            "property_type": "Single-Family",
            "units": 1,
            "occupancy": "Non-Owner-Occupied",
            "loan_amount": 750000,
            "appraised_value": 1000000,
            "borrower_fico_score": 760,
            "dscr_calculated": 1.1,
            "liquid_reserves_months": 4,
            "borrower_type": "U.S. Citizen",
            "property_location_state": "California",
            "is_interest_only": False,
            "using_short_term_rental_income": False,
            "cash_out_amount": 0
        }

        json_input = st.text_area("Enter loan application JSON:", value=json.dumps(sample_json, indent=2), height=400)
        if st.button("🔍 Validate Loan", type="primary"):
            try:
                payload = {"query": json.loads(json_input)}
                with st.spinner("Validating loan application..."):
                    response = requests.post(API_URL, json=payload)
                    data = response.json()
                    result = data.get("validation_result", {})

                    if result.get("is_eligible"):
                        st.success("✅ **ELIGIBLE** - The loan application meets all requirements!")
                    else:
                        st.error("❌ **NOT ELIGIBLE** - Some requirements were not met.")

                    if "validation_summary" in result:
                        for item in result["validation_summary"]:
                            status = item.get("status", "N/A")
                            rule_name = item.get("rule_checked", "N/A")

                            with st.expander(f"{rule_name} - {status}"):
                                if status == "PASS":
                                    st.markdown(f"**Status:** <span style='color:#28a745; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**Status:** <span style='color:#dc3545; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)

                                st.markdown(f"**Applicant Value:** {item.get('applicant_value', 'N/A')}")
                                st.markdown(f"**Required Value:** {item.get('required_value', 'N/A')}")
                                st.markdown(f"**Reasoning:** {item.get('reasoning', 'N/A')}")

                    with st.expander("🔍 Raw JSON Response"):
                        st.markdown('<div class="json-container">', unsafe_allow_html=True)
                        st.json(result)
                        st.markdown('</div>', unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please correct it before submitting.")