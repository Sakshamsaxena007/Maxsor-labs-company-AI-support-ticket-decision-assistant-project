"""Streamlit Frontend"""
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="MaxsorLabs Support Assistant", page_icon="🎫", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ---------------- Sidebar: session status ----------------
with st.sidebar:
    st.title("🎫 Support Assistant")
    if st.session_state.token:
        st.success(f"Logged in as {st.session_state.email}")
        if st.button("Log out"):
            st.session_state.token = None
            st.session_state.email = None
            st.rerun()
    else:
        st.info("Not logged in")

# ---------------- Not logged in -> Show Login/Register ----------------
if not st.session_state.token:
    st.header("Login / Register")
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pw")
            submitted = st.form_submit_button("Log in")
            if submitted:
                r = requests.post(f"{API_BASE}/login", json={"email": email, "password": password})
                if r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    st.session_state.email = email
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Login failed"))

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password (min 6 chars)", type="password", key="reg_pw")
            submitted = st.form_submit_button("Create account")
            if submitted:
                r = requests.post(f"{API_BASE}/register", json={"email": email, "password": password})
                if r.status_code == 201:
                    st.success("Account created! Please log in.")
                else:
                    st.error(r.json().get("detail", "Registration failed"))

# ---------------- Logged in -> Main app ----------------
else:
    tab_new, tab_history = st.tabs(["New Decision", "History"])

    with tab_new:
        st.header("Submit a Support Ticket")
        with st.form("ticket_form"):
            message = st.text_area("Describe the issue", height=100,
                                    placeholder="e.g. My order arrived damaged yesterday.")
            col1, col2 = st.columns(2)
            with col1:
                order_value = st.number_input("Order value (₹)", min_value=0.0, step=100.0)
                days_since_delivery = st.number_input("Days since delivery", min_value=0, step=1, value=0)
                product_type = st.selectbox("Product type", ["non_food", "food", "mixed", "unknown"])
            with col2:
                days_since_dispatch = st.number_input("Days since dispatch", min_value=0, step=1, value=0)
                opened_status = st.selectbox("Item opened?", ["unopened", "opened", "unknown"])
                order_status = st.selectbox("Order status", ["delivered", "dispatched", "processing", "unknown"])

            submitted = st.form_submit_button("Get AI Decision")

            if submitted:
                if not message.strip():
                    st.warning("Please describe the issue.")
                else:
                    payload = {
                        "message": message,
                        "order_value_inr": order_value or None,
                        "days_since_delivery": days_since_delivery or None,
                        "days_since_dispatch": days_since_dispatch or None,
                        "product_type": product_type,
                        "opened_status": opened_status,
                        "order_status": order_status,
                    }
                    with st.spinner("Retrieving policy + asking the model..."):
                        r = requests.post(f"{API_BASE}/tickets", json=payload, headers=auth_headers())

                    if r.status_code == 201:
                        decision = r.json()["decision"]
                        st.success(f"**Action:** {decision['action']}")
                        st.metric("Confidence", f"{decision['confidence']:.0%}")
                        st.write(f"**Reason:** {decision['reason']}")
                        st.write(f"**Sources:** {', '.join(decision['sources'])}")
                    else:
                        st.error(r.json().get("detail", "Something went wrong"))

    with tab_history:
        st.header("Your Previous Tickets")
        r = requests.get(f"{API_BASE}/tickets", headers=auth_headers())
        if r.status_code == 200:
            tickets = r.json()
            if not tickets:
                st.info("No tickets yet. Submit one in the 'New Decision' tab.")
            for t in tickets:
                label = f"#{t['id']} · {t['message'][:50]}"
                with st.expander(label):
                    st.write(f"**Message:** {t['message']}")
                    st.write(f"**Submitted:** {t['created_at']}")
                    decision = t.get("decision")
                    if decision:
                        st.write(f"**Action:** {decision['action']}")
                        st.write(f"**Confidence:** {decision['confidence']:.0%}")
                        st.write(f"**Reason:** {decision['reason']}")
                        st.write(f"**Sources:** {', '.join(decision['sources'])}")
        else:
            st.warning("No decision recorded for this ticket.")
           