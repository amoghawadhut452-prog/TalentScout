import streamlit as st
import re
import requests


HF_TOKEN = "your_token_here"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

st.set_page_config(page_title="TalentScout AI", layout="wide")

st.markdown("""
<style>
body {background-color: #0e1117;}
.stChatMessage {
    background-color: #1e1e1e !important;
    border-radius: 12px;
    padding: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("💼 TalentScout Hiring Assistant")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "step" not in st.session_state:
    st.session_state.step = 0

if "candidate" not in st.session_state:
    st.session_state.candidate = {}


def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def valid_phone(phone):
    return phone.isdigit() and len(phone) >= 10


MODELS = {
    "fast": "google/flan-t5-base",
    "balanced": "google/flan-t5-large"
}

def choose_model(experience):
    try:
        exp = int(experience)
    except:
        return MODELS["balanced"]

    if exp <= 2:
        return MODELS["fast"]
    else:
        return MODELS["balanced"]


def fallback_questions(tech_stack):
    techs = [t.strip() for t in tech_stack.split(",")]
    output = "## 🧪 Technical Questions\n"

    for tech in techs:
        output += f"\n### {tech}\n"
        output += f"- What is {tech}?\n"
        output += f"- How is {tech} used in real-world?\n"
        output += f"- What challenges exist in {tech}?\n"
        output += f"- Compare {tech} with alternatives\n"

    return output

def generate_questions(tech_stack, experience):
    model = choose_model(experience)
    api_url = f"https://api-inference.huggingface.co/models/{model}"

    prompt = f"""
You are a technical interviewer.

Candidate experience: {experience} years
Tech stack: {tech_stack}

For EACH technology generate:
- 1 basic question
- 2 intermediate questions
- 2 advanced questions
- 1 real-world scenario question

Make questions clear and structured.
"""

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": prompt},
            timeout=10
        )

        result = response.json()

        if isinstance(result, list):
            return "## 🧪 Technical Questions\n\n" + result[0]["generated_text"]

        return "⚠️ Model loading... using fallback.\n\n" + fallback_questions(tech_stack)

    except:
        return "⚠️ API failed. Using fallback.\n\n" + fallback_questions(tech_stack)


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if len(st.session_state.messages) == 0:
    greeting = """
Hello 👋 I'm your AI Hiring Assistant.

I will:
✔ Collect your details  
✔ Analyze your tech stack  
✔ Generate technical questions  

Type **exit** anytime.

👉 What is your full name?
"""
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.rerun()

user_input = st.chat_input("Type your answer...")

if user_input and user_input.lower() in ["exit", "quit", "stop"]:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "✅ Thank you! Our team will contact you."
    })
    st.rerun()

def process(user_input):
    step = st.session_state.step
    c = st.session_state.candidate

    if step == 0:
        c["name"] = user_input
        st.session_state.step += 1
        return "📧 Enter your email:"

    elif step == 1:
        if not valid_email(user_input):
            return "❌ Invalid email"
        c["email"] = user_input
        st.session_state.step += 1
        return "📱 Phone number?"

    elif step == 2:
        if not valid_phone(user_input):
            return "❌ Invalid phone"
        c["phone"] = user_input
        st.session_state.step += 1
        return "💼 Years of experience?"

    elif step == 3:
        c["exp"] = user_input
        st.session_state.step += 1
        return "🎯 Desired position?"

    elif step == 4:
        c["role"] = user_input
        st.session_state.step += 1
        return "📍 Current location?"

    elif step == 5:
        c["location"] = user_input
        st.session_state.step += 1
        return "🧠 Enter your tech stack (comma separated):"

    elif step == 6:
        c["tech"] = user_input
        st.session_state.step += 1

        with st.spinner("Generating questions..."):
            questions = generate_questions(user_input, c["exp"])

        return questions

    else:
        return "✅ Screening complete. We will get back to you soon."


if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    reply = process(user_input)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    st.rerun()