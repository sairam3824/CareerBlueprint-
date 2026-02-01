// AI Job Recommendation Bot - Frontend Application

class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusText = document.getElementById('statusText');

        this.sessionId = this.generateSessionId();
        this.messageHistory = [];
        this.apiBaseURL = '/api';
        this.backendAvailable = false;

        // Conversation state machine
        this.state = 'greeting';
        this.profile = {
            email: '',
            name: '',
            skills: [],
            experience_years: 0,
            preferred_locations: [],
            preferred_job_types: []
        };

        this.init();
    }

    init() {
        this.sendButton.addEventListener('click', () => this.handleSend());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSend();
            }
        });

        this.checkBackendConnection();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.apiBaseURL}/health`);
            if (response.ok) {
                this.backendAvailable = true;
                this.statusText.textContent = 'Connected to backend';
                this.statusText.style.color = '#4caf50';
            }
        } catch (error) {
            this.backendAvailable = false;
            this.statusText.textContent = 'Backend not connected - Demo mode';
            this.statusText.style.color = '#ff9800';
        }
    }

    async handleSend() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        this.displayMessage(message, 'user');
        this.chatInput.value = '';
        this.showTypingIndicator();

        if (!this.backendAvailable) {
            setTimeout(() => {
                this.hideTypingIndicator();
                this.handleDemoResponse(message);
            }, 800);
            return;
        }

        try {
            await this.processState(message);
        } catch (error) {
            console.error('Error processing message:', error);
            this.hideTypingIndicator();
            this.displayMessage('Something went wrong. Please try again.', 'bot');
        }
    }

    async processState(message) {
        switch (this.state) {
            case 'greeting':
                this.hideTypingIndicator();
                this.state = 'skills_input';
                this.displayMessage(
                    'Great, let\'s get started! Tell me about your technical skills. ' +
                    'For example: <em>"I know Python, JavaScript, React, and Docker"</em>',
                    'bot'
                );
                break;

            case 'skills_input':
                await this.handleSkillsInput(message);
                break;

            case 'experience_input':
                this.handleExperienceInput(message);
                break;

            case 'location_input':
                this.handleLocationInput(message);
                break;

            case 'preferences_input':
                this.handlePreferencesInput(message);
                break;

            case 'email_input':
                await this.handleEmailInput(message);
                break;

            case 'recommendations':
                await this.handlePostRecommendations(message);
                break;

            default:
                this.hideTypingIndicator();
                this.state = 'skills_input';
                this.displayMessage('Tell me about your skills so I can find jobs for you.', 'bot');
        }
    }

    async handleSkillsInput(message) {
        try {
            const response = await fetch(`${this.apiBaseURL}/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();
            this.hideTypingIndicator();

            if (!response.ok) {
                this.displayMessage('I couldn\'t process that. Please list your skills separated by commas.', 'bot');
                return;
            }

            const skills = data.data?.skills || [];
            if (skills.length === 0) {
                this.displayMessage(
                    'I couldn\'t detect any specific skills. Please mention them directly, e.g. ' +
                    '<em>"Python, JavaScript, React, SQL"</em>',
                    'bot'
                );
                return;
            }

            this.profile.skills = skills.map(s => s.name);
            const skillList = skills.map(s =>
                `<strong>${s.name}</strong> <span style="color:var(--text-secondary)">(${s.category})</span>`
            ).join('<br>');

            this.displayMessage(
                `I found these skills:<br><br>${skillList}<br><br>` +
                'How many years of professional experience do you have?',
                'bot'
            );
            this.state = 'experience_input';
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Skills extraction error:', error);
            this.displayMessage('There was an error extracting skills. Please try again.', 'bot');
        }
    }

    handleExperienceInput(message) {
        this.hideTypingIndicator();
        const years = parseInt(message.replace(/[^0-9]/g, ''), 10);
        if (isNaN(years) || years < 0 || years > 50) {
            this.displayMessage('Please enter a valid number of years (e.g. "3" or "5 years").', 'bot');
            return;
        }

        this.profile.experience_years = years;
        this.displayMessage(
            `Got it, ${years} years of experience. What is your preferred work location? ` +
            '(e.g. <em>"San Francisco"</em>, <em>"New York"</em>, or <em>"anywhere"</em>)',
            'bot'
        );
        this.state = 'location_input';
    }

    handleLocationInput(message) {
        this.hideTypingIndicator();
        const location = message.trim();
        if (location.toLowerCase() === 'anywhere' || location.toLowerCase() === 'any') {
            this.profile.preferred_locations = [];
        } else {
            this.profile.preferred_locations = [location];
        }

        this.displayMessage(
            'What type of job do you prefer?<br>' +
            '<strong>1.</strong> Remote<br>' +
            '<strong>2.</strong> Hybrid<br>' +
            '<strong>3.</strong> Onsite<br>' +
            '<strong>4.</strong> No preference',
            'bot'
        );
        this.state = 'preferences_input';
    }

    handlePreferencesInput(message) {
        this.hideTypingIndicator();
        const lower = message.toLowerCase().trim();
        const typeMap = { '1': 'remote', '2': 'hybrid', '3': 'onsite', '4': '' };
        let jobType = typeMap[lower] || '';
        if (!jobType && ['remote', 'hybrid', 'onsite'].includes(lower)) {
            jobType = lower;
        }
        this.profile.preferred_job_types = jobType ? [jobType] : [];

        this.displayMessage(
            'Last step - what is your email address? ' +
            'This is used to save your profile and track applications.',
            'bot'
        );
        this.state = 'email_input';
    }

    async handleEmailInput(message) {
        const email = message.trim();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            this.hideTypingIndicator();
            this.displayMessage('That doesn\'t look like a valid email. Please try again.', 'bot');
            return;
        }

        this.profile.email = email;

        // Create profile on backend
        try {
            await fetch(`${this.apiBaseURL}/profile/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: this.profile.email,
                    name: this.profile.name,
                    skills: this.profile.skills,
                    experience: this.profile.experience_years,
                    locations: this.profile.preferred_locations,
                    job_types: this.profile.preferred_job_types
                })
            });
        } catch (e) {
            console.error('Profile creation error:', e);
        }

        this.hideTypingIndicator();
        this.displayMessage('Searching for matching jobs based on your profile...', 'bot');
        this.showTypingIndicator();

        await this.fetchRecommendations();
    }

    async fetchRecommendations() {
        try {
            const response = await fetch(`${this.apiBaseURL}/recommendations/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile: {
                        skills: this.profile.skills,
                        experience_years: this.profile.experience_years,
                        preferred_locations: this.profile.preferred_locations,
                        preferred_job_types: this.profile.preferred_job_types
                    },
                    limit: 5
                })
            });

            const data = await response.json();
            this.hideTypingIndicator();

            if (!response.ok) {
                this.displayMessage(`Could not generate recommendations: ${data.error || 'Unknown error'}`, 'bot');
                this.state = 'recommendations';
                return;
            }

            const recs = data.recommendations || [];
            const gaps = data.skill_gaps || [];

            if (recs.length === 0) {
                this.displayMessage(
                    'No job listings were found right now. This may be because API keys are not configured. ' +
                    'Try again later or adjust your skills.',
                    'bot'
                );
                this.state = 'recommendations';
                return;
            }

            this.displayJobCards(recs);

            if (gaps.length > 0) {
                this.displaySkillGaps(gaps);
            }

            this.displayMessage(
                'You can:<br>' +
                '- Click <strong>Apply</strong> on any job card above<br>' +
                '- Type <strong>"history"</strong> to see your application history<br>' +
                '- Type <strong>"more"</strong> to search again with different criteria',
                'bot'
            );
            this.state = 'recommendations';
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Recommendation fetch error:', error);
            this.displayMessage('Failed to fetch recommendations. The backend may have encountered an error.', 'bot');
            this.state = 'recommendations';
        }
    }

    async handlePostRecommendations(message) {
        const lower = message.toLowerCase().trim();
        this.hideTypingIndicator();

        if (lower === 'history') {
            await this.showApplicationHistory();
        } else if (lower === 'more') {
            this.state = 'skills_input';
            this.displayMessage('Tell me your updated skills and I\'ll search again.', 'bot');
        } else {
            this.displayMessage(
                'Type <strong>"history"</strong> to view your applications, or <strong>"more"</strong> to start a new search.',
                'bot'
            );
        }
    }

    async showApplicationHistory() {
        if (!this.profile.email) {
            this.displayMessage('No email on file. Please start a new conversation to set up your profile.', 'bot');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseURL}/applications/history/${encodeURIComponent(this.profile.email)}`);
            const data = await response.json();

            const apps = data.applications || [];
            const stats = data.stats || {};

            if (apps.length === 0) {
                this.displayMessage('You haven\'t submitted any applications yet.', 'bot');
                return;
            }

            let html = `<strong>Application History</strong> (${apps.length} total)<br><br>`;
            apps.forEach(app => {
                const statusClass = (app.status || 'pending').toLowerCase();
                html += `<div class="job-card">
                    <h3>${app.job_title || 'Unknown'}</h3>
                    <p><strong>Company:</strong> ${app.company || 'N/A'}</p>
                    <p><strong>Applied:</strong> ${app.timestamp || 'N/A'}</p>
                    <span class="status-badge ${statusClass}">${app.status || 'pending'}</span>
                </div>`;
            });

            if (stats.total) {
                html += `<br><strong>Stats:</strong> ${stats.submitted || 0} submitted, ` +
                    `${stats.pending || 0} pending, ${stats.failed || 0} failed`;
            }

            this.displayMessage(html, 'bot');
        } catch (error) {
            console.error('History fetch error:', error);
            this.displayMessage('Could not retrieve application history.', 'bot');
        }
    }

    async applyToJob(job, buttonEl) {
        if (!this.profile.email) {
            this.displayMessage('Please complete the conversation first so I have your email.', 'bot');
            return;
        }

        buttonEl.disabled = true;
        buttonEl.textContent = 'Applying...';

        try {
            const response = await fetch(`${this.apiBaseURL}/applications/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: this.profile.email,
                    user_name: this.profile.name,
                    job_title: job.title,
                    company: job.company,
                    location: job.location,
                    salary: job.salary_min ? `$${job.salary_min} - $${job.salary_max}` : '',
                    job_url: job.url || '',
                    skills_matched: this.profile.skills
                })
            });

            const data = await response.json();

            if (response.ok) {
                buttonEl.textContent = 'Applied';
                buttonEl.classList.add('applied');
                this.displayMessage(
                    `Application submitted for <strong>${job.title}</strong> at <strong>${job.company}</strong>. ` +
                    `Reference: <code>${data.reference}</code>`,
                    'bot'
                );
            } else {
                buttonEl.disabled = false;
                buttonEl.textContent = 'Apply';
                this.displayMessage(`Application failed: ${data.error || 'Unknown error'}`, 'bot');
            }
        } catch (error) {
            console.error('Apply error:', error);
            buttonEl.disabled = false;
            buttonEl.textContent = 'Apply';
            this.displayMessage('Failed to submit application. Please try again.', 'bot');
        }
    }

    // --- Demo mode fallback ---

    handleDemoResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();

        if (lowerMessage.includes('python') || lowerMessage.includes('javascript') ||
            lowerMessage.includes('react') || lowerMessage.includes('skill')) {
            const response = `Great! I can see you have skills in programming. Here's what I extracted:

<strong>Your Skills:</strong>
${this.extractSkillsDemo(userMessage)}

<em>(Demo mode - start the backend for full functionality)</em>

Now, tell me:
- How many years of experience do you have?
- What type of job are you looking for? (remote, hybrid, onsite)
- What's your preferred location?`;
            this.displayMessage(response, 'bot');
        } else if (lowerMessage.match(/\d+\s*(year|yr)/)) {
            this.displayMessage(
                'Thanks! In demo mode I can\'t fetch real jobs. ' +
                'Start the Flask server with <code>python app.py</code> and reload the page for the full experience.',
                'bot'
            );
        } else {
            this.displayMessage(
                'I understand. To help you find the best jobs, tell me your skills first. ' +
                'For example: <em>"I know Python, JavaScript, React, and Docker"</em>',
                'bot'
            );
        }
    }

    extractSkillsDemo(text) {
        const skills = [];
        const skillKeywords = {
            'python': 'Python', 'javascript': 'JavaScript', 'js': 'JavaScript',
            'react': 'React', 'reactjs': 'React', 'node': 'Node.js',
            'nodejs': 'Node.js', 'docker': 'Docker', 'kubernetes': 'Kubernetes',
            'aws': 'AWS', 'java': 'Java', 'typescript': 'TypeScript',
            'sql': 'SQL', 'mongodb': 'MongoDB', 'git': 'Git'
        };

        const lowerText = text.toLowerCase();
        for (const [keyword, skillName] of Object.entries(skillKeywords)) {
            if (lowerText.includes(keyword) && !skills.includes(skillName)) {
                skills.push(skillName);
            }
        }

        if (skills.length === 0) {
            return '<em>No specific skills detected. Please mention your technical skills.</em>';
        }
        return skills.map(skill => `- ${skill}`).join('<br>');
    }

    // --- Display helpers ---

    displayMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = message;

        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;

        this.messageHistory.push({ sender, message, timestamp: new Date() });
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message';
        typingDiv.id = 'typingIndicator';

        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';

        typingDiv.appendChild(indicator);
        this.chatMessages.appendChild(typingDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    displayJobCards(recommendations) {
        let html = '<strong>Top Job Matches:</strong><br>';

        recommendations.forEach((rec, index) => {
            const job = rec.job || {};
            const score = rec.match_score || 0;
            const matching = rec.matching_skills || [];
            const explanation = rec.explanation || '';
            const salary = job.salary_min
                ? `$${Number(job.salary_min).toLocaleString()} - $${Number(job.salary_max).toLocaleString()}`
                : 'Not specified';

            html += `
                <div class="job-card" id="job-card-${index}">
                    <h3>${job.title || 'Untitled'}</h3>
                    <p><strong>Company:</strong> ${job.company || 'Unknown'}</p>
                    <p><strong>Location:</strong> ${job.location || 'N/A'}${job.remote ? ' (Remote)' : ''}</p>
                    <p><strong>Salary:</strong> ${salary}</p>
                    <p style="font-size:13px;color:var(--text-secondary)">${explanation}</p>
                    <div class="actions">
                        <span class="match-score">${score}% Match</span>
                        <button class="apply-btn" data-job-index="${index}">Apply</button>
                    </div>
                </div>
            `;
        });

        this.displayMessage(html, 'bot');

        // Attach click handlers to Apply buttons
        recommendations.forEach((rec, index) => {
            const btn = document.querySelector(`[data-job-index="${index}"]`);
            if (btn) {
                btn.addEventListener('click', () => this.applyToJob(rec.job || {}, btn));
            }
        });
    }

    displaySkillGaps(gaps) {
        let html = '<strong>Skill Gaps to Consider:</strong><br>';

        gaps.forEach(gap => {
            const impactClass = `impact-${gap.impact || 'low'}`;
            html += `
                <div class="skill-gap-card">
                    <span class="skill-name">${gap.skill}</span>
                    &mdash; <span class="${impactClass}">${gap.impact || 'low'} impact</span>
                    <div class="learning-time">Estimated learning time: ${gap.learning_time || 'varies'}</div>
                </div>
            `;
        });

        this.displayMessage(html, 'bot');
    }
}

// Initialize the chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('AI Job Bot initialized');
    new ChatInterface();
});
