# utils/qa_generator.py

import random

def generate_mcqs(text):
    sentences = text.split(". ")
    mcqs = []

    for i in range(min(5, len(sentences))):
        q = sentences[i].strip()
        if len(q.split()) > 6:
            answer = q.split()[-1].strip(".,")
            options = random.sample(["Python", "Machine", "AI", answer, "Code"], 4)
            random.shuffle(options)

            mcqs.append({
                "question": f"What is related to: {q[:40]}...?",
                "options": options,
                "answer": answer
            })

    return mcqs

def generate_short_answers(text):
    sentences = text.split(". ")
    questions = []

    for i in range(min(3, len(sentences))):
        q = sentences[i].strip()
        if len(q.split()) > 5:
            questions.append({
                "question": f"Explain: {q[:50]}...",
                "answer": q
            })

    return questions
