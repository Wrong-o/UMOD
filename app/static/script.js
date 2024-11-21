document.getElementById('api-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userInput = document.getElementById('user-input').value;

    const response = await fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: userInput })
    });

    const data = await response.json();
    if (data.response) {
        document.getElementById('response').innerText = data.response;
    } else {
        document.getElementById('response').innerText = "Error: " + data.error;
    }
});
