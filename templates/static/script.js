document.addEventListener('DOMContentLoaded', function() {
    // Handle subject input to show difficulty options
    const subjectsInput = document.getElementById('subjects');
    const difficultyContainer = document.getElementById('difficultyContainer');
    
    if (subjectsInput && difficultyContainer) {
        subjectsInput.addEventListener('input', function() {
            const subjects = this.value.split(',').map(s => s.trim()).filter(s => s);
            
            let html = '<div class="mb-3"><label class="form-label">Subject Difficulty</label>';
            
            subjects.forEach((subject, index) => {
                html += `
                <div class="row mb-2">
                    <div class="col-6">
                        <label class="form-label">${subject}</label>
                    </div>
                    <div class="col-6">
                        <select class="form-select" name="difficulty_${subject}">
                            <option value="easy">Easy</option>
                            <option value="medium" selected>Medium</option>
                            <option value="hard">Hard</option>
                        </select>
                    </div>
                </div>
                `;
            });
            
            html += '</div>';
            difficultyContainer.innerHTML = subjects.length ? html : '';
        });
    }
    
    // Handle completion checkboxes
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const card = this.closest('.card');
            if (this.checked) {
                card.classList.add('border-success');
            } else {
                card.classList.remove('border-success');
            }
        });
    });
});