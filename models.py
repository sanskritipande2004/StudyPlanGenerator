from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subjects = db.Column(db.String(500), nullable=False)
    hours_per_day = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(500), nullable=True)
    plan_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<StudyPlan {self.id}>'
