import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async function handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (!file) {
        showError('Por favor seleccione un archivo');
        return;
    }

    if (file.type !== 'application/pdf') {
        showError('Por favor seleccione un archivo PDF válido');
        event.target.value = ''; // Clear the input
        return;
    }

    // Show file info
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    fileName.textContent = file.name;
    fileInfo.style.display = 'block';

    // Process the file
    analyzeContract(file);
}

async function analyzeContract(file) {
    try {
        hideError();
        showLoading('Procesando documento...');

        // Validate file
        if (!file) {
            throw new Error('No se ha seleccionado ningún archivo');
        }

        // Create FormData
        const formData = new FormData();
        formData.append('file', file);

        console.log('Uploading file:', {
            name: file.name,
            type: file.type,
            size: file.size
        });

        // Send request
        const response = await fetch('/contract-review/analyze', {
            method: 'POST',
            body: formData // Don't set Content-Type - browser will set it automatically
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Error al procesar el archivo');
        }

        const data = await response.json();
        hideLoading();
        displayResults(data.data);

    } catch (error) {
        console.error('Error analyzing contract:', error);
        hideLoading();
        showError(error.message);
    }
}

function showError(message) {
    const errorContainer = document.querySelector('.error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger">
                <h5>Error de Análisis</h5>
                <p>${message}</p>
                <div class="mt-3">
                    <button type="button" class="btn btn-outline-primary" onclick="retryUpload()">
                        Intentar Nuevamente
                    </button>
                </div>
            </div>
        `;
        errorContainer.style.display = 'block';
    }
}

function retryUpload() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.value = ''; // Clear previous selection
        fileInput.click();
    }
}

function showLoading(message) {
    const loadingContainer = document.querySelector('.loading-container');
    if (loadingContainer) {
        loadingContainer.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border text-primary me-2" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <span>${message}</span>
            </div>
        `;
        loadingContainer.style.display = 'block';
    }
}

function hideLoading() {
    const loadingContainer = document.querySelector('.loading-container');
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
}
