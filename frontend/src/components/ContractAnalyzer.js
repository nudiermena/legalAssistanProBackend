async function analyzeContract(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);

    // Add analysis options and metadata as separate form fields
    formData.append(
      "analysis_options",
      JSON.stringify({
        risk_analysis: {
          financial: true,
          legal: true,
          compliance: true,
        },
      })
    );

    formData.append(
      "metadata",
      JSON.stringify({
        file_name: file.name,
        file_type: file.type,
      })
    );

    formData.append("jurisdiction", "Colombia");
    formData.append("language", "es");

    const response = await fetch("/api/contract-review/analyze", {
      method: "POST",
      body: formData, // Send as FormData instead of JSON
      // Remove Content-Type header - browser will set it automatically with boundary
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || "Error analyzing contract");
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Error analyzing contract:", error);
    throw error;
  }
}
