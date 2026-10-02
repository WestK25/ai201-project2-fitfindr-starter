"""Local Gradio interface: search, outfit and shareable fit card."""
import os
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def _format_session(session):
    if session["error"]:
        return session["error"], "", ""
    item = session["selected_item"]
    listing = (f"{item['title']}\n${item['price']:.2f} · {item['platform']} · {item['condition']}\n"
               f"Size: {item['size']}\nBrand: {item['brand'] or 'Not listed'}\n"
               f"Colors: {', '.join(item['colors'])}\n\n{item['description']}\n\n"
               "Classroom mock listing; not live inventory.")
    return listing, session["outfit_suggestion"], session["fit_card"]


def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """Preserve starter's three strings: listing, outfit suggestion, fit card."""
    if not isinstance(user_query, str) or not user_query.strip():
        return "Enter an item, for example: vintage graphic tee under $30, size M.", "", ""
    wardrobe = get_example_wardrobe() if wardrobe_choice == "Example wardrobe" else get_empty_wardrobe()
    return _format_session(run_agent(user_query, wardrobe))


EXAMPLE_QUERIES = ["vintage graphic tee under $30, size M", "90s track jacket in size M",
                   "flowy midi skirt under $40", "black combat boots size 8",
                   "designer ballgown size XXS under $5"]


def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("# FitFindr\nFind your next secondhand look. Describe a piece, add a size or budget, and see how to wear it.")
        with gr.Row():
            query_input = gr.Textbox(label="What are you looking for?", placeholder=EXAMPLE_QUERIES[0], lines=2, scale=3)
            wardrobe_choice = gr.Radio(choices=["Example wardrobe", "Empty wardrobe (new user)"], value="Example wardrobe", label="Wardrobe", scale=1)
        submit_btn = gr.Button("Find my fit", variant="primary")
        with gr.Row():
            listing_output = gr.Textbox(label="Your find", lines=12, interactive=False)
            outfit_output = gr.Textbox(label="How to wear it", lines=12, interactive=False)
            fitcard_output = gr.Textbox(label="Your fit card", lines=12, interactive=False)
        gr.Examples(examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES], inputs=[query_input, wardrobe_choice])
        for event in (submit_btn.click, query_input.submit):
            event(fn=handle_query, inputs=[query_input, wardrobe_choice], outputs=[listing_output, outfit_output, fitcard_output])
    return demo


if __name__ == "__main__":
    build_interface().launch(server_name="127.0.0.1", share=False)
