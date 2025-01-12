            // Function to get product name from URL and format it
            function getProductNameFromUrl() {
                const path = window.location.pathname;
                const productName = path.split('/').pop(); // Get last part of URL
                return productName
                    .replace(/([A-Z])/g, ' $1')
                    .replace(/(\d+)/g, ' $1')
                    .split(/(?=[A-Z0-9])/)
                    .join(' ')
                    .replace(/\s+/g, ' ')
                    .trim()
                    .replace(/\b\w/g, c => c.toUpperCase());
            }

            // Combine both window.onload functions
            document.addEventListener('DOMContentLoaded', function() {
                // Update header text
                const productName = getProductNameFromUrl();
                console.log("Product Name:", productName); // För debugging
                const headerTitle = document.querySelector('.header-text h1');
                if (headerTitle) {
                    headerTitle.textContent = productName;
                } else {
                    console.error("Header title element not found");
                }
            });


window.onload = function() {
    const logFrontendError = async (error) => {
        try {
            const response = await fetch('/frontend-log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: error.message || 'Unknown error',
                    url: window.location.href, // Current page URL
                    type: error.type || 'Error',
                    timestamp: new Date().toISOString(),
                    stack: error.stack || null, // Stack trace if available
                }),
            });

            if (!response.ok) {
                console.error("Failed to log frontend error:", response.statusText);
            } else {
                console.log("Frontend error logged successfully.");
            }
        } catch (err) {
            console.error("Error while sending frontend log:", err);
        }
    };

    // Capture uncaught JavaScript errors
    window.onerror = (message, source, lineno, colno, error) => {
        logFrontendError({
            message: message,
            type: 'UncaughtError',
            stack: error ? error.stack : `At ${source}:${lineno}:${colno}`,
        });
    };

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
        logFrontendError({
            message: event.reason ? event.reason.message : 'Unhandled rejection',
            type: 'PromiseRejection',
            stack: event.reason ? event.reason.stack : null,
        });
    });
 
    // Update header text again to ensure it's set
    const productName = getProductNameFromUrl();
    document.querySelector('.header-text h1').textContent = productName;

    // Your existing welcome message
    typeWelcomeMessage('Welcome! How can I help you today? Detta är en genväg - för officiell information, se användarmanualen.');
};

console.log = (message) => sendLog("info", message);
console.warn = (message) => sendLog("warning", message);
console.error = (message) => sendLog("error", message);

async function sendLog(level, message) {
    try {
        const response = await fetch('/frontend-log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level, message }),
        });

        if (!response.ok) {
            console.error("Failed to send log:", await response.text());
        }
    } catch (error) {
        console.error("Error sending log:", error);
    }
}

// Utility function for delay
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function typeWelcomeMessage(text, responseId) {
    const wrapper = document.createElement('div');
    wrapper.classList.add('message-wrapper');

    // Store the response_id as a data attribute
    wrapper.dataset.responseId = responseId;

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'bot-message');

    const textElement = document.createElement('div');
    textElement.style.whiteSpace = 'pre-line';

    const feedbackContainer = document.createElement('div');
    feedbackContainer.classList.add('feedback-container');
    feedbackContainer.style.display = 'flex';

    const thumbsUp = document.createElement('button');
    thumbsUp.classList.add('feedback-button');
    thumbsUp.innerHTML = '👍';
    thumbsUp.style.fontSize = '16px';
    thumbsUp.onclick = function() {
        handleFeedback(this, true);
    };

    const thumbsDown = document.createElement('button');
    thumbsDown.classList.add('feedback-button');
    thumbsDown.innerHTML = '👎';
    thumbsDown.style.fontSize = '16px';
    thumbsDown.onclick = function() {
        handleFeedback(this, false);
    };

    const cursor = document.createElement('span');
    cursor.classList.add('cursor');
    cursor.textContent = '|';

    messageDiv.appendChild(textElement);
    messageDiv.appendChild(cursor);

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-time');
    timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    messageDiv.appendChild(timeDiv);

    wrapper.appendChild(messageDiv);
    wrapper.appendChild(feedbackContainer);

    const chatContainer = document.getElementById('chatContainer');
    chatContainer.appendChild(wrapper);
    scrollToBottom();

    const typingSpeed = 10;
    let currentText = '';
    for (let i = 0; i < text.length; i++) {
        currentText += text[i];
        textElement.textContent = currentText;
        await sleep(typingSpeed);
        scrollToBottom();
    }

    cursor.style.display = 'none';
}

// Function to decode HTML entities
function decodeHtmlEntities(text) {
    if (!text) return '';
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value.normalize('NFC'); // Normalize to composed form
}

