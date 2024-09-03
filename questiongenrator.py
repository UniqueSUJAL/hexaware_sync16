from flask import Flask, render_template, request
import ollama

app = Flask(__name__)

def generate_questions_with_ollama(description, num_questions):
    questions = set()

    for i in range(num_questions):
        prompt = f"Generate a unique question based on the following context:\n\n{description}"

        try:
            response = ollama.chat(model="llama2", messages=[{"role": "user", "content": prompt}])

            # Extract the question from the response
            if isinstance(response, dict) and 'message' in response and 'content' in response['message']:
                question = response['message']['content'].strip()

                # Remove unwanted prefix if present
                unwanted_phrases = [
                    "Sure, here's a unique question based on the provided context:",
                    "Here's a unique question based on the provided context:"
                ]
                for phrase in unwanted_phrases:
                    if question.startswith(phrase):
                        question = question[len(phrase):].strip()

                # Add the cleaned question to the set
                if question:
                    questions.add(question)
                else:
                    questions.add(f"No content generated for request {i + 1}.")
            else:
                questions.add(f"Unexpected response structure for request {i + 1}: {response}")

        except Exception as e:
            questions.add(f"An error occurred for request {i + 1}: {e}")

    return list(questions)

@app.route("/", methods=["GET", "POST"])
def home():
    questions = None

    if request.method == "POST":
        description = request.form.get("description")
        num_questions = int(request.form.get("num_questions"))
        if description:
            questions = generate_questions_with_ollama(description, num_questions)
    
    return render_template("questiongenratorpage.html", questions=questions)

if __name__ == "__main__":
    app.run(debug=True)
