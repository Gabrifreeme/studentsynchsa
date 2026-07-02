import gradio as gr
import json
import os

PROFILE_DATA_PATH = "profile_data.json"

def save_profile(name, email, phone):
    profile_data = {
        "name": name,
        "email": email,
        "phone": phone
    }
    try:
        if os.path.exists(PROFILE_DATA_PATH):
            with open(PROFILE_DATA_PATH, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        else:
            data = []

        data.append(profile_data)

        with open(PROFILE_DATA_PATH, "w") as f:
            json.dump(data, f, indent=4)

        return "Profile saved successfully!", profile_data
    except Exception as e:
        return f"Error saving profile: {e}", None

def load_profile():
    if os.path.exists(PROFILE_DATA_PATH):
        try:
            with open(PROFILE_DATA_PATH, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data[-1]
        except Exception as e:
            print(f"Error loading profile: {e}")
    return {"name": "", "email": "", "phone": ""}

initial_profile = load_profile()

with gr.Blocks() as demo:
    gr.Markdown("# Student Profile Setup")
    gr.Markdown("Enter your basic details below. This information will be used to auto-fill university applications.")

    with gr.Row():
        name = gr.Textbox(label="Full Name", value=initial_profile.get("name", ""))
        email = gr.Textbox(label="Email Address", value=initial_profile.get("email", ""))
        phone = gr.Textbox(label="Phone Number", value=initial_profile.get("phone", ""))

    submit_button = gr.Button("Save Profile")
    output_message = gr.Textbox(label="Status")

    submit_button.click(
        fn=save_profile,
        inputs=[name, email, phone],
        outputs=output_message
    )

    clear_button = gr.Button("Clear Form")
    clear_button.click(lambda: ["", "", ""], inputs=None, outputs=[name, email, phone])

if __name__ == "__main__":
    demo.launch()
