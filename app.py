import gradio as gr
from query import ask

def handle_query(question):
    if not question.strip():
        return "Please enter a valid question.", ""
    try:
        result = ask(question)
        sources_text = "\n".join(f"• {s}" for s in result["sources"])
        return result["answer"], sources_text
    except Exception as e:
        return f"Error: {e}", ""

# Build Gradio Block query interface
with gr.Blocks(title="Columbia Grad Dining - Unofficial Guide") as demo:
    gr.Markdown("# 🎓 Columbia University Graduate Dining")
    gr.Markdown("### 🔍 The Unofficial Guide - Grounded RAG Query System")
    gr.Markdown(
        "Ask questions about graduate dining plan tiers, pricing, location limits, "
        "and real student experiences on campus."
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            inp = gr.Textbox(
                label="Your Question", 
                placeholder="e.g., Can I use the graduate meal plan swipes at Ferris Booth Commons?",
                lines=2
            )
            btn = gr.Button("Submit Query", variant="primary")
        
        with gr.Column(scale=3):
            answer = gr.Textbox(
                label="Grounded Answer (with citations)", 
                lines=8, 
                interactive=False
            )
            sources = gr.Textbox(
                label="Retrieved Sources", 
                lines=4, 
                interactive=False
            )
            
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])
    
    gr.Examples(
        examples=[
            ["What are the graduate meal plans and how much do they cost?"],
            ["Can I use my graduate meal plan swipes at John Jay or Ferris?"],
            ["What dining options are closest to Mudd for SEAS students?"],
            ["What happens if I run out of meals before the end of the term?"],
            ["Is a graduate meal plan worth it for an off-campus student?"],
            ["How is the housing lottery structured?"] # Out-of-scope query
        ],
        inputs=inp
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
