import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
        this.setState({ error, errorInfo });
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-black text-white p-10 font-mono flex flex-col items-center justify-center">
                    <div className="max-w-4xl w-full border border-red-500 rounded-lg p-8 bg-red-900/20">
                        <h1 className="text-4xl font-bold text-red-500 mb-4">⚠️ Application Crashed</h1>
                        <p className="text-xl mb-6">Something went wrong while rendering the UI.</p>

                        <div className="bg-black/50 p-6 rounded-lg border border-white/10 overflow-auto mb-6">
                            <h2 className="text-lg font-bold text-gray-400 mb-2">Error Message:</h2>
                            <pre className="text-red-400 whitespace-pre-wrap">{this.state.error && this.state.error.toString()}</pre>
                        </div>

                        <div className="bg-black/50 p-6 rounded-lg border border-white/10 overflow-auto max-h-[400px]">
                            <h2 className="text-lg font-bold text-gray-400 mb-2">Component Stack:</h2>
                            <pre className="text-gray-500 text-sm whitespace-pre-wrap">{this.state.errorInfo && this.state.errorInfo.componentStack}</pre>
                        </div>

                        <button
                            onClick={() => window.location.reload()}
                            className="mt-8 px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold transition-colors"
                        >
                            Reload Application
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
