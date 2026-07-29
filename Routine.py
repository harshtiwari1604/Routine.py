import pandas as pd
import streamlit as st
from supabase import create_client

# Page Configuration
st.set_page_config(
    page_title="Routine Manager Pro", page_icon="⏰", layout="wide"
)

# --- SECURE CREDENTIALS SETUP ---
SUPABASE_URL = "https://bqnmzwqayxetuhlygjim.supabase.co"
SUPABASE_KEY = "sb_publishable_CronO2VjYTyyHdV0iOkJWw_2BPsJeyz"


@st.cache_resource
def init_supabase():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

# --- PREMIUM STYLING ---
st.markdown(
    """
    <style>
        .main { background-color: #0b0f19; color: #ffffff; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: black; border: none; }
        .stButton>button:hover { opacity: 0.9; }
    </style>
""",
    unsafe_allow_html=True,
)

if "user" not in st.session_state:
  st.session_state.user = None

# --- AUTHENTICATION SCREEN ---
if not st.session_state.user:
  st.markdown(
      "<h1 style='text-align: center; color: #38ef7d;'>⏰ Routine Manager"
      " Pro</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='text-align: center; color: gray;'>Plan Your Day, Master Your"
      " Time</p>",
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 1.2, 1])
  with col2:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
      st.markdown("### Welcome Back")
      with st.form("login_form"):
        login_email = st.text_input("Email")
        login_pass = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
          try:
            res = supabase.auth.sign_in_with_password({
                "email": login_email,
                "password": login_pass,
            })
            st.session_state.user = res.user
            st.success("Login Successful!")
            st.rerun()
          except Exception as e:
            st.error(f"Login failed: {e}")

    with tab2:
      st.markdown("### Create Account")
      with st.form("signup_form"):
        signup_email = st.text_input("Email Address")
        signup_pass = st.text_input(
            "Create Password (min 6 chars)", type="password"
        )
        signup_btn = st.form_submit_button("Sign Up")

        if signup_btn:
          try:
            res = supabase.auth.sign_up({
                "email": signup_email,
                "password": signup_pass,
            })
            st.success(
                "Account created! Check your email to verify or try logging"
                " in."
            )
          except Exception as e:
            st.error(f"Signup failed: {e}")

else:
  current_user = st.session_state.user

  # Top Bar with Welcome Greeting & Logout
  col_h1, col_h2 = st.columns([3, 1])
  with col_h1:
    st.markdown(
        f"<h1>👋 Hello! <span style='font-size:15px;"
        f" color:#38ef7d;'>({current_user.email})</span></h1>",
        unsafe_allow_html=True,
    )
  with col_h2:
    if st.button("🚪 Logout"):
      supabase.auth.sign_out()
      st.session_state.user = None
      st.rerun()

  st.markdown("---")

  # --- FETCH ROUTINE TASKS FROM SUPABASE ---
  try:
    response = (
        supabase.table("routine_tasks")
        .select("*")
        .eq("user_id", current_user.id)
        .execute()
    )
    tasks_data = response.data
  except:
    tasks_data = []

  df = pd.DataFrame(tasks_data)

  # --- SIDEBAR: ADD NEW TASK ---
  st.sidebar.markdown("## 🕹️ Control Center")
  st.sidebar.markdown(f"**Logged in as:** {current_user.email}")
  st.sidebar.markdown("---")
  st.sidebar.markdown("### ➕ Add Daily Task")

  with st.sidebar.form("task_logger", clear_on_submit=True):
    task_time = st.text_input("Time / Slot (e.g. 08:00 AM - 09:00 AM)")
    task_name = st.text_input("Task Title (e.g. Study, Exercise)")
    category = st.selectbox(
        "Category",
        [
            "Study / Academics",
            "Fitness / Health",
            "Development / Coding",
            "Chores / Daily",
            "Rest / Leisure",
        ],
    )
    status = st.selectbox("Status", ["Pending", "Completed"])

    submitted = st.form_submit_button("Add to Routine")
    if submitted:
      if task_name:
        try:
          supabase.table("routine_tasks").insert({
              "user_id": current_user.id,
              "task_time": task_time,
              "task_name": task_name,
              "category": category,
              "status": status,
          }).execute()
          st.sidebar.success("Task Added!")
          st.rerun()
        except Exception as e:
          st.sidebar.error(f"Error saving: {e}")
      else:
        st.sidebar.error("Task title cannot be empty")

  # --- MAIN BODY ---
  col_left, col_right = st.columns([1.6, 1])

  with col_left:
    st.markdown("### 📅 Your Daily Schedule")
    if not df.empty and "task_name" in df:
      display_df = df[
          ["id", "task_time", "task_name", "category", "status"]
      ].rename(
          columns={
              "id": "Task ID",
              "task_time": "Time Slot",
              "task_name": "Task",
              "category": "Category",
              "status": "Status",
          }
      )
      with st.container(height=350):
        st.dataframe(
            display_df.drop(columns=["Task ID"]), use_container_width=True
        )
    else:
      st.info("No routine tasks added yet. Use the left sidebar to add one!")

  with col_right:
    st.markdown("### 📊 Routine Overview")
    if not df.empty and "status" in df:
      status_summary = df.groupby("status")["task_name"].count().reset_index()
      status_summary.columns = ["Status", "Count"]

      with st.container(height=350):
        st.bar_chart(status_summary, x="Status", y="Count", color="#38ef7d")
    else:
      st.warning("Analytics will appear once tasks are added.")

  # --- DELETE SPECIFIC TASK SECTION ---
  st.markdown("---")
  if not df.empty and "task_name" in df:
    with st.expander("🗑️ Delete / Modify Routine Tasks", expanded=False):
      task_options = {
          f"⏰ {row['task_time']} | 📌 {row['task_name']} ({row['status']})": row[
              "id"
          ]
          for index, row in df.iterrows()
      }

      selected_task = st.selectbox(
          "Select task to remove", options=list(task_options.keys())
      )

      if st.button("Delete Selected Task"):
        target_id = task_options[selected_task]
        try:
          supabase.table("routine_tasks").delete().eq("id", target_id).eq(
              "user_id", current_user.id
          ).execute()
          st.success("Task deleted successfully!")
          st.rerun()
        except Exception as e:
          st.error(f"Failed to delete: {e}")
