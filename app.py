import json
import random
from flask import flash
import os
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = '8963'

def load_vocabulary():
    try:
        with open('bank_vocab.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return [
            {"en": "Alma mater", "bn": "পুরানো পাঠ ক্রিত বিদ্যালয়"},
            {"en": "Panacea", "bn": "মহা ঔষধ"},
            {"en": "Topiary", "bn": "কাটার আর্ট"},
            {"en": "Relapse", "bn": "আরোগ্য লাভের পর আবার আক্রান্ত"}
        ]

vocabulary = load_vocabulary()

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        try:
            num_questions = int(request.form['num_questions'])
            if num_questions < 1 or num_questions > len(vocabulary):
                return render_template('home.html', vocab_size=len(vocabulary), error=f"Choose 1 to {len(vocabulary)} questions")

            selected = random.sample(vocabulary, num_questions)
            quiz = []
            all_bn = [item['bn'] for item in vocabulary]

            for item in selected:
                options = random.sample([bn for bn in all_bn if bn != item['bn']], 3)
                options.append(item['bn'])
                random.shuffle(options)

                quiz.append({
                    'en': item['en'],
                    'options': options,
                    'correct_answer': item['bn']
                })

            session['quiz_data'] = {
                'questions': quiz,
                'user_answers': [],
                'current_index': 0
            }

            return redirect(url_for('quiz'))

        except Exception as e:
            return render_template('home.html', vocab_size=len(vocabulary), error=str(e))

    return render_template('home.html', vocab_size=len(vocabulary))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    quiz_data = session.get('quiz_data')
    if not quiz_data:
        return redirect(url_for('home'))

    current = quiz_data['current_index']
    total = len(quiz_data['questions'])

    if request.method == 'POST':
        answer = request.form.get('option')
        skip = request.form.get('skip')

        if skip == 'true':
            quiz_data['user_answers'].append(None)
        elif answer:
            quiz_data['user_answers'].append(answer)

        quiz_data['current_index'] += 1
        session['quiz_data'] = quiz_data

        if quiz_data['current_index'] >= total:
            return redirect(url_for('results'))
        else:
            return redirect(url_for('quiz'))

    if current >= total:
        return redirect(url_for('results'))

    return render_template('quiz.html',
                           question=quiz_data['questions'][current],
                           index=current + 1,
                           total=total)

@app.route('/results')
def results():
    quiz_data = session.get('quiz_data')
    if not quiz_data:
        return redirect(url_for('home'))

    results = []
    for i, q in enumerate(quiz_data['questions']):
        user_answer = quiz_data['user_answers'][i]
        is_correct = (user_answer == q['correct_answer'])
        results.append({
            'question': q['en'],
            'user_answer': user_answer,
            'correct_answer': q['correct_answer'],
            'is_correct': is_correct,
            'skipped': user_answer is None
        })

    score = sum(1 for r in results if r['is_correct'])
    return render_template('results.html', results=results, score=score, total=len(results))



@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        english = request.form.get('english', '').strip()
        bengali = request.form.get('bengali', '').strip()

        if not english or not bengali:
            flash('Both fields are required.', 'error')
        else:
            new_entry = {"en": english, "bn": bengali}

            if os.path.exists('bank_vocab.json'):
                with open('bank_vocab.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []

            data.append(new_entry)

            with open('bank_vocab.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            flash('Vocabulary added successfully!', 'success')

    try:
        with open('bank_vocab.json', 'r', encoding='utf-8') as f:
            current_data = json.load(f)
    except FileNotFoundError:
        current_data = []

    return render_template('admin.html', vocab=current_data)
if __name__ == '__main__':
    app.run(debug=True)