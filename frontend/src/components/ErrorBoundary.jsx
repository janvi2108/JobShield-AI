import React from 'react';
import { ShieldAlert, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('JobShield AI Runtime Error Caught by Boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#101114] text-[#F2F4F6] flex items-center justify-center p-6">
          <div className="max-w-md w-full p-8 rounded-xl bg-[#191C22] border border-[#2C313C] text-center space-y-4 shadow-2xl">
            <div className="w-12 h-12 rounded-full bg-red-950/40 border border-red-800/60 text-red-400 mx-auto flex items-center justify-center">
              <ShieldAlert className="w-6 h-6 stroke-[2]" />
            </div>
            <h2 className="text-xl font-bold text-[#F2F4F6]">
              Something went wrong
            </h2>
            <p className="text-xs text-[#949BA6] leading-relaxed">
              An unexpected error occurred while rendering this view. Your session and backend data remain intact.
            </p>
            {this.state.error?.message && (
              <div className="p-3 rounded bg-[#101114] border border-[#2C313C] font-mono text-[11px] text-red-300 text-left overflow-x-auto">
                {this.state.error.message}
              </div>
            )}
            <div className="pt-2">
              <button
                type="button"
                onClick={this.handleReset}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-semibold text-xs transition-all shadow-md"
              >
                <RotateCcw className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Return to Home</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
