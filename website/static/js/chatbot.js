const chatbotCSS = `
   * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Inter", sans-serif;
        }

        :root {
            /* Primary color palette - Medical blue theme */
            --primary-color: #1e88e5;
            --primary-light: #42a5f5;
            --primary-dark: #1565c0;
            --primary-gradient: linear-gradient(135deg, var(--primary-light), var(--primary-dark));
            
            /* Secondary colors */
            --secondary-color: #f5f7fa; /* Light background */
            --background-color: #e8eef6; /* Subtle blue tint background */
            
            /* Text colors */
            --text-color: #2c3e50;
            --text-muted: #7f8c8d;
            --text-light: #95a5a6;
            --text-on-primary: #FFFFFF;

            /* Status colors */
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --error-color: #e74c3c;
            --info-color: #3498db;
            
            --white: #FFFFFF;
            
            /* Shadows */
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 12px rgba(30, 136, 229, 0.12);
            --shadow-lg: 0 8px 24px rgba(30, 136, 229, 0.15);

            /* Border radius */
            --border-radius-sm: 8px;
            --border-radius-md: 12px;
            --border-radius-lg: 16px;
            --border-radius-xl: 24px;
            --border-radius-pill: 100px;
            
            /* Transitions */
            --transition-fast: 0.15s ease;
            --transition-normal: 0.25s ease;
            --transition-slow: 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        body {
            width: 100%;
            min-height: 100vh;
            background-color: var(--background-color);
            color: var(--text-color);
            transition: background-color 0.3s ease;
        }

        /* Chatbot toggle button */
        #chatbot-toggler {
            position: fixed;
            bottom: 30px;
            right: 35px;
            border: none;
            height: 60px;
            width: 60px;
            display: flex;
            cursor: pointer;
            align-items: center;
            justify-content: center;
            border-radius: var(--border-radius-pill);
            background: var(--primary-gradient);
            color: var(--text-on-primary);
            box-shadow: var(--shadow-lg);
            transition: all var(--transition-slow);
            z-index: 10000;
        }

        #chatbot-toggler:hover {
            transform: scale(1.05);
            box-shadow: 0 12px 28px rgba(30, 136, 229, 0.25);
        }

        body.show-chatbot #chatbot-toggler {
            transform: rotate(90deg);
            background: var(--primary-dark);
        }

        #chatbot-toggler span {
            position: absolute;
            font-size: 28px;
            transition: opacity var(--transition-fast), transform var(--transition-normal);
        }
        
        #chatbot-toggler .chat-icon { 
            opacity: 1; 
            transform: scale(1);
        }
        
        #chatbot-toggler .close-icon { 
            opacity: 0; 
            transform: scale(0.5);
        }

        body.show-chatbot #chatbot-toggler .chat-icon { 
            opacity: 0; 
            transform: scale(0.5);
        }
        
        body.show-chatbot #chatbot-toggler .close-icon { 
            opacity: 1; 
            transform: scale(1);
        }

        /* Chatbot popup */
        .chatbot-popup {
            position: fixed;
            right: 35px;
            bottom: 100px;
            width: 380px;
            max-height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--white);
            border-radius: var(--border-radius-lg);
            opacity: 0;
            pointer-events: none;
            transform: translateY(30px) scale(0.95);
            transform-origin: bottom right;
            box-shadow: var(--shadow-lg);
            transition: opacity var(--transition-normal), transform var(--transition-slow);
            z-index: 9999;
        }

        body.show-chatbot .chatbot-popup {
            opacity: 1;
            pointer-events: auto;
            transform: translateY(0) scale(1);
            z-index: 20000;
        }

        /* Chat header */
        .chat-header {
            display: flex;
            align-items: center;
            padding: 16px 20px;
            background: var(--primary-gradient);
            color: var(--text-on-primary);
            justify-content: space-between;
            border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
            flex-shrink: 0;
        }

        .chat-header .header-info {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .header-info .chatbot-logo {
            width: 40px;
            height: 40px;
            padding: 7px;
            flex-shrink: 0;
            background: rgba(255,255,255,0.95);
            border-radius: var(--border-radius-pill);
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .header-info .chatbot-logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .header-info .logo-text {
            font-weight: 600;
            font-size: 1.2rem;
        }

        .chat-header .header-actions {
            display: flex;
            gap: 8px;
        }

        .chat-header .header-actions button {
            border: none;
            color: var(--text-on-primary);
            height: 38px;
            width: 38px;
            font-size: 22px;
            cursor: pointer;
            border-radius: var(--border-radius-pill);
            background: rgba(255, 255, 255, 0.15);
            transition: background-color var(--transition-fast), transform var(--transition-fast);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .chat-header .header-actions button:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        
        .chat-header .header-actions button:active {
            transform: scale(0.95);
        }

        /* Chat body */
        .chat-body {
            padding: 20px;
            gap: 18px;
            display: flex;
            flex-grow: 1;
            overflow-y: auto;
            flex-direction: column;
            scrollbar-width: thin;
            scrollbar-color: #D1D5DB transparent;
            background-color: var(--secondary-color);
            position: relative;
        }

        .chat-body::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-body::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .chat-body::-webkit-scrollbar-thumb {
            background-color: #D1D5DB;
            border-radius: var(--border-radius-pill);
            border: 2px solid var(--secondary-color);
        }

        /* Message bubbles */
        .chat-body .message {
            position: relative;
            max-width: 85%;
            display: flex;
            align-items: flex-end;
            gap: 10px;
        }

        .chat-body .bot-message {
            align-self: flex-start;
        }
        
        .chat-body .user-message {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .chat-body .bot-avatar {
            width: 36px;
            height: 36px;
            border-radius: var(--border-radius-pill);
            border: 2px solid var(--white);
            background-color: var(--white);
            box-shadow: var(--shadow-sm);
            flex-shrink: 0;
            object-fit: cover;
        }

        .message-content-wrapper {
            display: flex;
            flex-direction: column;
            max-width: calc(100% - 48px);
        }
        
        .user-message .message-content-wrapper {
            align-items: flex-end;
        }

        .chat-body .message .message-text {
            padding: 12px 18px;
            font-size: 0.95rem;
            line-height: 1.6;
            word-wrap: break-word;
            white-space: pre-wrap;
            border-radius: var(--border-radius-md);
            box-shadow: var(--shadow-sm);
        }

        .chat-body .bot-message .message-text {
            background: var(--white);
            color: var(--text-color);
            border-bottom-left-radius: 4px;
        }

        .chat-body .user-message .message-text {
            color: var(--text-on-primary);
            background: var(--primary-color);
            border-bottom-right-radius: 4px;
        }

        .message-time {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 6px;
            padding: 0 8px;
        }
        
        .user-message .message-time {
            align-self: flex-end;
        }

        /* Thinking indicator */
        .chat-body .bot-message .thinking-indicator {
            display: flex;
            gap: 5px;
            padding: 14px 18px;
            background: var(--white);
            border-radius: var(--border-radius-md);
            box-shadow: var(--shadow-sm);
            border-bottom-left-radius: 4px;
        }

        .chat-body .bot-message .thinking-indicator .dot {
            height: 8px;
            width: 8px;
            border-radius: 50%;
            background: var(--primary-light);
            animation: dotPulse 1.4s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite;
        }

        .chat-body .bot-message .thinking-indicator .dot:nth-child(1) { animation-delay: 0s; }
        .chat-body .bot-message .thinking-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
        .chat-body .bot-message .thinking-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dotPulse {
            0%, 80%, 100% { transform: scale(0.7); opacity: 0.6; }
            40% { transform: scale(1); opacity: 1; }
        }

        /* Quick replies */
        #quick-replies-container {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            padding: 12px 20px 16px 68px;
            background-color: var(--secondary-color);
        }

        .quick-reply {
            border: 1px solid rgba(30, 136, 229, 0.3);
            color: var(--primary-color);
            padding: 9px 18px;
            border-radius: var(--border-radius-pill);
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all var(--transition-normal);
            background-color: var(--white);
            box-shadow: var(--shadow-sm);
            outline: none;
        }

        .quick-reply:hover {
            background-color: var(--primary-light);
            border-color: var(--primary-light);
            color: var(--text-on-primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.2);
        }
        
        .quick-reply:active {
            transform: translateY(0px) scale(0.98);
            box-shadow: var(--shadow-sm);
        }

        /* Chat footer and form */
        .chat-footer {
            padding: 15px;
            border-top: 1px solid rgba(0, 0, 0, 0.08);
            background: var(--white);
            flex-shrink: 0;
        }

        .chat-form {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .chat-form .message-input-wrapper {
            flex-grow: 1;
            position: relative;
            background: var(--secondary-color);
            border-radius: var(--border-radius-pill);
            padding: 0 15px;
            transition: box-shadow var(--transition-fast);
        }
        
        .chat-form .message-input-wrapper:focus-within {
            box-shadow: 0 0 0 2px var(--primary-light);
        }

        .chat-form .message-input {
            width: 100%;
            min-height: 46px;
            max-height: 120px;
            outline: none;
            resize: none;
            border: none;
            background: transparent;
            font-size: 0.95rem;
            padding: 13px 0;
            line-height: 1.5;
            color: var(--text-color);
        }
        
        .chat-form .message-input::placeholder {
            color: var(--text-muted);
        }

        .chat-form .chat-controls {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chat-form .chat-controls button {
            height: 44px;
            width: 44px;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--border-radius-pill);
            background: transparent;
            color: var(--text-muted);
            transition: all var(--transition-fast);
        }
        
        .chat-form .chat-controls button:hover {
            color: var(--primary-color);
            background: rgba(30, 136, 229, 0.08);
        }
        
        .chat-form .chat-controls button:active {
            transform: scale(0.9);
        }

        #record-button.recording {
            color: var(--white);
            background: var(--error-color);
            animation: pulseRecord 1.5s infinite;
        }
        
        #record-button.recording:hover {
            background: #c0392b;
        }

        @keyframes pulseRecord {
            0% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.5); }
            70% { box-shadow: 0 0 0 8px rgba(231, 76, 60, 0); }
            100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }
        }

        #send-message {
            background: var(--primary-color) !important;
            color: var(--text-on-primary) !important;
        }
        
        #send-message:hover {
            background: var(--primary-dark) !important;
            transform: scale(1.05);
        }

        .chat-form .message-input:placeholder-shown + #send-message {
            display: none !important;
        }
        
        .chat-form .message-input:not(:placeholder-shown) + #send-message {
            display: flex !important;
        }

        #status {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-align: right;
            padding-top: 5px;
            min-height: 1.2em;
            transition: opacity 0.3s ease;
        }

        /* Health Info Cards */
        .health-info-card {
            background: white;
            border-radius: var(--border-radius-md);
            padding: 12px;
            margin-top: 4px;
            margin-bottom: 4px;
            border-left: 4px solid var(--primary-color);
            box-shadow: var(--shadow-sm);
            font-size: 0.9rem;
        }

        .health-info-card h4 {
            color: var(--primary-color);
            margin-bottom: 5px;
            font-weight: 600;
        }

        .health-info-card p {
            color: var(--text-color);
            margin-bottom: 0;
        }

        /* Animated wave background for header */
        .chat-header::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(90deg, 
                var(--primary-light), 
                var(--info-color), 
                var(--primary-dark), 
                var(--primary-light));
            background-size: 300% 100%;
            animation: gradientWave 12s ease-in-out infinite;
            z-index: 1;
            border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
        }

        @keyframes gradientWave {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Responsive styles */
        @media (max-width: 480px) {
            #chatbot-toggler {
                right: 20px;
                bottom: 20px;
                height: 55px;
                width: 55px;
            }

            .chatbot-popup {
                right: 0;
                bottom: 0;
                width: 100%;
                max-height: 100%;
                border-radius: 20px 20px 0 0;
                transform: translateY(100%);
            }
            
            body.show-chatbot .chatbot-popup {
                transform: translateY(0);
            }

            .chat-header { 
                padding: 14px 16px; 
                border-radius: 20px 20px 0 0;
            }
            
            .header-info .chatbot-logo { 
                width: 36px; 
                height: 36px; 
            }
            
            .header-info .logo-text { 
                font-size: 1.1rem; 
            }
            
            .chat-header .header-actions button { 
                height: 32px; 
                width: 32px; 
                font-size: 20px; 
            }

            .chat-body {
                padding: 15px;
            }
            
            #quick-replies-container {
                padding: 10px 15px 12px 58px;
            }

            .chat-body .message { 
                max-width: 90%; 
            }
            
            .chat-body .bot-avatar { 
                width: 32px; 
                height: 32px; 
            }
            
            .message-content-wrapper { 
                max-width: calc(100% - 42px); 
            }

            .chat-footer { 
                padding: 12px; 
            }
            
            .chat-form .message-input-wrapper { 
                padding: 0 12px; 
            }
            
            .chat-form .message-input { 
                min-height: 42px; 
                padding: 11px 0; 
                font-size: 0.9rem;
            }
            
            .chat-form .chat-controls button { 
                height: 38px; 
                width: 38px; 
            }
            
            #status { 
                display: none; 
            }
        }
`;

