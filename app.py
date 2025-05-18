from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import traceback
import json
import sys
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_plans.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'your_secret_key_here'

db = SQLAlchemy(app)

# Model
class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subjects = db.Column(db.String(500), nullable=False)
    hours_per_day = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(500))
    plan_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

# Plan generator
def round_to_half(n):
    return round(n * 2) / 2

def generate_study_plan(subjects, hours_per_day, days, difficulty):
    total_hours = hours_per_day * days
    subject_weights = {'easy': 1, 'medium': 1.5, 'hard': 2}
    weighted_subjects = [(s, subject_weights.get(difficulty.get(s, 'medium'), 1)) for s in subjects]
    total_weight = sum(w for _, w in weighted_subjects) or 1
    subject_hours = {s: max(0.5, round_to_half((w / total_weight) * total_hours)) for s, w in weighted_subjects}
    current_date = datetime.now().date()
    study_plan = []

    for day in range(days):
        day_plan = {'date': (current_date + timedelta(days=day)).strftime('%Y-%m-%d'), 'subjects': []}
        available_subjects = [s for s, h in subject_hours.items() if h > 0]
        if not available_subjects:
            break
        num_subjects_today = min(3, len(available_subjects))
        subjects_today = random.sample(available_subjects, k=max(2, num_subjects_today)) if len(available_subjects) >= 2 else available_subjects
        hours_left_today = hours_per_day

        for subject in subjects_today:
            max_assignable = min(subject_hours[subject], hours_left_today)
            assigned_hours = round_to_half(min(max_assignable, 2.0))
            if assigned_hours < 0.5:
                assigned_hours = max_assignable
            if hours_left_today - assigned_hours < 0.5 and hours_left_today - assigned_hours > 0:
                assigned_hours = hours_left_today

            day_plan['subjects'].append({
                'name': subject,
                'hours': assigned_hours,
                'difficulty': difficulty.get(subject, 'medium'),
                'completed': False
            })

            subject_hours[subject] -= assigned_hours
            hours_left_today -= assigned_hours

            if hours_left_today <= 0:
                break

        study_plan.append(day_plan)

    return study_plan

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        subjects = [s.strip() for s in request.form.get('subjects', '').split(',') if s.strip()]
        if not subjects:
            flash('Please enter at least one subject', 'error')
            return redirect(url_for('index'))

        difficulty = {key.replace('difficulty_', '').replace('_', ' '): value
                      for key, value in request.form.items() if key.startswith('difficulty_')}

        try:
            hours_per_day = int(request.form.get('hours_per_day', 2))
            days = int(request.form.get('days', 7))
        except ValueError:
            flash('Please enter valid numbers for hours and days', 'error')
            return redirect(url_for('index'))

        study_plan = generate_study_plan(subjects, hours_per_day, days, difficulty)
        new_plan = StudyPlan(
            subjects=",".join(subjects),
            hours_per_day=hours_per_day,
            days=days,
            difficulty=",".join([f"{s}:{d}" for s, d in difficulty.items()]),
            plan_data=json.dumps(study_plan),
            created_at=datetime.now()
        )

        db.session.add(new_plan)
        db.session.commit()
        return render_template('plan.html', plan=study_plan, plan_id=new_plan.id)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        flash('An error occurred while generating your plan', 'error')
        return redirect(url_for('index'))

@app.route('/plans')
def view_plans():
    plans = StudyPlan.query.order_by(StudyPlan.created_at.desc()).all()
    return render_template('view_plans.html', plans=plans)

@app.route('/plan/<int:plan_id>')
def view_plan(plan_id):
    plan = StudyPlan.query.get_or_404(plan_id)
    try:
        study_plan = json.loads(plan.plan_data)
    except Exception:
        flash('Error loading study plan', 'error')
        return redirect(url_for('view_plans'))
    return render_template('plan.html', plan=study_plan, plan_id=plan.id)

@app.route('/analytics/<int:plan_id>')
def analytics(plan_id):
    plan_db = StudyPlan.query.get_or_404(plan_id)
    plan = json.loads(plan_db.plan_data)

    total_tasks = 0
    completed_tasks = 0
    total_hours = 0
    subject_total_hours = {}
    subject_completed_hours = {}

    for day in plan:
        for subject in day['subjects']:
            name = subject['name']
            hours = subject['hours']
            total_hours += hours
            total_tasks += 1
            subject_total_hours[name] = subject_total_hours.get(name, 0) + hours
            if subject.get('completed', False):
                subject_completed_hours[name] = subject_completed_hours.get(name, 0) + hours
                completed_tasks += 1

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks else 0

    return render_template(
        'analytics.html',
        total_hours=round(total_hours, 2),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate=round(completion_rate, 2),
        subject_total_hours=subject_total_hours,
        subject_completed_hours=subject_completed_hours,
        plan_id=plan_id
    )

@app.route('/delete/<int:plan_id>', methods=['POST'])
def delete_plan(plan_id):
    plan = StudyPlan.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    flash('Plan deleted successfully', 'success')
    return redirect(url_for('view_plans'))

@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        day_index = data.get('day_index')
        subject_index = data.get('subject_index')
        completed = data.get('completed')
        plan = StudyPlan.query.get(plan_id)
        if not plan:
            return jsonify({'success': False, 'message': 'Plan not found'}), 404
        study_plan = json.loads(plan.plan_data)
        study_plan[day_index]['subjects'][subject_index]['completed'] = completed
        plan.plan_data = json.dumps(study_plan)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ✅ Ensure DB tables are created
with app.app_context():
    db.create_all()

# ✅ Start the app only for local development
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
