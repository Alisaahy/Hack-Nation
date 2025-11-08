async function testAPI() {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    resultDiv.className = '';
    resultDiv.textContent = 'Loading...';
    
    try {
        const response = await fetch('/api/hello');
        const data = await response.json();
        resultDiv.className = 'show success';
        resultDiv.textContent = `✅ ${data.message}`;
    } catch (error) {
        resultDiv.className = 'show';
        resultDiv.textContent = `❌ Error: ${error.message}`;
    }
}