// Helper function to create DOM elements
function createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag);
    for (const key in attributes) {
        if (key === 'className') {
            element.className = attributes[key];
        } else if (key === 'textContent') {
            element.textContent = attributes[key];
        } else if (key === 'innerHTML') {
            element.innerHTML = attributes[key];
        } else if (key === 'style') {
            for(const styleKey in attributes[key]) {
                element.style[styleKey] = attributes[key][styleKey];
            }
        }
         else {
            element.setAttribute(key, attributes[key]);
        }
    }
    children.forEach(child => {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else if (child) { // Ensure child is not null or undefined
            element.appendChild(child);
        }
    });
    return element;
}

function buildChatbotUI() {
    // Add Meta Tags
    if (!document.querySelector('meta[charset="UTF-8"]')) {
        document.head.appendChild(createElement('meta', { charset: 'UTF-8' }));
    }
    if (!document.querySelector('meta[name="viewport"]')) {
        document.head.appendChild(createElement('meta', { name: 'viewport', content: 'width=device-width, initial-scale=1.0' }));
    }
    document.title = "AI Health Assistant";

    // Add Font Links
    if (!document.querySelector('link[href*="fonts.googleapis.com/css2?family=Poppins"]')) {
        document.head.appendChild(createElement('link', { 
            href: 'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap', 
            rel: 'stylesheet' 
        }));
    }
    if (!document.querySelector('link[href*="fonts.googleapis.com/css2?family=Material+Symbols+Rounded"]')) {
        document.head.appendChild(createElement('link', { 
            href: 'https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200', 
            rel: 'stylesheet' 
        }));
    }
     // Add Inter font if specifically needed by CSS and not covered by Poppins as primary
    if (!document.querySelector('link[href*="fonts.googleapis.com/css2?family=Inter"]')) {
        document.head.appendChild(createElement('link', {
            href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
            rel: 'stylesheet'
        }));
    }


    // Add CSS Styles
    const styleTag = createElement('style', { type: 'text/css', textContent: chatbotCSS });
    document.head.appendChild(styleTag);

    // Create Chatbot Toggler Button
    const chatIconSpan = createElement('span', { className: 'material-symbols-rounded chat-icon', textContent: 'chat_bubble' });
    const closeIconSpan = createElement('span', { className: 'material-symbols-rounded close-icon', textContent: 'close' });
    const chatbotToggler = createElement('button', {
        id: 'chatbot-toggler',
        'aria-label': 'Toggle Chatbot'
    }, [chatIconSpan, closeIconSpan]);
    document.body.appendChild(chatbotToggler);

    // Create Chatbot Popup
    // Header
    const chatbotLogoImg = createElement('img', { src: 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', alt: 'Chatbot Logo' });
    const chatbotLogoDiv = createElement('div', { className: 'chatbot-logo' }, [chatbotLogoImg]);
    const logoTextH2 = createElement('h2', { className: 'logo-text', id: 'chatbot-heading', textContent: 'AI Assistant' });
    const headerInfoDiv = createElement('div', { className: 'header-info' }, [chatbotLogoDiv, logoTextH2]);

    const resetChatButton = createElement('button', { id: 'resetChatHistory', className: 'material-symbols-rounded', title: 'Reset Chat', 'aria-label': 'Reset Chat History', textContent: 'refresh' });
    const closeChatbotBtn = createElement('button', { id: 'close-chatbot', className: 'material-symbols-rounded', title: 'Close Chat', 'aria-label': 'Close Chat Window', textContent: 'close' });
    const headerActionsDiv = createElement('div', { className: 'header-actions' }, [resetChatButton, closeChatbotBtn]);

    const chatHeaderDiv = createElement('div', { className: 'chat-header' }, [headerInfoDiv, headerActionsDiv]);

    // Chat Body
    const chatBodyDiv = createElement('div', { id: 'chat-box', className: 'chat-body', role: 'log', 'aria-live': 'polite' });

    // Quick Replies Container
    const quickRepliesContainerDiv = createElement('div', { id: 'quick-replies-container', 'aria-label': 'Quick Reply Options' });

    // Chat Footer
    const userInputTextarea = createElement('textarea', { placeholder: 'Type your message...', className: 'message-input', id: 'user-input', rows: '1', 'aria-label': 'Message Input' });
    const messageInputWrapperDiv = createElement('div', { className: 'message-input-wrapper' }, [userInputTextarea]);

    const recordButtonElem = createElement('button', { type: 'button', id: 'record-button', className: 'material-symbols-rounded', title: 'Voice Input', 'aria-label': 'Start Voice Input', textContent: 'mic' });
    const sendMessageButton = createElement('button', { type: 'submit', id: 'send-message', className: 'material-symbols-rounded', title: 'Send Message', 'aria-label': 'Send Message', textContent: 'send' });
    const chatControlsDiv = createElement('div', { className: 'chat-controls' }, [recordButtonElem, sendMessageButton]);
    
    const chatForm = createElement('form', { action: '#', className: 'chat-form', id: 'chat-form', 'aria-label': 'Chat Input Form' }, [messageInputWrapperDiv, chatControlsDiv]);
    const statusDisplayDiv = createElement('div', { id: 'status', role: 'status', textContent: 'Ready' });
    const chatFooterDiv = createElement('div', { className: 'chat-footer' }, [chatForm, statusDisplayDiv]);

    const chatbotPopupDiv = createElement('div', {
        className: 'chatbot-popup',
        role: 'complementary',
        'aria-labelledby': 'chatbot-heading'
    }, [chatHeaderDiv, chatBodyDiv, quickRepliesContainerDiv, chatFooterDiv]);
    document.body.appendChild(chatbotPopupDiv);
}


// --- Chatbot Functionality (Original Script Logic) ---
function initializeChatbotFunctionality() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const recordButton = document.getElementById('record-button');
    const statusDiv = document.getElementById('status');
    const toggler = document.getElementById('chatbot-toggler');
    const closeButton = document.getElementById('close-chatbot');
    const resetButton = document.getElementById('resetChatHistory');
    const quickRepliesContainer = document.getElementById('quick-replies-container');
    const chatForm = document.getElementById('chat-form'); // Get the form element

    let recognition;
    let currentAudio = null;
    let isRecording = false; // Moved isRecording here for proper scope

    const API_BASE_URL = 'http://127.0.0.1:5000';

    function playAudio(base64Audio) {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }
        try {
            const byteCharacters = atob(base64Audio);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const audioBlob = new Blob([byteArray], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(audioBlob);
            currentAudio = new Audio(audioUrl);
            currentAudio.play().catch(e => console.error("Error playing audio:", e));
        } catch (e) {
            console.error("Error decoding base64 audio:", e);
        }
    }

    async function fetchInitialGreeting() {
        showThinking();
        try {
            const response = await fetch(`${API_BASE_URL}/reset_chat_interaction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            removeThinking();
            if (data.bot_response_text) {
                addMessage(data.bot_response_text, false);
                if (data.bot_audio_base64) {
                    // playAudio(data.bot_audio_base64); // Uncomment if auto-play on greeting is desired
                }
                renderQuickReplies(["Check Symptoms", "Ask about appointments", "General health question"]);
            } else {
                addMessage("Error: Could not load initial greeting.", false);
            }
        } catch (error) {
            removeThinking();
            console.error('Error fetching initial greeting:', error);
            addMessage(`Failed to connect. Please try again later. (${error.message})`, false);
        }
    }

    let isFirstOpen = true;
    if (toggler) {
        toggler.addEventListener('click', () => {
            const isShowing = document.body.classList.toggle('show-chatbot');
            toggler.setAttribute('aria-expanded', isShowing.toString());
            if (isShowing) {
                if(userInput) userInput.focus();
                if (isFirstOpen) {
                    fetchInitialGreeting();
                    isFirstOpen = false;
                }
            }
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', () => {
            document.body.classList.remove('show-chatbot');
            if(toggler) toggler.setAttribute('aria-expanded', 'false');
        });
    }

    if (resetButton) {
        resetButton.addEventListener('click', async () => {
            if(chatBox) chatBox.innerHTML = '';
            if(quickRepliesContainer) quickRepliesContainer.innerHTML = '';
            if (statusDiv) statusDiv.textContent = 'Resetting...';
            showThinking();
            try {
                const response = await fetch(`${API_BASE_URL}/reset_chat_interaction`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
                if (!response.ok) throw new Error(`HTTP error! ${response.status}`);
                const data = await response.json();
                removeThinking();
                if (data.bot_response_text) {
                    addMessage(data.bot_response_text, false);
                    if (data.bot_audio_base64) {
                        // playAudio(data.bot_audio_base64);
                    }
                }
                renderQuickReplies(["Check Symptoms", "Ask about appointments", "General health question"]);
                if (statusDiv) statusDiv.textContent = 'Ready';
            } catch (error) {
                removeThinking();
                console.error('Error resetting chat:', error);
                addMessage(`Error resetting chat: ${error.message}`, false);
                if (statusDiv) statusDiv.textContent = 'Error';
            }
        });
    }

    function addMessage(text, isUser = false, time = null) {
        if (!chatBox) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'bot-message');

        const currentTime = time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Basic sanitization for display as HTML (newline to <br>)
        const sanitizedText = text.replace(/&/g, "&")
                                  .replace(/</g, "<")
                                  .replace(/>/g, ">")
                                  .replace(/"/g, "")
                                  .replace(/'/g, "'")
                                  .replace(/\n/g, "<br>");

        if (isUser) {
            messageDiv.innerHTML = `
                <div class="message-content-wrapper">
                    <div class="message-text">${sanitizedText}</div>
                    <div class="message-time">${currentTime}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <img class="bot-avatar" src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="Bot Avatar">
                <div class="message-content-wrapper">
                    <div class="message-text">${sanitizedText}</div>
                    <div class="message-time">${currentTime}</div>
                </div>
            `;
        }
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function showThinking() {
        if (!chatBox || document.getElementById('thinking-indicator')) return;
        const thinkingMessageDiv = document.createElement('div');
        thinkingMessageDiv.classList.add('message', 'bot-message', 'thinking');
        thinkingMessageDiv.id = 'thinking-indicator';
        thinkingMessageDiv.setAttribute('aria-label', 'AI is thinking');
        thinkingMessageDiv.innerHTML = `
            <img class="bot-avatar" src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="Bot Avatar">
            <div class="message-content-wrapper">
                <div class="thinking-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        chatBox.appendChild(thinkingMessageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeThinking() {
        const thinkingDiv = document.getElementById('thinking-indicator');
        if (thinkingDiv) {
            thinkingDiv.remove();
        }
    }

    function renderQuickReplies(replies) {
        if (!quickRepliesContainer) return;
        quickRepliesContainer.innerHTML = '';
        if (!replies || replies.length === 0) return;

        replies.forEach(replyText => {
            const button = document.createElement('button');
            button.classList.add('quick-reply');
            button.textContent = replyText;
            button.type = 'button';
            button.addEventListener('click', () => {
                if(userInput) {
                    userInput.value = replyText;
                    userInput.dispatchEvent(new Event('input', { bubbles: true }));
                    handleSendMessage();
                }
            });
            quickRepliesContainer.appendChild(button);
        });
        if(chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function handleSendMessage(event) {
        if (event) event.preventDefault();
        if (!userInput) return;

        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        userInput.value = '';
        userInput.style.height = 'auto';
        if(quickRepliesContainer) quickRepliesContainer.innerHTML = '';
        showThinking();
        if (statusDiv) statusDiv.textContent = 'AI is thinking...';

        try {
            const response = await fetch(`${API_BASE_URL}/chat_interaction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, speak: true })
            });

            removeThinking();
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: "Unknown server error" }));
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || response.statusText}`);
            }
            const data = await response.json();

            if (data.error) {
                addMessage(`Error: ${data.error}`, false);
            } else {
                addMessage(data.bot_response_text, false);
                if (data.bot_audio_base64) {
                    playAudio(data.bot_audio_base64);
                }

                if (data.current_stage === 'awaiting_initial_choice' || data.bot_response_text.toLowerCase().includes("anything else i can help")) {
                    renderQuickReplies(["Check Symptoms", "Ask about appointments", "General health question"]);
                } else if (data.current_stage === 'clarifying_symptom' && data.ambiguous_symptoms && Array.isArray(data.ambiguous_symptoms)) {
                     renderQuickReplies(data.ambiguous_symptoms.map((s,i) => `${i+1}) ${s.replace(/_/g, ' ')}`));
                } else if (data.current_stage === 'confirming_symptoms') {
                    renderQuickReplies(["Yes", "No"]);
                } else {
                    if(quickRepliesContainer) quickRepliesContainer.innerHTML = '';
                }
            }
        } catch (error) {
            removeThinking();
            console.error('Error sending message to backend:', error);
            addMessage(`Sorry, an error occurred: ${error.message}. Please try again.`, false);
        }
        if (statusDiv) statusDiv.textContent = 'Ready';
        if(userInput) userInput.focus();
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            if(recordButton) {
                recordButton.classList.add('recording');
                recordButton.setAttribute('aria-label', 'Stop Voice Input');
            }
            if (statusDiv) statusDiv.textContent = 'Listening...';
            isRecording = true;
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if(userInput) {
                userInput.value = transcript;
                userInput.dispatchEvent(new Event('input', { bubbles: true }));
                handleSendMessage();
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            let errorMsg = `Mic Error: ${event.error}`;
            if (event.error === 'no-speech') errorMsg = 'No speech detected.';
            else if (event.error === 'audio-capture') errorMsg = 'Mic problem. Check permissions.';
            else if (event.error === 'not-allowed') errorMsg = 'Mic access denied.';
            if (statusDiv) statusDiv.textContent = errorMsg;
        };

        recognition.onend = () => {
            if(recordButton) {
                recordButton.classList.remove('recording');
                recordButton.setAttribute('aria-label', 'Start Voice Input');
            }
            if (isRecording && statusDiv) statusDiv.textContent = 'Ready';
            isRecording = false;
        };

    } else {
        console.warn('Speech recognition not supported');
        if(recordButton) {
            recordButton.disabled = true;
            recordButton.title = "Speech recognition not supported";
        }
        if (statusDiv) statusDiv.textContent = 'Speech not supported';
    }

    if (recordButton) {
        recordButton.addEventListener('click', () => {
            if (!recognition) return;
            if (isRecording) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (error) {
                    console.error('Error starting recognition:', error);
                    if (statusDiv) statusDiv.textContent = 'Mic start error.';
                }
            }
        });
    }
    
    if (chatForm) {
        chatForm.addEventListener('submit', handleSendMessage);
    }

    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = (userInput.scrollHeight) + 'px';
        });

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
    }
    // Initial state for toggler
    if(toggler) {
      toggler.setAttribute('aria-expanded', 'false');
    }
}

// Main execution
document.addEventListener('DOMContentLoaded', () => {
    buildChatbotUI();
    initializeChatbotFunctionality();
});