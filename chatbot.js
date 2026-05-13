// chatbot.js — DataWizard AI Analyst Chat (Gemini-Powered, Professional Grade)

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════
    //  State
    // ═══════════════════════════════════════════════════
    let conversationHistory = [];
    let isExpanded = false;
    let isStreaming = false;

    // ═══════════════════════════════════════════════════
    //  Markdown Renderer (Enhanced)
    // ═══════════════════════════════════════════════════
    function renderMarkdown(text) {
        if (!text) return '';
        let html = text;

        // Code blocks (``` ... ```)
        html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
            const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;').trim();
            const langLabel = lang ? `<div class="md-code-lang">${lang}</div>` : '';
            return `<div class="md-code-block">${langLabel}<pre><code>${escaped}</code></pre></div>`;
        });

        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');

        // Tables (Robust parsing)
        html = html.replace(/((?:\|.+\|(?:\r?\n|\r))+)/g, (match) => {
            const rows = match.trim().split('\n').filter(r => r.trim());
            if (rows.length < 2) return match;
            const isSep = (r) => /^\|[\s\-:|]+\|$/.test(r.trim());
            let headerRow = rows[0];
            let dataRows = rows.slice(1);
            if (dataRows.length > 0 && isSep(dataRows[0])) {
                dataRows = dataRows.slice(1);
            }
            const parseCells = (r) => r.split('|').slice(1, -1).map(c => c.trim());
            let tableHtml = '<div class="md-table-wrap"><table><thead><tr>';
            parseCells(headerRow).forEach(c => { tableHtml += `<th>${c}</th>`; });
            tableHtml += '</tr></thead><tbody>';
            dataRows.forEach(r => {
                if (!isSep(r)) {
                    tableHtml += '<tr>';
                    parseCells(r).forEach(c => { tableHtml += `<td>${c}</td>`; });
                    tableHtml += '</tr>';
                }
            });
            tableHtml += '</tbody></table></div>';
            return tableHtml;
        });

        // Headers
        html = html.replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
        html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

        // Bold & Italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Blockquotes
        html = html.replace(/^>\s?(.+)$/gm, '<blockquote class="md-blockquote">$1</blockquote>');

        // Horizontal rules
        html = html.replace(/^---$/gm, '<hr class="md-hr">');

        // Unordered lists
        html = html.replace(/^[\s]*[-*]\s+(.+)$/gm, '<li>$1</li>');
        html = html.replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul class="md-ul">$1</ul>');

        // Ordered lists
        html = html.replace(/^[\s]*\d+\.\s+(.+)$/gm, '<li>$1</li>');

        // Line breaks (Preserve empty lines effectively but avoid clutter)
        html = html.replace(/\n\n+/g, '<br><br>');
        html = html.replace(/\n/g, '<br>');

        // Clean up double <br> after block elements
        html = html.replace(/(<\/div>)<br>/g, '$1');
        html = html.replace(/(<\/table>)<br>/g, '$1');
        html = html.replace(/(<\/ul>)<br>/g, '$1');
        html = html.replace(/(<\/blockquote>)<br>/g, '$1');
        html = html.replace(/(<hr>)<br>/g, '$1');
        html = html.replace(/(<\/h[1-4]>)<br>/g, '$1');

        return html;
    }

    // ═══════════════════════════════════════════════════
    //  Init
    // ═══════════════════════════════════════════════════
    function initChatbot() {
        if (document.getElementById('dw-chat-widget')) return;

        const chatHTML = `
            <div id="dw-chat-widget">
                <button id="dw-chat-toggle" title="Chat with DataWizard AI">
                    <i class="fas fa-comment-dots"></i>
                </button>
                <div id="dw-chat-window">
                    <div class="dw-chat-header">
                        <div class="dw-chat-header-left">
                            <div class="dw-chat-avatar"><i class="fas fa-robot"></i></div>
                            <div class="dw-chat-header-info">
                                <div class="dw-chat-header-title">${typeof t === 'function' ? t('chatTitle') : 'DataWizard AI'}</div>
                                <div class="dw-chat-model-badge">Gemini 2.5 Pro</div>
                            </div>
                        </div>
                        <div class="dw-chat-header-actions">
                            <button class="dw-chat-header-btn" id="dw-btn-newchat" title="New Chat"><i class="fas fa-plus"></i></button>
                            <button class="dw-chat-header-btn" id="dw-btn-expand" title="Expand"><i class="fas fa-expand"></i></button>
                        </div>
                    </div>
                    <div id="dw-chat-body">
                        <div id="dw-welcome-screen" class="dw-welcome-screen">
                            <div class="dw-welcome-icon">🧙‍♂️</div>
                            <div class="dw-welcome-title">${typeof t === 'function' ? t('chatWelcomeTitle') : 'DataWizard AI Analyst'}</div>
                            <div class="dw-welcome-subtitle">${typeof t === 'function' ? t('chatWelcomeSub') : ''}</div>
                            <div class="dw-welcome-chips">
                                <button class="dw-welcome-chip" data-query="${typeof t === 'function' ? t('chatChip1Q') : ''}">${typeof t === 'function' ? t('chatChip1') : '💰 Calculate Total'}</button>
                                <button class="dw-welcome-chip" data-query="${typeof t === 'function' ? t('chatChip2Q') : ''}">${typeof t === 'function' ? t('chatChip2') : '🔮 Predict Trends'}</button>
                                <button class="dw-welcome-chip" data-query="${typeof t === 'function' ? t('chatChip3Q') : ''}">${typeof t === 'function' ? t('chatChip3') : '🔍 Outliers'}</button>
                                <button class="dw-welcome-chip" data-query="${typeof t === 'function' ? t('chatChip4Q') : ''}">${typeof t === 'function' ? t('chatChip4') : '📊 Statistical Summary'}</button>
                            </div>
                        </div>
                        <div id="dw-chat-messages" class="dw-chat-messages" style="display:none;"></div>
                    </div>
                    <div id="dw-suggestions-container"></div>
                    <div class="dw-chat-input-area">
                        <div class="dw-chat-input-wrap">
                            <textarea id="dw-chat-input" class="dw-chat-textarea" placeholder="${typeof t === 'function' ? t('chatPlaceholder') : ''}" rows="1"></textarea>
                        </div>
                        <button id="dw-chat-send" class="dw-chat-send" disabled title="Send">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', chatHTML);

        // Bind events
        const toggleBtn = document.getElementById('dw-chat-toggle');
        const chatWindow = document.getElementById('dw-chat-window');
        const chatInput = document.getElementById('dw-chat-input');
        const sendBtn = document.getElementById('dw-chat-send');
        const expandBtn = document.getElementById('dw-btn-expand');
        const newChatBtn = document.getElementById('dw-btn-newchat');

        toggleBtn.addEventListener('click', () => {
            chatWindow.classList.toggle('open');
            toggleBtn.classList.toggle('active');
            if (chatWindow.classList.contains('open')) {
                chatInput.focus();
                // Ensure correct file context when opened
                if(!getFileId() && !document.getElementById('dw-chat-messages').children.length) {
                    appendMessage(typeof t === 'function' ? t('chatNoFile') : '⚠️ Please upload a file first.', 'ai error');
                }
            }
        });

        chatInput.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 140) + 'px';
            sendBtn.disabled = this.value.trim() === '';
        });

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        sendBtn.addEventListener('click', sendMessage);

        expandBtn.addEventListener('click', () => {
            isExpanded = !isExpanded;
            chatWindow.classList.toggle('expanded', isExpanded);
            expandBtn.querySelector('i').className = isExpanded ? 'fas fa-compress' : 'fas fa-expand';
        });

        newChatBtn.addEventListener('click', () => {
            conversationHistory = [];
            const msgs = document.getElementById('dw-chat-messages');
            msgs.innerHTML = '';
            msgs.style.display = 'none';
            document.getElementById('dw-welcome-screen').style.display = 'flex';
            document.getElementById('dw-suggestions-container').innerHTML = '';
        });

        // Welcome chip clicks
        document.querySelectorAll('.dw-welcome-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                chatInput.value = chip.dataset.query;
                chatInput.dispatchEvent(new Event('input'));
                sendMessage();
            });
        });
    }

    // ═══════════════════════════════════════════════════
    //  Helpers
    // ═══════════════════════════════════════════════════
    function getFileId() {
        const params = new URLSearchParams(window.location.search);
        return params.get('id') || params.get('file_id') || localStorage.getItem('last_file_id');
    }

    function scrollToBottom() {
        const msgs = document.getElementById('dw-chat-messages');
        if (msgs) msgs.scrollTop = msgs.scrollHeight;
    }

    // ═══════════════════════════════════════════════════
    //  Send Message
    // ═══════════════════════════════════════════════════
    async function sendMessage() {
        const input = document.getElementById('dw-chat-input');
        const text = input.value.trim();
        if (!text || isStreaming) return;

        const fileId = getFileId();
        const msgs = document.getElementById('dw-chat-messages');
        const welcome = document.getElementById('dw-welcome-screen');

        // Show messages area, hide welcome
        welcome.style.display = 'none';
        msgs.style.display = 'flex';

        // Append user message
        appendMessage(text, 'user');
        conversationHistory.push({ role: 'user', content: text });

        // Clear input
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('dw-chat-send').disabled = true;
        document.getElementById('dw-suggestions-container').innerHTML = '';

        if (!fileId) {
            appendMessage(typeof t === 'function' ? t('chatNoFileData') : '⚠️ Please upload a data file first.', 'ai error');
            return;
        }

        // Show thinking indicator
        const thinkingEl = showThinking();
        isStreaming = true;

        try {
            const response = await fetch(`http://127.0.0.1:8000/ai/gemini-chat/${fileId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    conversation_history: conversationHistory.slice(0, -1) // exclude current msg
                })
            });

            removeThinking(thinkingEl);

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || (typeof t === 'function' ? t('chatServerError') : 'Server error'));
            }

            const data = await response.json();
            const aiText = data.response || (typeof t === 'function' ? t('chatNoResponse') : 'No response.');

            // Typewriter effect
            await typewriterAppend(aiText);
            conversationHistory.push({ role: 'assistant', content: aiText });

            // Show suggestions
            if (data.suggestions && data.suggestions.length > 0) {
                showSuggestions(data.suggestions);
            }

        } catch (error) {
            removeThinking(thinkingEl);
            console.error("Chat Error:", error);
            appendMessage((typeof t === 'function' ? t('chatConnError') : '⚠️ Connection error: ') + error.message, 'ai error');
        } finally {
            isStreaming = false;
        }
    }

    // ═══════════════════════════════════════════════════
    //  Append Message
    // ═══════════════════════════════════════════════════
    function appendMessage(text, type) {
        const msgs = document.getElementById('dw-chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = `dw-chat-msg ${type}`;

        if (type === 'user') {
            msgDiv.textContent = text;
        } else {
            // AI label
            const label = document.createElement('div');
            label.className = 'dw-msg-label';
            label.innerHTML = '<i class="fas fa-sparkles"></i> DataWizard AI';
            msgDiv.appendChild(label);

            // Content
            const content = document.createElement('div');
            content.className = 'dw-msg-content';
            content.innerHTML = renderMarkdown(text);
            msgDiv.appendChild(content);

            // Action buttons
            const actions = document.createElement('div');
            actions.className = 'dw-msg-actions';
            actions.innerHTML = `
                <button class="dw-msg-action-btn" onclick="navigator.clipboard.writeText(this.closest('.dw-chat-msg').querySelector('.dw-msg-content')?.innerText || '')">
                    <i class="fas fa-copy"></i> ${typeof t === 'function' ? t('chatCopy') : 'Copy'}
                </button>
            `;
            msgDiv.appendChild(actions);
        }

        msgs.appendChild(msgDiv);
        scrollToBottom();
        return msgDiv;
    }

    // ═══════════════════════════════════════════════════
    //  Typewriter Effect
    // ═══════════════════════════════════════════════════
    async function typewriterAppend(fullText) {
        const msgs = document.getElementById('dw-chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = 'dw-chat-msg ai';

        const label = document.createElement('div');
        label.className = 'dw-msg-label';
        label.innerHTML = '<i class="fas fa-sparkles"></i> DataWizard AI';
        msgDiv.appendChild(label);

        const content = document.createElement('div');
        content.className = 'dw-msg-content';
        msgDiv.appendChild(content);

        const cursor = document.createElement('span');
        cursor.className = 'dw-typewriter-cursor';
        msgDiv.appendChild(cursor);

        msgs.appendChild(msgDiv);

        // Stream characters in chunks for performance
        const chunkSize = 8;
        let rendered = '';
        for (let i = 0; i < fullText.length; i += chunkSize) {
            rendered += fullText.slice(i, i + chunkSize);
            content.innerHTML = renderMarkdown(rendered);
            scrollToBottom();
            await sleep(15);
        }

        // Final render & remove cursor
        content.innerHTML = renderMarkdown(fullText);
        cursor.remove();

        // Add actions
        const actions = document.createElement('div');
        actions.className = 'dw-msg-actions';
        actions.innerHTML = `
            <button class="dw-msg-action-btn" onclick="navigator.clipboard.writeText(this.closest('.dw-chat-msg').querySelector('.dw-msg-content')?.innerText || '')">
                <i class="fas fa-copy"></i> ${typeof t === 'function' ? t('chatCopy') : 'Copy'}
            </button>
        `;
        msgDiv.appendChild(actions);

        scrollToBottom();
    }

    function sleep(ms) {
        return new Promise(r => setTimeout(r, ms));
    }

    // ═══════════════════════════════════════════════════
    //  Thinking Indicator
    // ═══════════════════════════════════════════════════
    function showThinking() {
        const msgs = document.getElementById('dw-chat-messages');
        const el = document.createElement('div');
        el.className = 'dw-chat-msg ai dw-thinking-msg';
        el.innerHTML = `
            <div class="dw-thinking-indicator">
                <div class="dw-thinking-brain"><i class="fas fa-brain"></i></div>
                <div>
                    <div class="dw-thinking-text">${typeof t === 'function' ? t('chatThinking') : 'Reading data...'}</div>
                    <div class="dw-thinking-dots"><span></span><span></span><span></span></div>
                </div>
            </div>
        `;
        msgs.appendChild(el);
        scrollToBottom();
        return el;
    }

    function removeThinking(el) {
        if (el && el.parentNode) el.remove();
    }

    // ═══════════════════════════════════════════════════
    //  Suggestion Chips
    // ═══════════════════════════════════════════════════
    function showSuggestions(suggestions) {
        const container = document.getElementById('dw-suggestions-container');
        container.innerHTML = '';
        const row = document.createElement('div');
        row.className = 'dw-suggestions-row';

        suggestions.forEach(text => {
            const chip = document.createElement('button');
            chip.className = 'dw-suggestion-chip';
            chip.textContent = text;
            chip.addEventListener('click', () => {
                const input = document.getElementById('dw-chat-input');
                input.value = text;
                input.dispatchEvent(new Event('input'));
                sendMessage();
            });
            row.appendChild(chip);
        });

        container.appendChild(row);
    }

    // ═══════════════════════════════════════════════════
    //  Boot
    // ═══════════════════════════════════════════════════
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatbot);
    } else {
        initChatbot();
    }
})();
