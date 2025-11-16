// AI Job Recommendation Bot - Frontend Application

class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusText = document.getElementById('statusText');
        
        this.sessionId = this.generateSessionId();
        this.messageHistory = [];
        this.apiBaseURL = 'http://localhost:5000/api';
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.sendButton.addEventListener('click', () => this.handleSend());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSend();
            }
        });
        
        // Check backend connection
        this.checkBackendConnection();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.apiBaseURL}/health`);
            if (response.ok) {
                this.statusText.textContent = '✅ Connected to backend';
                this.statusText.style.color = '#4caf50';
            }
        } catch (error) {
            this.statusText.textContent = '⚠️ Backend not connected - Demo mode';
            this.statusText.style.color = '#ff9800';
        }
    }
    
    async handleSend() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Display user message
        this.displayMessage(message, 'user');
        this.chatInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Simulate bot response (demo mode)
        setTimeout(() => {
            this.hideTypingIndicator();
            this.handleDemoResponse(message);
        }, 1000);
    }
    
    handleDemoResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();
        
        // Demo skill extraction
        if (lowerMessage.includes('python') || lowerMessage.includes('javascript') || 
            lowerMessage.includes('react') || lowerMessage.includes('skill')) {
            
            const response = `Great! I can see you have skills in programming. Here's what I extracted:
            
📋 <strong>Your Skills:</strong>
${this.extractSkillsDemo(userMessage)}

Now, tell me:
• How many years of experience do you have?
• What type of job are you looking for? (remote, hybrid, onsite)
• What's your preferred location?`;
            
            this.displayMessage(response, 'bot');
        }
        else if (lowerMessage.match(/\d+\s*(year|yr)/)) {
            const response = `Perfect! Based on your profile, let me find some matching jobs for you...

🔍 <strong>Searching job boards...</strong>

<em>(Note: Backend is not running yet. To see real job recommendations, we need to complete the implementation and start the Flask server.)</em>

Would you like me to continue building the remaining modules?`;
            
            this.displayMessage(response, 'bot');
        }
        else {
            const response = `I understand. To help you find the best jobs, I need to know about your skills first.

Could you tell me what programming languages, frameworks, or tools you know?

For example: "I know Python, JavaScript, React, and Docker"`;
            
            this.displayMessage(response, 'bot');
        }
    }
    
    extractSkillsDemo(text) {
        const skills = [];
        const skillKeywords = {
            'python': 'Python',
            'javascript': 'JavaScript',
            'js': 'JavaScript',
            'react': 'React',
            'reactjs': 'React',
            'node': 'Node.js',
            'nodejs': 'Node.js',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'aws': 'AWS',
            'java': 'Java',
            'typescript': 'TypeScript',
            'sql': 'SQL',
            'mongodb': 'MongoDB',
            'git': 'Git'
        };
        
        const lowerText = text.toLowerCase();
        for (const [keyword, skillName] of Object.entries(skillKeywords)) {
            if (lowerText.includes(keyword) && !skills.includes(skillName)) {
                skills.push(skillName);
            }
        }
        
        if (skills.length === 0) {
            return '• <em>No specific skills detected. Please mention your technical skills.</em>';
        }
        
        return skills.map(skill => `• ${skill}`).join('\n');
    }
    
    displayMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = message;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // Store in history
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
    
    displayJobCards(jobs) {
        let html = '<strong>🎯 Top Job Matches:</strong><br><br>';
        
        jobs.forEach((job, index) => {
            html += `
                <div class="job-card">
                    <h3>${job.title}</h3>
                    <p><strong>Company:</strong> ${job.company}</p>
                    <p><strong>Location:</strong> ${job.location}</p>
                    <p><strong>Salary:</strong> ${job.salary || 'Not specified'}</p>
                    <span class="match-score">${job.matchScore}% Match</span>
                </div>
            `;
        });
        
        this.displayMessage(html, 'bot');
    }
}

// Initialize the chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 AI Job Bot initialized');
    new ChatInterface();
});