async function typeMessage(response, responseId) {
    const wrapper = document.createElement('div');
    wrapper.classList.add('message-wrapper');

    // Store the response_id as a data attribute
    wrapper.dataset.responseId = responseId;

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'bot-message');

    const contentContainer = document.createElement('div');
    contentContainer.style.whiteSpace = 'pre-line';

    const feedbackContainer = document.createElement('div');
    feedbackContainer.classList.add('feedback-container');
    feedbackContainer.style.display = 'flex';

    const thumbsUp = document.createElement('button');
    thumbsUp.classList.add('feedback-button');
    thumbsUp.innerHTML = '👍';
    thumbsUp.style.fontSize = '16px';
    thumbsUp.onclick = function() {
        handleFeedback(this, true);
    };

    const thumbsDown = document.createElement('button');
    thumbsDown.classList.add('feedback-button');
    thumbsDown.innerHTML = '👎';
    thumbsDown.style.fontSize = '16px';
    thumbsDown.onclick = function() {
        handleFeedback(this, false);
    };

    feedbackContainer.appendChild(thumbsUp);
    feedbackContainer.appendChild(thumbsDown);

    const cursor = document.createElement('span');
    cursor.classList.add('cursor');
    cursor.textContent = '|';

    messageDiv.appendChild(contentContainer);
    messageDiv.appendChild(cursor);

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-time');
    timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    messageDiv.appendChild(timeDiv);

    wrapper.appendChild(messageDiv);
    wrapper.appendChild(feedbackContainer);

    const chatContainer = document.getElementById('chatContainer');
    chatContainer.appendChild(wrapper);
    scrollToBottom();

    const typingSpeed = 10;
    let currentText = '';

    // Use response.response if it exists, otherwise use response.text
    const messageText = response.response || response.text;
    let decodedText = decodeHtmlEntities(messageText || '');

    // Replace problematic characters like ²
    decodedText = decodedText.replace(/²/g, '^2');

    // Type the text response
    for (let i = 0; i < decodedText.length; i++) {
        currentText += decodedText[i];
        contentContainer.textContent = currentText;
        await sleep(typingSpeed);
        scrollToBottom();
    }

    // Handle images if they exist
    if (response.images && Array.isArray(response.images)) {
        response.images.forEach((imageUrl) => {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = 'Image';
            img.style.maxWidth = '100%';
            img.style.marginTop = '10px';
            img.style.borderRadius = '8px';
            img.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.1)';
            contentContainer.appendChild(img);
        });
    }

    cursor.style.display = 'none';
}

function handleFeedback(button, isPositive) {
    const container = button.parentElement;
    const buttons = container.getElementsByClassName('feedback-button');

    // Remove selected class from all buttons
    Array.from(buttons).forEach(btn => {
        btn.classList.remove('selected', 'negative');
    });

    // Add selected class to clicked button
    button.classList.add('selected');
    if (!isPositive) {
        button.classList.add('negative');
    }

    // Get the response_id from the message wrapper
    const messageWrapper = button.closest('.message-wrapper');
    const responseId = messageWrapper.dataset.responseId;

    // Send feedback using POST instead of GET
    fetch('/submit_feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            helpful: isPositive,
            response_id: responseId,
        }),
    })
    .then((response) => {
        if (!response.ok) {
            throw new Error('Failed to save feedback');
        }
        return response.json();
    })
    .then(() => {
        // Fade out and remove the feedback container
        container.style.transition = 'opacity 0.3s ease';
        container.style.opacity = '0';

        setTimeout(() => {
            container.remove();
        }, 300);

        // Show success message
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            font-family: 'Poppins', sans-serif;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        `;
        toast.textContent = 'Thank you for your feedback!';
        document.body.appendChild(toast);

        // Show and hide toast
        setTimeout(() => {
            toast.style.opacity = '1';
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, 2000);
        }, 100);
    })
    .catch((error) => {
        console.error('Error saving feedback:', error);
        button.classList.remove('selected', 'negative');
        alert('Failed to save feedback. Please try again.');
    });
}

// Function to create and display user message
async function createUserMessage(text) {
    try {
        const wrapper = document.createElement('div');
        wrapper.classList.add('message-wrapper', 'user');

        const message = document.createElement('div');
        message.classList.add('message', 'user-message');
        message.textContent = text;

        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        message.appendChild(timeDiv);

        wrapper.appendChild(message);

        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) {
            throw new Error("Chat container not found");
        }

        chatContainer.appendChild(wrapper);

        // Ensure scrollToBottom is defined before calling it
        if (typeof scrollToBottom === 'function') {
            scrollToBottom();
        } else {
            throw new Error("scrollToBottom function is not defined");
        }
    } catch (error) {
        // Log the error to the backend
        await logFrontendError({
            message: error.message,
            type: 'FrontendError',
            stack: error.stack || null,
        });
    }
}

// Function to auto-scroll chat container to the latest message
function scrollToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();

    if (text === '') return;

    console.log("Sending message:", text); // Add this to debug
    createUserMessage(text);
    input.value = '';

    try {
        const response = await fetch('/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });

        console.log("Response received:", response.status, response.statusText);

        const data = await response.json();
        console.log("Response data:", data);

        if (data.error) {
            await typeMessage({ response: 'Error: ' + data.error }, null);
        } else {
            await typeMessage(data, data.response_id);
        }
    } catch (error) {
        console.error("Error during API call:", error);
        await typeMessage({ response: 'Sorry, there was an error processing your message.' }, null);
    }
}

// Function to handle Enter key for sending messages
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}