// Mermaid initialization with theme support for Material MkDocs
document.addEventListener('DOMContentLoaded', function() {
  if (typeof mermaid !== 'undefined') {
    // Initialize Mermaid with base theme
    // CSS will handle dark/light mode styling
    mermaid.initialize({
      startOnLoad: true,
      theme: 'base',
      themeVariables: {
        // Colors that work well in both themes
        primaryColor: '#6366f1',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#4f46e5',
        lineColor: '#94a3b8',
        secondaryColor: '#8b5cf6',
        tertiaryColor: '#10b981',
      },
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
      },
    });
  }
});
